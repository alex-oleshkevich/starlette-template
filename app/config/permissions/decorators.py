import functools
import typing

from starlette.requests import Request
from starlette.responses import Response

from app.config.permissions.context import Guard
from app.contrib.permissions import Rule

_PS = typing.ParamSpec("_PS")


def permission_required(
    get: Rule | None = None,
    post: Rule | None = None,
    put: Rule | None = None,
    patch: Rule | None = None,
    delete: Rule | None = None,
) -> typing.Callable[
    [typing.Callable[_PS, typing.Awaitable[Response]]], typing.Callable[_PS, typing.Awaitable[Response]]
]:
    def decorator(
        func: typing.Callable[_PS, typing.Awaitable[Response]],
    ) -> typing.Callable[_PS, typing.Awaitable[Response]]:
        ruleset = {
            "GET": get,
            "POST": post,
            "PUT": put,
            "PATCH": patch,
            "DELETE": delete,
        }

        @functools.wraps(func)
        async def wrapper(*args: _PS.args, **kwargs: _PS.kwargs) -> Response:
            request = kwargs.get("request")
            if not request and args:
                request = args[0]

            if not isinstance(request, Request):
                raise ValueError(
                    "The first positional argument must be a Request instance, "
                    "or a keyword argument 'request' must be provided. "
                    f"Invalid signature for {func.__name__}."
                )

            rule = ruleset.get(request.method, get) or get
            if rule:
                guard = Guard(request.state.access_context)
                guard.check_or_raise(rule)
            return await func(*args, **kwargs)

        return wrapper

    return decorator
