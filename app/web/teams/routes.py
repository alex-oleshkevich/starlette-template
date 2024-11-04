from sqlalchemy.exc import IntegrityError
from starlette import status
from starlette.background import BackgroundTask, BackgroundTasks
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from starlette_babel import gettext_lazy as _
from starlette_dispatch import FromPath, RouteGroup
from starlette_flash import flash

from app.config.dependencies import CurrentMembership, CurrentTeam, CurrentUser, DbSession, Files
from app.config.templating import templates
from app.contexts.teams.mails import send_team_invitation_email, send_team_member_joined_email
from app.contexts.teams.models import InvitationToken, TeamInvite
from app.contexts.teams.repo import TeamRepo
from app.contrib import forms, htmx
from app.contrib.forms import create_form
from app.contrib.urls import redirect_later, safe_referer
from app.web.teams.forms import GeneralSettingsForm, InviteForm

routes = RouteGroup()
team_invitation_public_routes = RouteGroup()


@routes.get_or_post("/teams/select", name="teams.select")
async def select_team_view(request: Request) -> Response:
    if request.method == "POST":
        formdata = await request.form()
        team_id = formdata.get("team_id")
        try:
            membership = next((m for m in request.state.team_memberships if str(m.team_id) == team_id), None)
            if membership is None:
                raise ValueError

            redirect_to = safe_referer(request, request.query_params.get("next", "/"))
            response = RedirectResponse(redirect_to, status_code=302)
            response.set_cookie("team_id", str(membership.team_id), max_age=60 * 60 * 24 * 365)
        except ValueError:
            flash(request).error(_("Invalid team."))
        else:
            return response

    return templates.TemplateResponse(request, "web/teams/select.html", {"page_title": _("Select Team")})


@routes.get_or_post("/teams/settings", name="teams.settings")
async def settings_view(request: Request, dbsession: DbSession, team: CurrentTeam, files: Files) -> Response:
    form = await create_form(request, GeneralSettingsForm, obj=team)
    if await forms.validate_on_submit(request, form):
        if form.logo.clear:
            if team.logo:
                await files.delete(team.logo)
            form.logo.data = None

        if form.logo.is_uploaded:
            form.logo.data = await files.upload(
                form.logo.data, "teams/{team_id}/logo.{extension}", extra_tokens=dict(team_id=team.id)
            )

        form.populate_obj(team)

        await dbsession.commit()
        return htmx.response().success_toast(_("Team has been updated."))

    return templates.TemplateResponse(
        request, "web/teams/settings_general.html", {"page_title": _("Team Settings"), "form": form}
    )


@routes.get_or_post("/teams/members", name="teams.members")
async def members_view(request: Request, dbsession: DbSession, team: CurrentTeam) -> Response:
    repo = TeamRepo(dbsession)
    members = await repo.get_team_members(team.id)
    invites = await repo.get_invites(team.id)

    template_name = "web/teams/members.html"
    if htmx.is_htmx_request(request):
        if htmx.matches_target(request, "members"):
            template_name = "web/teams/members_view.html"
        if htmx.matches_target(request, "invitations"):
            template_name = "web/teams/invites_view.html"

    return templates.TemplateResponse(
        request, template_name, {"page_title": _("Members"), "members": members, "invites": invites}
    )


