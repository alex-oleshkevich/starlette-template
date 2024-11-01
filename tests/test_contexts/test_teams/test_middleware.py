from unittest import mock

from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse
from starlette.routing import Route, Router

from app.contexts.teams.middleware import RequireTeamMiddleware, TeamMiddleware
from app.contexts.teams.models import TeamMember
from tests.factories import RequestScopeFactory, TeamFactory, TeamMemberFactory, TeamRoleFactory, UserFactory


class TestTeamMiddleware:
    async def test_requires_http_context(self) -> None:
        app = mock.AsyncMock()
        middleware = TeamMiddleware(app, cookie_name="team_id", query_param="team_id")
        scope = RequestScopeFactory(type="lifespan")
        send_mock = mock.AsyncMock()
        await middleware(scope, mock.AsyncMock(), send_mock)
        assert app.call_count == 1
        assert send_mock.call_count == 0

    async def test_no_team_id(self, dbsession: AsyncSession) -> None:
        """It should not set the team if there are no teams that user is member of."""
        user = UserFactory()

        scope = RequestScopeFactory(
            type="http",
            user=user,
            state={"dbsession": dbsession},
        )
        app = mock.AsyncMock()
        middleware = TeamMiddleware(app, cookie_name="team_id", query_param="team_id")
        await middleware(scope, mock.AsyncMock(), mock.AsyncMock())
        assert scope["state"]["team"] is None
        assert scope["state"]["team_member"] is None
        assert scope["state"]["team_memberships"] == []
        app.assert_called_once()

    async def test_team_from_cookie(self, team_member: TeamMember, dbsession: AsyncSession) -> None:
        scope = RequestScopeFactory(
            type="http",
            user=team_member.user,
            state={"dbsession": dbsession},
            headers=[(b"cookie", f"team_id={team_member.team_id}".encode())],
        )
        app = mock.AsyncMock()
        middleware = TeamMiddleware(app, cookie_name="team_id", query_param="team_id")
        await middleware(scope, mock.AsyncMock(), mock.AsyncMock())
        assert scope["state"]["team"].id == team_member.team.id
        assert scope["state"]["team_member"].id == team_member.id
        app.assert_called_once()

    async def test_invalid_team_from_cookie(self, team_member: TeamMember, dbsession: AsyncSession) -> None:
        team = TeamFactory()
        scope = RequestScopeFactory(
            type="http",
            user=team_member.user,
            state={"dbsession": dbsession},
            headers=[(b"cookie", f"team_id={team.id}".encode())],
        )
        app = mock.AsyncMock()
        middleware = TeamMiddleware(app, cookie_name="team_id", query_param="team_id")
        await middleware(scope, mock.AsyncMock(), mock.AsyncMock())
        assert scope["state"]["team"] != team
        app.assert_called_once()

    async def test_team_from_query(self, team_member: TeamMember, dbsession: AsyncSession) -> None:
        scope = RequestScopeFactory(
            type="http",
            user=team_member.user,
            state={"dbsession": dbsession},
            query_string=f"team_id={team_member.team_id}".encode(),
        )
        app = mock.AsyncMock()
        middleware = TeamMiddleware(app, cookie_name="team_id", query_param="team_id")
        await middleware(scope, mock.AsyncMock(), mock.AsyncMock())
        assert scope["state"]["team"].id == team_member.team.id
        assert scope["state"]["team_member"].id == team_member.id
        app.assert_called_once()

    async def test_team_from_cookie_and_query(self, team_member: TeamMember, dbsession: AsyncSession) -> None:
        """Value from query string should take precedence over cookie."""
        scope = RequestScopeFactory(
            type="http",
            user=team_member.user,
            state={"dbsession": dbsession},
            headers=[(b"cookie", b"team_id=2")],
            query_string=f"team_id={team_member.team_id}".encode(),
        )
        app = mock.AsyncMock()
        middleware = TeamMiddleware(app, cookie_name="team_id", query_param="team_id")
        await middleware(scope, mock.AsyncMock(), mock.AsyncMock())
        assert scope["state"]["team"].id == team_member.team.id
        assert scope["state"]["team_member"].id == team_member.id
        app.assert_called_once()

    async def test_set_query_to_cookie(self, team_member: TeamMember, dbsession: AsyncSession) -> None:
        """Value from query string should take precedence over cookie.
        If the query string is set, the cookie should be updated."""
        scope = RequestScopeFactory(
            type="http",
            user=team_member.user,
            state={"dbsession": dbsession},
            query_string=f"team_id={team_member.team_id}".encode(),
        )
        send_mock = mock.AsyncMock()
        middleware = TeamMiddleware(
            Router(routes=[Route("/", lambda _: JSONResponse({}), name="home")]),
            cookie_name="team_id",
            query_param="team_id",
        )
        await middleware(scope, mock.AsyncMock(), send_mock)
        assert send_mock.call_args_list[0].args[0]["headers"] == [
            (b"content-length", b"2"),
            (b"content-type", b"application/json"),
            (b"set-cookie", f'team_id={team_member.team_id};path="/";httponly'.encode()),
        ]

    async def test_selects_first_team(self, dbsession: AsyncSession) -> None:
        """It should automatically select the first team if there is only one and not cookie/query value available."""
        user = UserFactory()
        team = TeamFactory(owner=user)
        team_member = TeamMemberFactory(role=TeamRoleFactory(team=team), team=team, user=user)

        scope = RequestScopeFactory(
            type="http",
            user=team_member.user,
            state={"dbsession": dbsession},
        )
        send_mock = mock.AsyncMock()
        middleware = TeamMiddleware(
            Router(routes=[Route("/", lambda _: JSONResponse({}), name="home")]),
            cookie_name="team_id",
            query_param="team_id",
        )
        await middleware(scope, mock.AsyncMock(), send_mock)
        assert send_mock.call_args_list[0].args[0]["headers"] == [
            (b"content-length", b"2"),
            (b"content-type", b"application/json"),
            (b"set-cookie", f'team_id={team_member.team_id};path="/";httponly'.encode()),
        ]


