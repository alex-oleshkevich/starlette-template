from redis.asyncio import Redis

from app.config import settings

__all__ = ["redis"]

redis = Redis.from_url(settings.redis_url)
