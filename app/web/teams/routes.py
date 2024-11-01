from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from starlette_babel import gettext_lazy as _
from starlette_dispatch import RouteGroup
from starlette_flash import flash

from app.config.templating import templates
from app.contrib.urls import safe_referer

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
