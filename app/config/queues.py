import logging
import typing

from saq import Queue
from saq.types import Context

from app.config import settings
from app.config.events import events

_P = typing.ParamSpec("_P")


async def debug_task(context: Context) -> None:
    logging.info("Received debug task.")


task_queue = Queue.from_url(settings.task_queue_url)
queue_settings = {
    "queue": task_queue,
    "concurrency": settings.task_queue_concurrency,
    "cron_jobs": [],
    "functions": [
        debug_task,
        events.task,
    ],
}
