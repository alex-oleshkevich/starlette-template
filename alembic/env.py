import asyncio
import glob
import importlib
import os
import typing
from logging.config import fileConfig

from alembic import context
from alembic.autogenerate.api import AutogenContext
from alembic.operations import MigrationScript
from alembic.runtime.migration import MigrationContext
from sqlalchemy import engine_from_config, pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncEngine

from app.config import settings
from app.config.sqla.migrations import RendersMigrationType
from app.config.sqla.models import Base

model_paths = [
    *glob.glob(f"{settings.package_name}/models/*.py"),
    *glob.glob(f"{settings.package_name}/*/models.py"),
    *glob.glob(f"{settings.package_name}/contexts/**/models.py"),
]


def discover_models() -> None:
    """Discover models for automatic migration generation."""
    for file_name in model_paths:
        if "__init__" in file_name:
            continue
        pymodule = file_name.replace(os.path.sep, ".").replace(".py", "")
        importlib.import_module(pymodule)


def delete_empty_migration_scripts(
    context: MigrationContext,
    revision: str | typing.Iterable[str | None] | typing.Iterable[str],
    directives: list[MigrationScript],
) -> None:
    assert config.cmd_opts is not None
    if getattr(config.cmd_opts, "autogenerate", False):
        script = directives[0]
        assert script.upgrade_ops is not None
        if script.upgrade_ops.is_empty():
            directives[:] = []


def process_revision_directives(
    context: MigrationContext,
    revision: str | typing.Iterable[str | None] | typing.Iterable[str],
    directives: list[MigrationScript],
) -> None:
    delete_empty_migration_scripts(context, revision, directives)


discover_models()

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata


# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def render_item(type_: str, obj: typing.Any, autogen_context: AutogenContext) -> str | typing.Literal[False]:
    """Apply custom rendering for items that comply RendersMigrationType interface."""
    if type_ == "type" and isinstance(obj, RendersMigrationType):
        return obj.render_item(type_, obj, autogen_context)

    return False


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    This configures the context with just a URL and not an Engine, though an Engine is acceptable here as well.  By
    skipping the Engine creation we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
        render_item=render_item,
        process_revision_directives=process_revision_directives,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
        render_item=render_item,
        include_object=None,
        process_revision_directives=process_revision_directives,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.

    In this scenario we need to create an Engine and associate a connection with the context.
    """
    connectable = AsyncEngine(
        engine_from_config(
            config.get_section(config.config_ini_section),  # type: ignore[arg-type]
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
            future=True,
        ),
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
