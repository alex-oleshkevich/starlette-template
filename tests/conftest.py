import typing

import limits
import pytest
from mailers import InMemoryTransport
from mailers.pytest_plugin import Mailbox
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.testclient import TestClient
from starlette_babel import switch_locale, switch_timezone

from app.asgi import app as starlette_app
from app.config import mailers
from app.config import settings as app_settings
from app.config.database import new_dbsession
from app.config.settings import Config
from app.contexts.users.models import User
from tests.factories import RequestFactory, RequestScopeFactory, UserFactory


@pytest.fixture(scope="session")
def settings() -> Config:
    return app_settings


@pytest.fixture
def app() -> Starlette:
    """Return configured Starlette application."""
    return starlette_app


@pytest.fixture(autouse=True, scope="session")
def _switch_timezone() -> typing.Generator[None, None, None]:
    with switch_timezone("UTC"):
        yield


@pytest.fixture(autouse=True, scope="session")
def _switch_language() -> typing.Generator[None, None, None]:
    with switch_locale("en"):
        yield


@pytest.fixture
async def dbsession() -> typing.AsyncGenerator[AsyncSession, None]:
    async with new_dbsession() as dbsession:
        yield dbsession


@pytest.fixture
def mailbox() -> Mailbox:
    assert isinstance(mailers.mail_transport, InMemoryTransport)
    mailers.mail_transport.storage.clear()
    return mailers.mail_transport.storage


@pytest.fixture
def user() -> User:
    return UserFactory()


@pytest.fixture
def client(app: Starlette) -> typing.Generator[TestClient, None, None]:
    """A test client. Not authenticated."""
    with TestClient(app, follow_redirects=False) as client:
        yield client


@pytest.fixture
def auth_client(client: TestClient, user: User, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """Authenticated client."""
    with monkeypatch.context() as m:
        m.setattr("app.web.login.routes.login_limiter", limits.parse("1000/second"))
        response = client.post("/login", data={"email": user.email, "password": "password"})
        assert response.status_code == 302, "Client should be authenticated, got: %s" % response.status_code
    return client


@pytest.fixture
def http_request(app: Starlette, dbsession: AsyncSession) -> Request:
    return RequestFactory(scope=RequestScopeFactory(app=app, state={"dbsession": dbsession}))
