from starlette.requests import Request
from starlette.responses import JSONResponse

from app.config import settings


async def version_view(_: Request) -> JSONResponse:
    return JSONResponse(
        dict(
            app_env=settings.app_env,
            commit=settings.release_commit,
            date=settings.release_date,
            branch=settings.release_branch,
            version=settings.release_version,
        )
    )
