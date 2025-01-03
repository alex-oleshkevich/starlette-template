from starlette import status
from starlette.background import BackgroundTask
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from starlette_auth import logout
from starlette_auth.authentication import update_session_auth_hash
from starlette_babel import gettext_lazy as _
from starlette_dispatch import RouteGroup
from starlette_flash import flash

from app import settings
from app.config.crypto import averify_password, make_password
from app.config.templating import templates
from app.contexts.auth.mails import send_account_deleted_mail, send_password_changed_mail
from app.contexts.users.repo import UserRepo
from app.contrib import forms, htmx
from app.http.dependencies import CurrentMembership, CurrentUser, DbSession
from app.http.exceptions import PermissionDeniedError
from app.http.web.profile.forms import PasswordForm, ProfileForm

routes = RouteGroup()


@routes.get("/profile", name="profile")
async def profile_view(request: Request, user: CurrentUser) -> Response:
    profile_form = await forms.create_form(request, ProfileForm, obj=user)
    password_form = await forms.create_form(request, PasswordForm)

    return templates.TemplateResponse(
        request,
        "web/profile/index.html",
        {
            "page_title": _("My Profile"),
            "profile_form": profile_form,
            "password_form": password_form,
        },
    )


@routes.post("/profile/edit", name="profile.edit")
async def edit_profile_view(request: Request, dbsession: DbSession, user: CurrentUser) -> Response:
    form = await forms.create_form(request, ProfileForm, obj=user)
    if await forms.validate_on_submit(request, form):
        form.populate_obj(user)
        await dbsession.commit()
        return htmx.response(
            status.HTTP_204_NO_CONTENT,
            background=BackgroundTask(send_password_changed_mail, user),
        ).toast(_("Profile updated successfully."))

    return templates.TemplateResponse(
        request, "web/profile/profile_form.html", {"page_title": _("Edit Profile"), "form": form}
    )


@routes.post("/profile/password", name="profile.password")
async def password_view(request: Request, dbsession: DbSession, user: CurrentUser) -> Response:
    form = await forms.create_form(request, PasswordForm)
    if await forms.validate_on_submit(request, form):
        assert form.current_password.data
        if await averify_password(user.password, form.current_password.data):
            assert form.password.data
            user.password = make_password(form.password.data)
            await dbsession.commit()
            update_session_auth_hash(request, user, settings.secret_key)
            return htmx.response(status.HTTP_204_NO_CONTENT).toast(_("Password has been changed."))

        form.current_password.errors = [_("Current password is incorrect."), *form.current_password.errors]

    return templates.TemplateResponse(
        request, "web/profile/password_form.html", {"page_title": _("Edit Profile"), "form": form}
    )


@routes.delete("/profile", name="profile.delete")
async def delete_profile_view(request: Request, dbsession: DbSession, user: CurrentUser) -> Response:
    repo = UserRepo(dbsession)
    await repo.delete(user)
    await dbsession.commit()
    await logout(request)
    flash(request).success(_("Account has been deleted."))
    response = RedirectResponse(
        request.url_for("login"),
        status_code=status.HTTP_302_FOUND,
        background=BackgroundTask(send_account_deleted_mail, user),
    )
    return htmx.redirect(response, request.url_for("login"))


@routes.post("/profile/leave", name="profile.leave_team")
async def leave_team_view(request: Request, dbsession: DbSession, team_member: CurrentMembership) -> Response:
    if team_member.team.owner == team_member.user:
        raise PermissionDeniedError(_("You cannot leave your own team."))

    team_member.suspend()
    await dbsession.commit()
    flash(request).success(_("You have left the team."))
    return htmx.response(status.HTTP_302_FOUND, headers={"location": str(request.url_for("dashboard"))}).redirect(
        request.url_for("dashboard")
    )
