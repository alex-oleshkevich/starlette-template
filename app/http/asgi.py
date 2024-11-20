from async_storages.contrib.starlette import FileServer
from starception import install_error_handler
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.routing import Mount
from starlette.staticfiles import StaticFiles
from starlette_sqlalchemy import DbSessionMiddleware

from app.config import settings
from app.config.database import new_dbsession
from app.config.files import file_storage
from app.config.sentry import configure_sentry
from app.exceptions import AppError
from app.http.api.app import api_app
from app.http.error_handlers import on_app_error
from app.http.web.app import web_router

install_error_handler()
configure_sentry(
    sentry_dsn=settings.sentry_dsn,
    app_env=settings.app_env,
    app_version=settings.release_version,
)

# List of middleware that will be applied to every route in the app.
global_middleware = [
    Middleware(DbSessionMiddleware, session_factory=new_dbsession),
]

app = Starlette(
    debug=settings.debug,
    routes=[
        Mount("/api", api_app),
        Mount("/media", FileServer(file_storage), name="media"),
        Mount("/static", app=StaticFiles(packages=["app.resources"]), name="static"),
        Mount("", web_router),
    ],
    middleware=global_middleware,
    exception_handlers={
        AppError: on_app_error,  # type: ignore[dict-item]
    },
)
