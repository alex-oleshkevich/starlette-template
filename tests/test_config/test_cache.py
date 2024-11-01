import pytest

from app.config.cache import cache_backend_factory
from app.contrib.cache.backends.memory import MemoryCacheBackend
from app.contrib.cache.backends.redis import RedisCacheBackend


def test_cache_factory() -> None:
    assert isinstance(cache_backend_factory("redis://"), RedisCacheBackend)
    assert isinstance(cache_backend_factory("rediss://"), RedisCacheBackend)
    assert isinstance(cache_backend_factory("memory://"), MemoryCacheBackend)
    with pytest.raises(NotImplementedError, match="Unknown cache backend"):
        cache_backend_factory("unknown://")
