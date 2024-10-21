from urllib.request import Request

from starlette.responses import Response
from starlette_dispatch import RouteGroup

from app.config.templating import templates

routes = RouteGroup()


@routes.get("/", name="dashboard")
async def dashboard_view(request: Request) -> Response:
    return templates.TemplateResponse("web/dashboard/index.html", {"request": request})
