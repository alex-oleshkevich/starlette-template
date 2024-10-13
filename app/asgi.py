from async_storages.contrib.starlette import FileServer
from starception import install_error_handler
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.routing import Mount
from starlette.staticfiles import StaticFiles
from starlette_sqlalchemy import DbSessionMiddleware

from app.api.app import api_app
from app.config import settings
from app.config.database import new_dbsession
from app.config.files import file_storage
from app.config.sentry import configure_sentry
from app.web.app import web_router

install_error_handler()
configure_sentry(
    sentry_dsn=settings.sentry_dsn,
    app_env=settings.app_env,
    app_version=settings.release_version,
)

# List of middleware that will be applied to every route in the app.
global_middleware = [
    Middleware(DbSessionMiddleware, session_factory=new_dbsession),
    Middleware(
        CORSMiddleware,
        allow_methods=["*"],
        allow_headers=["*"],
        allow_origins=["*"] if settings.debug else ["http://localhost", "http://localhost:7000"],
    ),
]

app = Starlette(
    debug=settings.debug,
    routes=[
        Mount("/api", api_app),
        Mount("/static", app=StaticFiles(packages=["app.resources"]), name="static"),
        Mount("/media", FileServer(file_storage), name="media"),
        Mount("", web_router),
    ],
    middleware=global_middleware,
)
