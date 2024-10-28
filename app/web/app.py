from starlette.middleware import Middleware
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.responses import RedirectResponse
from starlette.routing import Mount, Route, Router
from starlette_auth import LoginRequiredMiddleware, SessionBackend
from starlette_dispatch import RouteGroup
from starsessions import CookieStore, SessionAutoloadMiddleware, SessionMiddleware

from app.config import settings
from app.config.environment import Environment
from app.contexts.auth.authentication import db_user_loader
from app.web.auth.routes import routes as login_routes
from app.web.dashboard.routes import routes as dashboard_routes
from app.web.internal.routes import routes as internal_routes
from app.web.profile.routes import routes as profile_routes
from app.web.register.routes import routes as register_routes

web_router = Router(
    middleware=[
        Middleware(
            SessionMiddleware,
            rolling=True,
            lifetime=settings.session_lifetime,
            store=CookieStore(settings.secret_key),
            cookie_https_only=settings.app_env != Environment.UNITTEST,
        ),
        Middleware(SessionAutoloadMiddleware),
        Middleware(
            AuthenticationMiddleware,
            backend=SessionBackend(db_user_loader, secret_key=settings.secret_key),
        ),
    ],
    routes=RouteGroup(
        children=[
            internal_routes,
            login_routes,
            register_routes,
            Route("/", RedirectResponse("/app", status_code=302), name="home"),
            Mount(
                path="/app",
                middleware=[
                    Middleware(LoginRequiredMiddleware, path_name="login"),
                ],
                routes=RouteGroup(
                    children=[
                        dashboard_routes,
                        profile_routes,
                    ]
                ),
            ),
        ]
    ),
)
