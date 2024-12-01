from app import settings
from app.contexts.auth.events import UserAuthenticated
from app.contrib.events import EventDispatcher

events = EventDispatcher(
    task_queue_url=settings.redis_url,
    sync=settings.debug or settings.is_test,
    subscribers={
        UserAuthenticated: [],
    },
)
