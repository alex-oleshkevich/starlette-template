from limits import RateLimitItem
from limits.aio.storage import RedisStorage
from limits.aio.strategies import MovingWindowRateLimiter

from app.config import settings
from app.exceptions import RateLimitedError


class RateLimiter:
    def __init__(self, item: RateLimitItem, namespace: str) -> None:
        self.item = item
        self.namespace = f"rate_limit:{settings.app_slug}:{settings.app_env}:{namespace}"
        self.storage = RedisStorage(settings.redis_url)
        self.limiter = MovingWindowRateLimiter(self.storage)

    async def hit(self, actor_id: str) -> bool:
        return await self.limiter.hit(self.item, self.namespace, actor_id)

    async def hit_or_raise(self, actor_id: str) -> None:
        if not await self.hit(actor_id):
            stats = await self.limiter.get_window_stats(self.item, self.namespace, actor_id)
            raise RateLimitedError(stats=stats)

    async def clear(self, actor_id: str) -> None:
        await self.limiter.clear(self.item, self.namespace, actor_id)

    async def reset(self) -> None:
        await self.storage.reset()
