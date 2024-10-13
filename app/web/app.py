from starlette.routing import Route, Router

from app.web.version import version_view

web_router = Router(
    [
        Route("/version", version_view),
    ]
)