class TestRequireTeamMiddleware:
    async def test_requires_http_context(self) -> None:
        app = mock.AsyncMock()
        middleware = RequireTeamMiddleware(app, redirect_path_name="select")
        scope = RequestScopeFactory(type="lifespan")
        send_mock = mock.AsyncMock()
        await middleware(scope, mock.AsyncMock(), send_mock)
        assert app.call_count == 1
        assert send_mock.call_count == 0

    async def test_with_no_team_in_state(self) -> None:
        app = mock.AsyncMock()
        middleware = RequireTeamMiddleware(Router(), redirect_path_name="select")
        scope = RequestScopeFactory(
            type="http",
            state={"team": None},
            router=Router(
                routes=[
                    Route("/select", lambda _: JSONResponse({}), name="select"),
                ]
            ),
        )
        send_mock = mock.AsyncMock()
        await middleware(scope, mock.AsyncMock(), send_mock)
        assert app.call_count == 0
        assert send_mock.call_args_list[0].args[0]["headers"] == [
            (b"content-length", b"0"),
            (b"location", b"http://testserver/select"),
        ]

    async def test_does_not_redirect_to_selection_page(self, team_member: TeamMember) -> None:
        app = Router(
            routes=[
                Route("/select", lambda _: JSONResponse({}), name="select"),
            ]
        )
        middleware = RequireTeamMiddleware(app, redirect_path_name="select")
        scope = RequestScopeFactory(
            type="http",
            path="/select",
            raw_path=b"/select",
            state={"team": None},
            router=app,
        )
        send_mock = mock.AsyncMock()
        await middleware(scope, mock.AsyncMock(), send_mock)

    async def test_with_team(self, team_member: TeamMember) -> None:
        app = mock.AsyncMock()
        middleware = RequireTeamMiddleware(app, redirect_path_name="select")
        scope = RequestScopeFactory(type="http", state={"team": team_member.team})
        send_mock = mock.AsyncMock()
        await middleware(scope, mock.AsyncMock(), send_mock)
        assert app.call_count == 1
        assert send_mock.call_count == 0
