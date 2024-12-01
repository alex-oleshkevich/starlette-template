from unittest import mock

from app.contrib.events import Event, EventDispatcher, TASK_NAME


class _DummyEvent(Event): ...


class TestEventDispatcher:
    async def test_emit_sync(self) -> None:
        subscriber = mock.AsyncMock()
        dispatcher = EventDispatcher(
            task_queue_url="",
            subscribers={
                _DummyEvent: [subscriber],
            },
            sync=True,
        )
        event = _DummyEvent()
        dispatcher._task_queue = mock.AsyncMock()
        await dispatcher.emit(event)
        dispatcher._task_queue.assert_not_called()

    async def test_emit_async(self) -> None:
        subscriber = mock.AsyncMock()
        dispatcher = EventDispatcher(
            task_queue_url="",
            subscribers={
                _DummyEvent: [subscriber],
            },
            sync=False,
        )
        event = _DummyEvent()
        dispatcher._task_queue = mock.AsyncMock()
        await dispatcher.emit(event)
        dispatcher._task_queue.enqueue.assert_called_once_with(
            TASK_NAME, envelope={"type": "tests.test_contrib.test_events:_DummyEvent", "event": {}}
        )

    async def test_dispatches_single_handlers_sync(self) -> None:
        subscriber = mock.AsyncMock()
        dispatcher = EventDispatcher(
            task_queue_url="",
            subscribers={
                _DummyEvent: [subscriber],
            },
            sync=False,
        )
        event = _DummyEvent()
        await dispatcher.dispatch(event)
        subscriber.assert_called_once_with(event)

    async def test_dispatches_multiple_handlers_sync(self) -> None:
        subscriber = mock.AsyncMock()
        subscriber2 = mock.AsyncMock()
        dispatcher = EventDispatcher(
            task_queue_url="",
            subscribers={
                _DummyEvent: [subscriber, subscriber2],
            },
            sync=False,
        )
        event = _DummyEvent()
        await dispatcher.dispatch(event)
        subscriber.assert_called_once_with(event)
        subscriber2.assert_called_once_with(event)

    async def test_dispatches_from_queue(self) -> None:
        subscriber = mock.AsyncMock()
        dispatcher = EventDispatcher(
            task_queue_url="",
            subscribers={
                _DummyEvent: [subscriber],
            },
            sync=False,
        )
        event = _DummyEvent()
        await dispatcher.task_handler(mock.MagicMock(), envelope={"type": event.event_type(), "event": {}})
        subscriber.assert_called_once_with(event)

    def test_task_function(self) -> None:
        dispatcher = EventDispatcher(task_queue_url="", subscribers={})
        assert dispatcher.task == (TASK_NAME, dispatcher.task_handler)
