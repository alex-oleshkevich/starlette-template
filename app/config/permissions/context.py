import dataclasses

from starlette.authentication import AuthCredentials
from starlette.requests import HTTPConnection
from starlette.types import ASGIApp, Receive, Scope, Send

from app.config.permissions import permissions
from app.contexts.billing.models import Subscription, SubscriptionPlan
from app.contexts.teams.models import Team, TeamMember
from app.contexts.users.models import User
from app.contrib.permissions import (
    Permission,
    Resource,
    Rule,
    check_rule,
    check_rule_or_raise,
    get_defined_permissions,
)


@dataclasses.dataclass
class AccessContext:
    user: User
    team: Team
    scopes: set[Permission]
    team_member: TeamMember
    subscription: Subscription | None
    subscription_plan: SubscriptionPlan | None


class Guard:
    def __init__(self, access_context: AccessContext) -> None:
        self._access_context = access_context

    def check(self, rule: Rule, resource: Resource | None = None) -> bool:
        """Check if the given rule is satisfied in the current context."""
        return check_rule(self._access_context, rule, resource)

    def check_or_raise(self, rule: Rule, resource: Resource | None = None) -> None:
        """Check if the given rule is satisfied in the current context, raise AccessDeniedError if not."""
        return check_rule_or_raise(self._access_context, rule, resource)


class AccessContextMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        assert scope["type"] in ["http", "websocket"]

        request = HTTPConnection(scope)
        user: User = request.user
        try:
            team: Team = request.state.team
            team_member: TeamMember = request.state.team_member
        except AttributeError:
            raise ValueError("TeamMiddleware must be installed before AccessContextMiddleware.")

        try:
            subscription: Subscription = request.state.subscription
        except AttributeError:
            raise ValueError("SubscriptionMiddleware must be installed before AccessContextMiddleware.")

        auth: AuthCredentials = request.auth
        scopes = set(self.get_user_scopes(auth.scopes + team_member.role.permissions))
        request.state.access_context = AccessContext(
            user=user,
            team=team,
            scopes=scopes,
            team_member=team_member,
            subscription=subscription,
            subscription_plan=subscription.plan if subscription else None,
        )
        await self.app(scope, receive, send)

    def get_user_scopes(self, scopes: list[str]) -> list[Permission]:
        defined_permissions = {p.id: p for p in get_defined_permissions(permissions)}
        return [defined_permissions[permission] for permission in scopes if permission in defined_permissions]
