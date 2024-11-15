import typing

from mailers import Mailer
from redis import Redis as RedisType
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from app.config.cache import cache
from app.config.files import file_storage
from app.config.mailers import mailer
from app.config.pagination import get_page_number, get_page_size
from app.config.redis import redis
from app.config.settings import Config, settings
from app.contexts.billing.exceptions import SubscriptionRequiredError
from app.contexts.billing.models import Subscription
from app.contexts.teams.models import Team, TeamMember
from app.contexts.users.models import User
from app.contrib.cache import Cache as Cache_
from app.contrib.storage import FileStorage


def _get_current_subscription_or_raise(request: Request) -> Subscription:
    subscription: Subscription | None = request.state.subscription
    if subscription is None:
        raise SubscriptionRequiredError()
    return subscription


Files = typing.Annotated[FileStorage, file_storage]
Mail = typing.Annotated[Mailer, mailer]
Cache = typing.Annotated[Cache_, cache]
Redis = typing.Annotated[RedisType, redis]
DbSession = typing.Annotated[AsyncSession, lambda r: r.state.dbsession]
Settings = typing.Annotated[Config, settings]
CurrentUser = typing.Annotated[User, lambda r: r.user]
CurrentTeam = typing.Annotated[Team, lambda r: r.state.team]
CurrentMembership = typing.Annotated[TeamMember, lambda r: r.state.team_member]
CurrentSubscription = typing.Annotated[Subscription | None, lambda r: r.state.subscription]
RequireSubscription = typing.Annotated[Subscription, _get_current_subscription_or_raise]
PageNumber = typing.Annotated[int, lambda r: get_page_number(r)]
PageSize = typing.Annotated[int, lambda r: get_page_size(r)]
