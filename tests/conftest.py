import typing

import pytest
import sqlalchemy as sa
from mailers import InMemoryTransport
from mailers.pytest_plugin import Mailbox
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session, scoped_session
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.testclient import TestClient
from starlette_babel import switch_locale, switch_timezone
from starsessions import InMemoryStore, SessionStore

from app.asgi import app as starlette_app
from app.config import mailers
from app.config import settings as app_settings
from app.config.database import new_dbsession
from app.config.settings import Config
from app.contexts.subscriptions.models import SubscriptionPlan
from app.contexts.teams.models import Team, TeamMember, TeamRole
from app.contexts.users.models import User
from app.contrib.storage import StorageType
from app.contrib.testing import TestAuthClient
from app.web.app import session_backend as app_session_backend
from tests import database
from tests.factories import (
    RequestFactory,
    RequestScopeFactory,
    SubscriptionPlanFactory,
    TeamFactory,
    TeamMemberFactory,
    TeamRoleFactory,
    UserFactory,
)


@pytest.fixture(scope="session", autouse=True)
def settings() -> Config:
    assert app_settings.storages_type == StorageType.MEMORY, "File storage must be in-memory for tests"
    assert app_settings.database_url.endswith("_test"), 'Database URL must contain "_test" to prevent data loss'

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
async def dbsession(settings: Config) -> typing.AsyncGenerator[AsyncSession, None]:
    async with new_dbsession() as dbsession:
        yield dbsession


@pytest.fixture
def dbsession_sync() -> scoped_session[Session]:
    return database.SyncSession


@pytest.fixture
def mailbox() -> Mailbox:
    assert isinstance(mailers.mail_transport, InMemoryTransport)
    mailers.mail_transport.storage.clear()
    return mailers.mail_transport.storage


@pytest.fixture
def user() -> User:
    return UserFactory()


@pytest.fixture()
def subscription_plan(dbsession_sync: Session) -> typing.Generator[SubscriptionPlan, None, None]:
    stmt = sa.select(SubscriptionPlan).where(SubscriptionPlan.is_default.is_(True))
    plan = dbsession_sync.scalars(stmt).one_or_none()
    if not plan:
        plan = SubscriptionPlanFactory(is_default=True, price=0)
        dbsession_sync.add(plan)
        dbsession_sync.commit()
    yield plan


@pytest.fixture()
def team(user: User) -> Team:
    return TeamFactory(owner=user)


@pytest.fixture()
def team_user_role(team: Team) -> TeamRole:
    return TeamRoleFactory(team=team, is_admin=False)


@pytest.fixture()
def team_admin_role(team: Team) -> TeamRole:
    return TeamRoleFactory(team=team, is_admin=True)


@pytest.fixture()
def team_member(user: User, team: Team, team_admin_role: TeamRole) -> TeamMember:
    return TeamMemberFactory(user=user, team=team, role=team_admin_role)


@pytest.fixture()
def user_session() -> SessionStore:
    assert isinstance(app_session_backend, InMemoryStore)
    return app_session_backend


@pytest.fixture
def client(app: Starlette) -> typing.Generator[TestClient, None, None]:
    """A test client. Not authenticated."""
    with TestClient(app, follow_redirects=False) as client:
        yield client


@pytest.fixture
async def auth_client(
    app: Starlette,
    team_member: TeamMember,
    user_session: SessionStore,
    settings: Config,
) -> typing.AsyncGenerator[TestClient, None]:
    """Authenticated client."""

    with TestAuthClient(
        app,
        session_store=user_session,
        session_cookie=settings.session_cookie,
        team_cookie=settings.team_cookie,
        follow_redirects=False,
    ) as client:
        await client.force_user(team_member.user)
        client.force_team(team_member.team)
        yield client


@pytest.fixture
def http_request(app: Starlette, dbsession: AsyncSession) -> Request:
    return RequestFactory(scope=RequestScopeFactory(app=app, state={"dbsession": dbsession}))


@pytest.fixture()
def free_subscription_plan(dbsession_sync: Session) -> typing.Generator[SubscriptionPlan, None, None]:
    stmt = sa.select(SubscriptionPlan).where(SubscriptionPlan.is_default.is_(True))
    plan = dbsession_sync.scalars(stmt).one_or_none()
    if not plan:
        plan = SubscriptionPlanFactory(is_default=True, price=0)
        dbsession_sync.add(plan)
        dbsession_sync.commit()
    yield plan
