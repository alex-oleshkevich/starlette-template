import functools
import typing

from markupsafe import Markup
from starlette.requests import Request
from starlette_babel.locale import get_language
from starlette_flash import flash

from app.config import settings
from app.config.permissions import guards
from app.config.permissions.context import Guard
from app.contrib.urls import abs_url_for, media_url, pathname_matches, static_url, url_matches


def css_classes(**classes: bool) -> str:
    """Generate a string of CSS classes."""
    return Markup(" ".join(name for name, enabled in classes.items() if enabled))


def app_processor(request: Request) -> dict[str, typing.Any]:
    """Add general context to the template."""
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
        "app_language": get_language(),
        "current_user": request.user,
        "css_classes": css_classes,
        **(getattr(request.state, "template_context", {})),
    }


def authenticated_processor(request: Request) -> dict[str, typing.Any]:
    """Add authenticated context to the template."""
    authenticated_context = {}

    try:
        guard = Guard(request.state.access_context)
        authenticated_context.update(
            {
                "current_team": request.state.team,
                "current_team_member": request.state.team_member,
                "current_subscription": request.state.subscription,
                "team_memberships": request.state.team_memberships,
                "is_granted": guard.check,
                "permissions": guards,
            }
        )
    except AttributeError:
        pass
    return authenticated_context
