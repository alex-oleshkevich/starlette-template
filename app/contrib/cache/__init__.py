from __future__ import annotations

import datetime
import typing

from app.contrib.cache.backends.base import CacheBackend
from app.contrib.cache.serializers import CacheSerializer, JsonCacheSerializer


class Cache:
    def __init__(
        self, backend: CacheBackend, serializer: CacheSerializer = JsonCacheSerializer(), namespace: str = "cache"
    ) -> None:
        self.backend = backend
        self.namespace = namespace
        self.serializer = serializer

    async def set(self, key: str, value: typing.Any, ttl: datetime.timedelta | int) -> None:
        ttl_seconds = ttl.total_seconds() if isinstance(ttl, datetime.timedelta) else ttl
        await self.backend.set(self._make_key(key), self.serializer.serialize(value), int(ttl_seconds))

    async def get(self, key: str) -> typing.Any | None:
        value = await self.backend.get(self._make_key(key))
        return self.serializer.deserialize(value) if value is not None else None

    def _make_key(self, key: str) -> str:
        return f"{self.namespace}:{key}" if self.namespace else key
