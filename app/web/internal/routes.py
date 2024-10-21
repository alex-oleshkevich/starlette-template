from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette_dispatch import RouteGroup

from app.config.dependencies import Settings

routes = RouteGroup()


@routes.get("/version")
async def version_view(request: Request, settings: Settings) -> Response:
    return JSONResponse(
        dict(
            app_env=settings.app_env,
            commit=settings.release_commit,
            date=settings.release_date,
            branch=settings.release_branch,
            version=settings.release_version,
        )
    )
