from __future__ import annotations

import datetime
import typing
import uuid

import factory
import faker as fakerlib
from factory.alchemy import SQLAlchemyModelFactory
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Mount, Route

from app.config.crypto import make_password
from app.config.permissions.context import AccessContext
from app.contexts.billing.models import Subscription, SubscriptionPlan
from app.contexts.teams.models import Team, TeamInvite, TeamMember, TeamRole
from app.contexts.users.models import User
from app.contrib.permissions import Permission
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
    app: Starlette = factory.LazyFunction(
        lambda: Starlette(
            debug=False,
            routes=[
                Route("/", lambda: Response("index"), name="home"),
                Mount("/static", Response("static"), name="static"),
            ],
        )
    )
    user: typing.Any | None = None
    session: dict[str, typing.Any] = factory.LazyFunction(dict)
    state: dict[str, typing.Any] = factory.LazyFunction(dict)
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
    is_admin: bool = False

    class Meta:
        model = TeamRole


class TeamMemberFactory(BaseModelFactory):
    team: Team = factory.SubFactory(TeamFactory)
    user: User = factory.SelfAttribute("team.owner")
    role: TeamRole = factory.LazyAttribute(lambda obj: TeamRoleFactory(team=obj.team, is_admin=True, name="Owner"))

    class Meta:
        model = TeamMember


class TeamInviteFactory(BaseModelFactory):
    team: Team = factory.SubFactory(TeamFactory)
    email: str = factory.LazyFunction(lambda: uuid.uuid4().hex + "@example.com")
    role: TeamRole = factory.LazyAttribute(lambda obj: TeamRoleFactory(team=obj.team))
    inviter: TeamMember = factory.LazyAttribute(
        lambda obj: TeamMemberFactory(
            team=obj.team,
            user=obj.team.owner,
            role=TeamRoleFactory(team=obj.team, is_admin=True, name="Owner"),
        )
    )

    token: str = factory.LazyFunction(lambda: uuid.uuid4().hex)

    class Meta:
        model = TeamInvite


class SubscriptionFactory(BaseModelFactory):
    team: Team = factory.SubFactory(TeamFactory)
    plan: SubscriptionPlan = factory.SubFactory(SubscriptionPlanFactory)
    status: Subscription.Status = Subscription.Status.ACTIVE
    created_at: datetime.datetime = factory.LazyFunction(lambda: datetime.datetime.now(datetime.UTC))
    expires_at: datetime.datetime = factory.LazyFunction(
        lambda: datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=30)
    )

    class Meta:
        model = Subscription


class AccessContextFactory(factory.Factory):
    team_member: TeamMember = factory.SubFactory(TeamMemberFactory)
    user: User = factory.SelfAttribute("team_member.user")
    team: Team = factory.SelfAttribute("team_member.team")
    scopes: list[Permission] = factory.LazyFunction(lambda: [Permission("read")])
    subscription: Subscription = factory.SubFactory(SubscriptionFactory)
    subscription_plan: SubscriptionPlan = factory.SelfAttribute("subscription.plan")

    class Meta:
        model = AccessContext
