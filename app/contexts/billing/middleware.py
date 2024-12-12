from starlette.requests import Request
from starlette.types import ASGIApp, Receive, Scope, Send

from app.contexts.billing.repo import SubscriptionRepo


class SubscriptionMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in {"http", "websocket"}:
            await self.app(scope, receive, send)
            return

        request = Request(scope)
        if not request.user.is_authenticated:
            await self.app(scope, receive, send)
            return

        repo = SubscriptionRepo(request.state.dbsession)
        request.state.subscription = await repo.get_team_subscription(request.state.team.id)

        await self.app(scope, receive, send)
