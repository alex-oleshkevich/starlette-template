import logging

from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette_dispatch import RouteGroup

from app.http.dependencies import Settings

routes = RouteGroup()
logger = logging.getLogger(__name__)


@routes.get("/version")
async def version_view(request: Request, settings: Settings) -> Response:
    logger.info("Version view")
    return JSONResponse(
        dict(
            app_env=settings.app_env,
            commit=settings.release_commit,
            date=settings.release_date,
            branch=settings.release_branch,
            version=settings.release_version,
        )
    )
