import importlib
import os
import pathlib
import sys

from pydantic_settings import BaseSettings, SettingsConfigDict
from slugify import slugify

from app.config.environment import Environment
from app.contrib.storage import StorageType

PACKAGE_NAME = __name__.split(".")[0]
PACKAGE_DIR = pathlib.Path(importlib.import_module(PACKAGE_NAME).__path__[0])
REPO_DIR = PACKAGE_DIR.parent

RESOURCES_DIR = REPO_DIR / "resources"

IS_TEST = "pytest" in sys.argv[0] or os.environ.get("APP_ENV", default="") == "test"


class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="",
        env_file=REPO_DIR / ".env",
        secrets_dir=os.environ.get("SECRETS_DIR", "var/"),
    )

    # global settings
    package_name: str = PACKAGE_NAME
    package_dir: pathlib.Path = PACKAGE_DIR
    repo_dir: pathlib.Path = REPO_DIR
    resources_dir: pathlib.Path = RESOURCES_DIR
    is_test: bool = IS_TEST
    debug: bool = False
    secret_key: str = ""

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
    database_url: str = "postgresql+psycopg_async://postgres@localhost:5432/app"
    sqlalchemy_echo: bool = False

    # redis
    redis_url: str = "redis://"

    # cache options
    cache_namespace: str = f"{app_slug}:{app_env}:"
    cache_url: str = "redis://?socket_timeout=1"

    # email options
    mail_url: str = "smtp://localhost:1025"
    mail_default_from_address: str = "rvapp@localhost"
    mail_default_from_name: str = "RVApp Team"

    # file storage options
    storages_type: StorageType = StorageType.LOCAL
    storages_s3_bucket: str = ""
    storages_s3_access_key: str = ""
    storages_s3_secret_key: str = ""
    storages_s3_region: str = ""
    storages_s3_endpoint: str = ""
    storages_local_dir: pathlib.Path = repo_dir / "var" / "uploads"
    storages_local_url_prefix: str = "/media"

    # sentry options
    sentry_dsn: str = ""

    # encryption options
    # must be url-safe base64-encoded 32-byte key for Fernet
    encryption_key: str = ""


class TestConfig(Config):
    encryption_key: str = "w2P1uYmFG0PFmm0WcH4Eh/zEwXCoCgprtmiPl5zdDuU="
    database_url: str = "postgresql+psycopg_async://postgres@localhost:5432/app_test"
    mail_url: str = "memory://"
    file_storage_type: StorageType = StorageType.MEMORY


settings = TestConfig() if IS_TEST else Config()
