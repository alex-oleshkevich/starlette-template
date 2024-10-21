import typing

from mailers import Mailer
from redis import Redis as RedisType
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.cache import cache
from app.config.files import file_storage
from app.config.mailers import mailer
from app.config.redis import redis
from app.config.settings import Config, settings
from app.contrib.cache import Cache as Cache_
from app.contrib.storage import FileStorage

Files = typing.Annotated[FileStorage, file_storage]
Mail = typing.Annotated[Mailer, mailer]
Cache = typing.Annotated[Cache_, cache]
Redis = typing.Annotated[RedisType, redis]
DbSession = typing.Annotated[AsyncSession, lambda r: r.state.dbsession]
Settings = typing.Annotated[Config, settings]
