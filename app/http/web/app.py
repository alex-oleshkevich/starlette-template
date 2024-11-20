from starlette.middleware import Middleware
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.responses import RedirectResponse
from starlette.routing import Mount, Route, Router
from starlette_auth import LoginRequiredMiddleware, SessionBackend
from starlette_babel import LocaleMiddleware, TimezoneMiddleware
from starlette_dispatch import RouteGroup
from starsessions import InMemoryStore, SessionAutoloadMiddleware, SessionMiddleware
from starsessions.stores.redis import RedisStore

from app.config import redis, settings
from app.config.environment import Environment
from app.contexts.auth.authentication import db_user_loader
from app.contexts.billing.middleware import SubscriptionMiddleware
from app.contexts.teams.middleware import RequireTeamMiddleware, TeamMiddleware
from app.http.web.auth.routes import routes as login_routes
from app.http.web.billing.routes import routes as billing_routes
from app.http.web.billing.routes_stripe import routes as stripe_routes
from app.http.web.billing.routes_stripe_public import routes as public_stripe_routes
from app.http.web.dashboard.routes import routes as dashboard_routes
from app.http.web.internal.routes import routes as internal_routes
from app.http.web.profile.routes import routes as profile_routes
from app.http.web.register.routes import routes as register_routes
from app.http.web.teams.routes import routes as teams_routes
from app.http.web.teams.routes import team_invitation_public_routes

session_backend = InMemoryStore() if settings.is_test else RedisStore(connection=redis.redis)

web_router = Router(
    middleware=[
        Middleware(
            SessionMiddleware,
            rolling=True,
            lifetime=settings.session_lifetime,
            store=session_backend,
            cookie_name=settings.session_cookie,
            cookie_path="/",
            cookie_https_only=settings.app_env == Environment.PRODUCTION,
        ),
        Middleware(SessionAutoloadMiddleware),
        Middleware(
            AuthenticationMiddleware,
            backend=SessionBackend(db_user_loader, secret_key=settings.secret_key),
        ),
        Middleware(TimezoneMiddleware, fallback=settings.timezone),
        Middleware(LocaleMiddleware, locales=settings.i18n_locale_codes, default_locale=settings.i18n_default_locale),
    ],
    routes=RouteGroup(
        children=[
            internal_routes,
            login_routes,
            register_routes,
            public_stripe_routes,
            team_invitation_public_routes,
            Route("/", RedirectResponse("/app", status_code=302), name="home"),
            Mount(
                path="/app",
                middleware=[
                    Middleware(LoginRequiredMiddleware, path_name="login"),
                    Middleware(TeamMiddleware, cookie_name=settings.team_cookie, query_param="team_id"),
                    Middleware(RequireTeamMiddleware, redirect_path_name="teams.select"),
                    Middleware(SubscriptionMiddleware),
                ],
                routes=RouteGroup(
                    children=[
                        dashboard_routes,
                        profile_routes,
                        billing_routes,
                        stripe_routes,
                        teams_routes,
                    ]
                ),
            ),
        ]
    ),
)
