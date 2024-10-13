import functools
import typing

from starlette.requests import Request
from starlette_flash import flash

from app.config import settings
from app.contrib.urls import abs_url_for, media_url, pathname_matches, static_url, url_matches


def app_processor(request: Request) -> dict[str, typing.Any]:
    return {
        "app": request.app,
        "settings": settings,
        "url": request.url_for,
        "abs_url": functools.partial(abs_url_for, request),
        "url_matches": functools.partial(url_matches, request),
        "pathname_matches": functools.partial(pathname_matches, request),
        "static_url": functools.partial(static_url, request),
        "media_url": functools.partial(media_url, request),
        "flash_messages": flash(request),
        "app_theme": request.cookies.get("theme", "light"),
        **(getattr(request.state, "template_context", {})),
    }
