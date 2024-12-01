from app.config import settings
from app.config.logging import configure_logging
from app.config.sentry import configure_sentry

configure_logging()
configure_sentry(
    sentry_dsn=settings.sentry_dsn,
    app_env=settings.app_env,
    app_version=settings.release_version,
)
