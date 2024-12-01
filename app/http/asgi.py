import contextlib
import typing

import anyio
from async_storages.contrib.starlette import FileServer
from starception import install_error_handler
from starlette.applications import Starlette
from starlette.exceptions import HTTPException
from starlette.middleware import Middleware
from starlette.routing import Mount
from starlette.staticfiles import StaticFiles
from starlette_sqlalchemy import DbSessionMiddleware

from app.config import settings
from app.config.database import new_dbsession
from app.config.files import file_storage
from app.config.queues import task_queue
from app.contrib.permissions import AccessDeniedError
from app.http.api.app import api_app
from app.http.error_handlers import exception_handler, remap_exception
from app.http.exceptions import PermissionDeniedError
from app.http.web.app import web_router

install_error_handler()

# List of middleware that will be applied to every route in the app.
global_middleware = [
    Middleware(DbSessionMiddleware, session_factory=new_dbsession),
]


@contextlib.asynccontextmanager
async def lifespan_handler(app: Starlette) -> typing.AsyncGenerator[dict[str, typing.Any], None]:
    """Application lifespan handler.
    Any value yielded by this function will be available as `request.app.VARNAME`."""
    async with anyio.create_task_group() as tg:
        yield {}
        tg.cancel_scope.cancel()
        await task_queue.disconnect()


app = Starlette(
    debug=settings.debug,
    lifespan=lifespan_handler,
    routes=[
        Mount("/api", api_app),
        Mount("/media", FileServer(file_storage), name="media"),
        Mount("/static", app=StaticFiles(packages=["app.resources"]), name="static"),
        Mount("", web_router),
    ],
    middleware=global_middleware,
    exception_handlers={
        HTTPException: exception_handler,
        AccessDeniedError: remap_exception(PermissionDeniedError),
    },
)
