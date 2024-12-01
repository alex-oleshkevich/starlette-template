import typing
from unittest import mock

import pytest
from starlette.applications import Starlette
from starlette.authentication import AuthCredentials

from app.config.permissions.context import AccessContext, AccessContextMiddleware, Guard
from app.contexts.billing.models import Subscription
from app.contexts.teams.models import TeamMember
from app.contexts.users.models import User
from app.contrib.permissions import AccessDeniedError, Permission
from tests.factories import TeamMemberFactory, TeamRoleFactory


class TestGuard:
    def test_check(self, access_context: AccessContext) -> None:
        guard = Guard(access_context)
        assert guard.check(lambda c, r: True) is True  # type: ignore[arg-type]

    def test_check_or_raise(self, access_context: AccessContext) -> None:
        guard = Guard(access_context)
        with pytest.raises(AccessDeniedError):
            guard.check_or_raise(lambda c, r: False)  # type: ignore[arg-type]


class TestAccessContextMiddleware:
    async def test_requires_http_or_websocket(self) -> None:
        with pytest.raises(AssertionError):
            middleware = AccessContextMiddleware(Starlette())
            await middleware({"type": "lifespan"}, mock.AsyncMock(), mock.AsyncMock())

    async def test_requires_team_middleware(self, user: User) -> None:
        with pytest.raises(ValueError, match="TeamMiddleware"):
            middleware = AccessContextMiddleware(Starlette())
            scope = {
                "type": "http",
                "user": user,
            }
            await middleware(scope, mock.AsyncMock(), mock.AsyncMock())

    async def test_requires_subscription_middleware(self, team_member: TeamMember) -> None:
        with pytest.raises(ValueError, match="SubscriptionMiddleware"):
            middleware = AccessContextMiddleware(Starlette())
            scope = {
                "type": "http",
                "user": team_member.user,
                "state": {
                    "team": team_member.team,
                    "team_member": team_member,
                },
            }
            await middleware(scope, mock.AsyncMock(), mock.AsyncMock())

    async def test_creates_access_context(self, team_subscription: Subscription) -> None:
        team_member = TeamMemberFactory(
            role=TeamRoleFactory(permissions=["team:write"]),
        )

        with mock.patch(
            "app.config.permissions.context.get_defined_permissions",
            return_value=[Permission(id="team:read"), Permission(id="team:write")],
        ):
            middleware = AccessContextMiddleware(mock.AsyncMock())
            scope: dict[str, typing.Any] = {
                "type": "http",
                "user": team_member.user,
                "auth": AuthCredentials(scopes=["team:read"]),
                "state": {
                    "team": team_member.team,
                    "team_member": team_member,
                    "subscription": team_subscription,
                },
            }
            await middleware(scope, mock.AsyncMock(), mock.AsyncMock())
            access_context = scope["state"]["access_context"]
            assert access_context.user == team_member.user
            assert access_context.team == team_member.team
            assert access_context.scopes == {Permission(id="team:read"), Permission(id="team:write")}
            assert access_context.team_member == team_member
            assert access_context.subscription == team_subscription
            assert access_context.subscription_plan == team_subscription.plan
