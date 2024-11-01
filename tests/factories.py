from __future__ import annotations

import typing
import uuid

import factory
import faker as fakerlib
from factory.alchemy import SQLAlchemyModelFactory
from starlette.applications import Starlette
from starlette.requests import Request

from app.config.crypto import make_password
from app.contexts.subscriptions.models import SubscriptionPlan
from app.contexts.teams.models import Team, TeamMember, TeamRole
from app.contexts.users.models import User
from tests.database import SyncSession

faker = fakerlib.Faker()
T = typing.TypeVar("T")

Factory = factory.Factory


class BaseModelFactory(SQLAlchemyModelFactory):
    class Meta:
        abstract = True
        sqlalchemy_session = SyncSession
        sqlalchemy_session_persistence = "commit"


class RequestScopeFactory(factory.DictFactory):
    type: str = "http"
    method: str = "GET"
    http_version: str = "1.1"
    server: tuple[str, int] = ("testserver", 80)
    client: tuple[str, int] = ("testclient", 80)
    scheme: str = "http"
    path: str = "/"
    raw_path: bytes = b"/"
    query_string: bytes = b""
    root_path: str = ""
    app: Starlette | None = None
    state: dict[str, typing.Any] | None = None
    headers: tuple[tuple[bytes, bytes], ...] = (
        (b"host", b"testserver"),
        (b"connection", b"close"),
        (b"user-agent", b"testclient"),
        (b"accept", b"*/*"),
    )


class RequestFactory(factory.Factory[Request]):
    scope: factory.SubFactory = factory.SubFactory(RequestScopeFactory)

    class Meta:
        model = Request


class UserFactory(BaseModelFactory):
    first_name: str = factory.Faker("first_name")
    last_name: factory.Faker = factory.Faker("last_name")
    email: factory.LazyFunction = factory.LazyFunction(lambda: uuid.uuid4().hex + "@example.com")
    password: str = make_password("password")

    class Meta:
        model = User


class SubscriptionPlanFactory(BaseModelFactory):
    name: str = factory.Faker("word")
    description: str = factory.Faker("sentence")
    price: float = 10000
    is_default: bool = False
    is_archived: bool = False

    class Meta:
        model = SubscriptionPlan


class TeamFactory(BaseModelFactory):
    name: str = factory.Faker("company")
    owner: User = factory.SubFactory(UserFactory)

    class Meta:
        model = Team


class TeamRoleFactory(BaseModelFactory):
    team: Team = factory.SubFactory(TeamFactory)
    name: str = factory.Faker("word")
    is_admin: bool = True

    class Meta:
        model = TeamRole


class TeamMemberFactory(BaseModelFactory):
    team: Team = factory.SubFactory(TeamFactory)
    user: User = factory.SubFactory(UserFactory)
    role: TeamRole = factory.SubFactory(TeamRoleFactory)

    class Meta:
        model = TeamMember
