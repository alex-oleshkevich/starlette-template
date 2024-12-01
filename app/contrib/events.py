import logging
import time
import typing

import anyio
import saq
from pydantic import BaseModel
from saq.types import Context

type EventHandler = typing.Callable[[Event], typing.Awaitable[None]]
type Subscribers = dict[type[Event], list[EventHandler]]


class TaskCallback(typing.Protocol):
    def __call__(self, ctx: Context, *, envelope: dict[str, typing.Any]) -> typing.Awaitable[None]: ...


class Event(BaseModel):
    @classmethod
    def event_type(cls) -> str:
        return f"{cls.__module__}:{cls.__name__}"


T = typing.TypeVar("T", bound=Event)


class Envelope(BaseModel, typing.Generic[T]):
    type: str
    event: T


TASK_NAME = "dispatch_event"
logger = logging.getLogger(__name__)


class EventDispatcher:
    def __init__(self, task_queue_url: str, subscribers: Subscribers, sync: bool = False) -> None:
        self._task_queue = saq.Queue.from_url(task_queue_url)
        self._sync = sync
        self._event_handlers = subscribers
        self._event_type_map: dict[str, type[Event]] = {
            event.event_type(): event for event in self._event_handlers.keys()
        }

    async def emit(self, event: Event) -> None:
        if self._sync:
            await self.dispatch(event)
            return

        envelope = Envelope(type=event.event_type(), event=event)
        await self._task_queue.enqueue(TASK_NAME, envelope=envelope.model_dump())

    async def call_handler(self, event: Event, handler: EventHandler) -> None:
        start_time = time.time()
        try:
            await handler(event)
        finally:
            elapsed_time = time.time() - start_time
            logger.info(
                f"event {event.event_type()} handled in {elapsed_time:.2f} seconds.",
                extra={
                    "event": event.event_type(),
                    "elapsed_time": elapsed_time,
                },
            )

    async def dispatch(self, event: Event) -> None:
        handlers = self._event_handlers.get(type(event), [])
        logger.info(
            "will dispatch {count} handlers for event {event}".format(
                count=len(handlers),
                event=event.event_type(),
            ),
            extra={
                "event": event.event_type(),
            },
        )
        if len(handlers) == 1:
            await self.call_handler(event, handlers[0])
            return

        async with anyio.create_task_group() as tg:
            for handler in handlers:
                tg.start_soon(self.call_handler, event, handler)

    async def task_handler(self, ctx: Context, *, envelope: dict[str, typing.Any]) -> None:
        event_class = self._event_type_map[envelope["type"]]
        event = event_class(**envelope["event"])
        await self.dispatch(event)

    @property
    def task(self) -> tuple[str, TaskCallback]:
        return TASK_NAME, self.task_handler
