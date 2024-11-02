from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from starlette_babel import gettext_lazy as _
from starlette_dispatch import RouteGroup
from starlette_flash import flash

from app.config.dependencies import CurrentTeam, DbSession, Files
from app.config.templating import templates
from app.contrib import forms, htmx
from app.contrib.forms import create_form
from app.contrib.urls import safe_referer
from app.web.teams.forms import GeneralSettingsForm

routes = RouteGroup()


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
        if form.photo.clear:
            if team.photo:
                await files.delete(team.photo)
            form.photo.data = None

        if form.photo.is_uploaded:
            form.photo.data = await files.upload(
                form.photo.data, "teams/{team_id}/logo.{extension}", extra_tokens=dict(team_id=team.id)
            )

        form.populate_obj(team)

        await dbsession.commit()
        return htmx.response().success_toast(_("Team has been updated."))

    return templates.TemplateResponse(
        request, "web/teams/settings_general.html", {"page_title": _("Team Settings"), "form": form}
    )