@routes.get_or_post("/teams/members/invite", name="teams.members.invite")
async def invite_view(request: Request, dbsession: DbSession, team_member: CurrentMembership) -> Response:
    repo = TeamRepo(dbsession)
    roles = await repo.get_roles(team_member.team.id)
    form = await create_form(request, InviteForm)
    form.setup(roles)
    status_code = status.HTTP_200_OK
    if await forms.validate_on_submit(request, form):
        emails = [email.strip() for email in form.email.data.split(",") if email.strip()]  # type: ignore[union-attr]
        role = await repo.get_role(team_member.team.id, form.role.data)
        if not role:
            return htmx.response().error_toast(_("Invalid role.")).close_modal()

        tasks: list[BackgroundTask] = []

        for email in emails:
            token = InvitationToken()
            link = token.make_url(request)
            invite = TeamInvite(
                email=email,
                role=role,
                inviter=team_member,
                team=team_member.team,
                token=token.hashed_token,
            )
            dbsession.add(invite)
            tasks.append(BackgroundTask(send_team_invitation_email, invite, link))

        try:
            await dbsession.commit()
        except IntegrityError:
            status_code = status.HTTP_400_BAD_REQUEST
            form.email.errors = [*form.email.errors, _("One or more of the emails you entered is already invited.")]
        else:
            return (
                htmx.response(
                    background=BackgroundTasks(tasks),
                )
                .success_toast(_("Invites have been sent."))
                .close_modal()
                .trigger("refresh-invitations")
            )

    return templates.TemplateResponse(request, "web/teams/invite_form.html", {"form": form}, status_code=status_code)


@routes.post("/teams/members/toggle-status/{member_id:int}", name="teams.members.toggle_status")
async def toggle_status_view(dbsession: DbSession, team: CurrentTeam, member_id: FromPath[int]) -> Response:
    repo = TeamRepo(dbsession)
    member = await repo.get_team_member_by_id(team.id, member_id)
    if not member:
        return htmx.response(status.HTTP_404_NOT_FOUND).error_toast(_("Member not found.")).trigger("refresh-members")

    if member.is_suspended:
        member.unsuspend()
        message = _("Member has been activated.")
    else:
        member.suspend()
        message = _("Member has been deactivated.")

    await dbsession.commit()
    return htmx.response().success_toast(message).trigger("refresh-members")


@routes.post("/teams/invites/cancel/{invite_id:int}", name="teams.invites.cancel")
async def cancel_invitation_view(dbsession: DbSession, team: CurrentTeam, invite_id: FromPath[int]) -> Response:
    repo = TeamRepo(dbsession)
    invitation = await repo.get_invitation(team.id, invite_id)
    if not invitation:
        return (
            htmx.response(status.HTTP_404_NOT_FOUND)
            .error_toast(_("Invitation not found."))
            .trigger("refresh-invitations")
        )

    await dbsession.delete(invitation)
    await dbsession.commit()
    return htmx.response().success_toast(_("Member has been deactivated.")).trigger("refresh-invitations")


@routes.get_or_post("/teams/roles", name="teams.roles")
async def roles_view(request: Request, dbsession: DbSession, team: CurrentTeam) -> Response:
    repo = TeamRepo(dbsession)
    members = await repo.get_team_members(team.id)
    return templates.TemplateResponse(request, "web/teams/members.html", {"page_title": _("Roles"), "members": members})


@team_invitation_public_routes.get("/teams/members/accept-invite/{token}", name="teams.members.accept_invite")
async def accept_invite_view(
    request: Request,
    dbsession: DbSession,
    user: CurrentUser,
    token: FromPath[str],
) -> Response:
    if not user.is_authenticated:
        redirect_later(request, request.url)
        return RedirectResponse(request.url_for("register"), status_code=status.HTTP_302_FOUND)

    repo = TeamRepo(dbsession)
    invitation = await repo.get_invitation_by_token(token)
    if not invitation:
        return templates.TemplateResponse(
            request,
            "web/service/message.html",
            {
                "page_title": _("Invalid or expired invitation"),
                "message": _("The invitation you are trying to accept is invalid or has expired."),
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    team_member = await repo.accept_invitation(user, invitation)
    await dbsession.commit()

    flash(request).success(_("Welcome to the {team}!").format(team=team_member.team))
    redirect_url = safe_referer(request, request.query_params.get("next", request.url_for("dashboard")))
    redirect_url = redirect_url.include_query_params(team_id=team_member.team_id)
    return RedirectResponse(
        redirect_url,
        background=BackgroundTask(send_team_member_joined_email, invitation, team_member),
        status_code=status.HTTP_302_FOUND,
    )
