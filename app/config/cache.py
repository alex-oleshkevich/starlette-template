from urllib.parse import urlparse

from redis.asyncio import Redis

from app.config import settings
from app.contrib.cache import Cache, CacheBackend
from app.contrib.cache.backends.memory import MemoryCacheBackend
from app.contrib.cache.backends.redis import RedisCacheBackend
from app.contrib.cache.serializers import JsonCacheSerializer

__all__ = ["cache"]


def cache_backend_factory(cache_url: str) -> CacheBackend:
    schema = urlparse(cache_url).scheme
    if schema == "memory":
        return MemoryCacheBackend()

    if schema in ("redis", "rediss"):
        return RedisCacheBackend(Redis.from_url(cache_url))

    raise NotImplementedError(f"Unknown cache backend {schema}.")


cache = Cache(
    serializer=JsonCacheSerializer(),
    namespace=settings.cache_namespace,
    backend=cache_backend_factory(settings.cache_url),
)
