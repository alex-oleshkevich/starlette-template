import json
import typing

import httpx


class TestHtmxResponse:
    def __init__(self, response: httpx.Response) -> None:
        self.response = response

    def events(self) -> dict[str, typing.Any]:
        value: dict[str, typing.Any] = json.loads(self.response.headers.get("HX-Trigger", "{}"))
        return value

    def triggers(self, event_name: str) -> bool:
        events = self.events()
        return event_name in events


def as_htmx_response(response: httpx.Response) -> TestHtmxResponse:
    return TestHtmxResponse(response)
