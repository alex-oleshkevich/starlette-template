import sentry_sdk
from sentry_sdk.integrations.asyncio import AsyncioIntegration
from sentry_sdk.integrations.redis import RedisIntegration


def configure_sentry(sentry_dsn: str, app_env: str, app_version: str) -> None:
    sentry_sdk.init(
        dsn=sentry_dsn,
        enable_tracing=True,
        traces_sample_rate=0.1,
        sample_rate=0.1,
        profiles_sample_rate=0.1,
        environment=app_env,
        release=app_version,
        integrations=[
            AsyncioIntegration(),
            RedisIntegration(),
        ],
    )
