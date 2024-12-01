import json
import typing
import uuid

import httpx
from starlette.testclient import TestClient
from starlette.types import ASGIApp
from starlette_auth.authentication import SESSION_HASH, SESSION_KEY
from starsessions import SessionStore

from app.config import settings
from app.contexts.teams.models import Team
from app.contexts.users.models import User


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


class TestAuthClient(TestClient):
    def __init__(
        self,
        app: ASGIApp,
        session_store: SessionStore,
        session_cookie: str,
        team_cookie: str,
        base_url: str = "http://testserver",
        raise_server_exceptions: bool = True,  # noqa: FBT001,FBT002
        root_path: str = "",
        backend: typing.Literal["asyncio", "trio"] = "asyncio",
        backend_options: dict[str, typing.Any] | None = None,
        cookies: httpx._types.CookieTypes | None = None,
        headers: dict[str, str] | None = None,
        follow_redirects: bool = True,  # noqa: FBT001,FBT002
    ) -> None:
        self._session_store = session_store
        self._session_cookie = session_cookie
        self._team_cookie = team_cookie
        super().__init__(
            app,
            base_url,
            raise_server_exceptions,
            root_path,
            backend,
            backend_options,
            cookies,
            headers,
            follow_redirects,
        )

    async def force_user(self, user: User) -> None:
        """Force a user to be logged in.
        This will create a new user session."""
        session_id = uuid.uuid4().hex
        self.cookies.update({self._session_cookie: session_id})
        await self._session_store.write(
            session_id=session_id,
            ttl=int(settings.session_lifetime.total_seconds()),
            lifetime=int(settings.session_lifetime.total_seconds()),
            data=json.dumps(
                {
                    SESSION_KEY: user.id,
                    SESSION_HASH: user.get_session_auth_hash(settings.secret_key),
                }
            ).encode(),
        )

    def force_team(self, team: Team) -> None:
        self.cookies.update({self._team_cookie: str(team.id)})

    def clear_team(self) -> None:
        self.cookies.pop(self._team_cookie, None)

    def __enter__(self) -> typing.Self:
        return typing.cast(typing.Self, super().__enter__())
