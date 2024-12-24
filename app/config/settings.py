import datetime
import importlib
import os
import pathlib
import sys
import typing

from pydantic_settings import BaseSettings, SettingsConfigDict
from slugify import slugify

from app.config.environment import Environment
from app.contrib.storage import StorageType

PACKAGE_NAME = __name__.split(".")[0]
PACKAGE_DIR = pathlib.Path(importlib.import_module(PACKAGE_NAME).__path__[0])
REPO_DIR = PACKAGE_DIR.parent

# directory with docker secrets
SECRETS_DIR = os.environ.get("SECRETS_DIR")

RESOURCES_DIR = PACKAGE_DIR / "resources"

IS_TEST = "pytest" in sys.argv[0] or os.environ.get("APP_ENV", default="") == Environment.UNITTEST


class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="",
        env_file=REPO_DIR / ".env",
        secrets_dir=os.environ.get("SECRETS_DIR"),
    )

    # global settings
    package_name: str = PACKAGE_NAME
    package_dir: pathlib.Path = PACKAGE_DIR
    repo_dir: pathlib.Path = REPO_DIR
    resources_dir: pathlib.Path = RESOURCES_DIR
    is_test: bool = IS_TEST
    debug: bool = False
    secret_key: str = ""
    log_level: str = "INFO"

    # application options
    app_name: str = "Project Template"
    app_env: Environment = Environment.LOCAL
    app_slug: str = slugify(app_name)
    app_url: str = "http://localhost:7000"
    app_language: str = "en"

    # release options
    release_commit: str = ""
    release_branch: str = ""
    release_date: str = ""
    release_version: str = ""

    # database options
    database_url: str = "postgresql+psycopg_async://postgres@127.0.0.1:5432/project_template"
    sqlalchemy_echo: bool = False

    # redis
    redis_url: str = "redis://"

    # auth
    access_token_ttl: datetime.timedelta = datetime.timedelta(minutes=15)
    refresh_token_ttl: datetime.timedelta = datetime.timedelta(days=30)

    # cache options
    cache_namespace: str = f"{app_slug}:{app_env}:"
    cache_url: str = "redis://?socket_timeout=1"

    # email options
    mail_url: str = "smtp://localhost:1025"
    mail_default_from_address: str = "project@localhost"
    mail_default_from_name: str = "Project Team"

    # file storage options
    storages_type: StorageType = StorageType.LOCAL
    storages_s3_bucket: str = ""
    storages_s3_access_key: str = ""
    storages_s3_secret_key: str = ""
    storages_s3_region: str = ""
    storages_s3_endpoint: str = ""
    storages_local_dir: pathlib.Path = repo_dir / "var" / "uploads"
    storages_local_url_prefix: str = "/media"

    # i18n settings
    i18n_locales: typing.Sequence[tuple[str, str]] = (("en", "English"),)
    i18n_default_locale: str = "en"
    i18n_locale_codes: list[str] = [code for code, _ in i18n_locales]

    # timezone settings
    timezone: str = "UTC"

    # sentry options
    sentry_dsn: str = ""

    # encryption options
    # must be url-safe base64-encoded 32-byte key for Fernet
    encryption_key: str = ""

    # session settings
    session_cookie: str = "session"
    session_rolling: bool = True
    session_lifetime: datetime.timedelta = datetime.timedelta(days=14)

    # registration
    register_auto_login: bool = True
    register_require_email_confirmation: bool = True

    # google login
    google_client_id: str = ""
    google_client_secret: str = ""

    # teams
    team_cookie: str = "team_id"

    # stripe settings
    stripe_pricing_table_id: str = ""
    stripe_secret_key: str = ""
    stripe_public_key: str = ""
    stripe_webhook_secret: str = ""

    task_queue_concurrency: int = 10


class TestConfig(Config):
    """Configuration for unit tests.
    Values can be overridden from the environment variables. Such environment variables must be prefixed with TEST_."""

    model_config = SettingsConfigDict(env_file=None, secrets_dir=None, env_prefix="TEST_")
    debug: bool = True
    app_env: Environment = Environment.UNITTEST
    encryption_key: str = "w2P1uYmFG0PFmm0WcH4Eh/zEwXCoCgprtmiPl5zdDuU="
    database_url: str = "postgresql+psycopg_async://postgres@localhost:5432/project_template_test"
    mail_url: str = "memory://"
    cache_url: str = "memory://"
    storages_type: StorageType = StorageType.MEMORY


settings = TestConfig() if IS_TEST else Config()
