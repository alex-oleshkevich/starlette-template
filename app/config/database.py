import contextlib
import typing

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

async_dbengine = create_async_engine(
    settings.database_url,
    echo_pool=True,
    pool_size=20,
    pool_timeout=10,
    max_overflow=50,
)
async_dbsession = async_sessionmaker(async_dbengine, expire_on_commit=False)


@contextlib.asynccontextmanager
async def new_dbsession() -> typing.AsyncGenerator[AsyncSession, None]:
    async with async_dbsession() as dbsession:
        yield dbsession
