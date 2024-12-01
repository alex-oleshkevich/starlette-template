from app import settings
from app.contexts.auth.events import UserAuthenticated
from app.contrib.events import EventDispatcher

events = EventDispatcher(
    task_queue_url=settings.task_queue_url,
    sync=False,
    subscribers={
        UserAuthenticated: [],
    },
)
