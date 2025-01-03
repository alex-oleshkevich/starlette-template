from starlette.requests import Request
from starlette.responses import Response
from starlette_babel import gettext_lazy as _
from starlette_dispatch import RouteGroup

from app.config.templating import templates

routes = RouteGroup()


@routes.get("/", name="dashboard")
async def dashboard_view(request: Request) -> Response:
    return templates.TemplateResponse(
        request,
        "web/dashboard/index.html",
        {
            "page_title": _("Dashboard"),
            "page_description": _("Welcome to your dashboard!"),
        },
    )
