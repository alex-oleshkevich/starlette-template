import importlib.util
from unittest import mock

import pytest
from redis.asyncio import Redis

from app.config.settings import Config
from app.contrib.cache import Cache, JsonCacheSerializer
from app.contrib.cache.backends.memory import MemoryCacheBackend
from app.contrib.cache.backends.redis import RedisCacheBackend


class TestCache:
    async def test_get_set(self) -> None:
        cache = Cache(MemoryCacheBackend())
        await cache.set("key", "value", 60)
        assert await cache.get("key") == "value"

    async def test_namespace(self) -> None:
        backend = MemoryCacheBackend()
        cache = Cache(
            backend,
            namespace="test",
        )
        with mock.patch("time.time", return_value=0):
            await cache.set("key", "value", 60)
            assert backend.cache == {"test:key": (b'"value"', 60)}


class TestMemoryCacheBackend:
    async def test_get_set(self) -> None:
        backend = MemoryCacheBackend()
        await backend.set("key", b"value", 60)
        assert await backend.get("key") == b"value"

    async def test_expiration(self) -> None:
        backend = MemoryCacheBackend()
        await backend.set("key", b"value", -1)
        assert await backend.get("key") is None
        assert backend.cache == {}

    async def test_missing_key(self) -> None:
        backend = MemoryCacheBackend()
        assert await backend.get("key2") is None


@pytest.mark.skipif(not importlib.util.find_spec("redis"), reason="Redis is not installed.")
class TestRedisCacheBackend:
    async def test_get_set(self, settings: Config) -> None:
        client = Redis.from_url(settings.redis_url)
        backend = RedisCacheBackend(client)
        await backend.set("key", b"value", 60)
        assert await backend.get("key") == b"value"


class TestJSONSerializer:
    def test_serializer(self) -> None:
        serializer = JsonCacheSerializer()
        assert serializer.deserialize(serializer.serialize("value")) == "value"
