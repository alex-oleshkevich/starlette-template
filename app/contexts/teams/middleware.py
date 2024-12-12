import contextlib
import functools

from starlette.datastructures import MutableHeaders
from starlette.requests import Request
from starlette.responses import RedirectResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.contexts.teams.repo import TeamRepo


class TeamMiddleware:
    """Middleware to load the current team from a cookie or query parameter.
    If both are present, the query parameter takes precedence.
    If user is not a member of any team, the team and member will not be set."""

    def __init__(self, app: ASGIApp, cookie_name: str = "team_id", query_param: str = "team_id") -> None:
        self.app = app
        self.cookie_name = cookie_name
        self.query_param = query_param

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in {"http", "websocket"}:
            await self.app(scope, receive, send)
            return

        async def send_wrapper(message: Message, team_id: int) -> None:
            if message["type"] != "http.response.start":
                await send(message)
                return

            headers = MutableHeaders(scope=message)
            header_value = f'{self.cookie_name}={team_id};path="/";httponly'
            headers.append("set-cookie", header_value)

            await send(message)

        team_id: int | None = None
        request = Request(scope)
        if not request.user.is_authenticated:
            await self.app(scope, receive, send)
            return

        repo = TeamRepo(request.state.dbsession)
        memberships = await repo.get_active_memberships(int(request.user.identity))
        request.state.team = None
        request.state.team_member = None
        request.state.team_memberships = memberships

        with contextlib.suppress(TypeError, ValueError):
            team_id = int(request.query_params.get(self.query_param, request.cookies.get(self.cookie_name, "")))
            for membership in memberships:
                if membership.team_id == team_id:
                    request.state.team = membership.team
                    request.state.team_member = membership
                    break

        if request.state.team is None and len(memberships) == 1:
            request.state.team = memberships[0].team
            request.state.team_member = memberships[0]
            team_id = request.state.team.id

        if team_id:
            await self.app(scope, receive, functools.partial(send_wrapper, team_id=team_id))
        else:
            await self.app(scope, receive, send)


class RequireTeamMiddleware:
    """Middleware to redirect to a specified path if the user is not a member of any team."""

    def __init__(self, app: ASGIApp, redirect_path_name: str) -> None:
        self.app = app
        self.redirect_path_name = redirect_path_name

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in {"http", "websocket"}:
            await self.app(scope, receive, send)
            return

        request = Request(scope)
        if request.state.team is None:
            redirect_url = request.url_for(self.redirect_path_name)
            if redirect_url.path == request.url.path:
                await self.app(scope, receive, send)
                return

            response = RedirectResponse(redirect_url)
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)
