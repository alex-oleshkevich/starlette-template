from fastapi import FastAPI
from starlette.middleware import Middleware

from app.config import settings
from app.config.permissions.context import AccessContextMiddleware

api_app = FastAPI(
    debug=settings.debug,
    middleware=[
        Middleware(AccessContextMiddleware),
    ],
)
