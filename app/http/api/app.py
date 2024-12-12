from fastapi import FastAPI
from fastapi.exceptions import HTTPException, RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware import Middleware
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette_babel import LocaleMiddleware, TimezoneMiddleware

from app.config import settings
from app.config.permissions.context import AccessContextMiddleware
from app.contexts.auth.authentication import db_user_loader, JWTBackend
from app.contexts.billing.middleware import SubscriptionMiddleware
from app.contexts.teams.middleware import TeamMiddleware
from app.exceptions import RateLimitedError
from app.http.api.auth.routes import router as auth_router
from app.http.api.error_handlers import api_exception_handler, api_fastapi_validation_handler, api_rate_limited_handler
from app.http.api.profile.routes import router as profile_router
from app.http.api.schemas import Paginated
from app.http.responses import ErrorSchema

api_app = FastAPI(
    debug=settings.debug,
    docs_url="/docs",
    version="0.1.0",
    title=settings.app_name,
    summary="API for the application",
    description="API for the application",
    swagger_ui_init_oauth={},
    servers=[
        {"url": f"{settings.app_url}/api", "description": "API server"},
    ],
    responses={
        200: {"model": Paginated},
        400: {"model": ErrorSchema},
    },
    exception_handlers={
        RateLimitedError: api_rate_limited_handler,
        RequestValidationError: api_fastapi_validation_handler,
        HTTPException: api_exception_handler,
        StarletteHTTPException: api_exception_handler,
    },
    middleware=[
        Middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
            expose_headers=["*"],
            allow_credentials=True,
        ),
        Middleware(AuthenticationMiddleware, backend=JWTBackend(db_user_loader)),
        Middleware(TimezoneMiddleware, fallback=settings.timezone),
        Middleware(LocaleMiddleware, locales=settings.i18n_locale_codes, default_locale=settings.i18n_default_locale),
        Middleware(TeamMiddleware, cookie_name=settings.team_cookie, query_param="team_id"),
        Middleware(SubscriptionMiddleware),
        Middleware(AccessContextMiddleware),
    ],
)
api_app.include_router(auth_router)
api_app.include_router(profile_router)
