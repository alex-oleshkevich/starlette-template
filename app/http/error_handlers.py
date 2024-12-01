import logging
import typing

from starlette import status
from starlette.datastructures import MutableHeaders
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request
from starlette.responses import Response

from app import error_codes
from app.config.templating import templates
from app.contrib import htmx
from app.http.exceptions import HTTPException
from app.http.responses import JSONErrorResponse

logger = logging.getLogger(__name__)


def remap_exception(new_exception: type[Exception]) -> typing.Callable[[Request, Exception], Response]:
    """Remap one exception to another.
    Used to integrate with third-party libraries that raise their own exceptions."""

    def handler(request: Request, _: Exception) -> Response:
        return exception_handler(request, new_exception())

    return handler


def exception_handler(request: Request, exc: Exception) -> Response:
    """Default exception handler for HTTP exceptions.

    It should not handle any non-HTTP exceptions, instead let them bubble up to the Starlette's exception handler
    that handles all exceptions and returns a generic error message with status code 500.
    This lets us catch and log all exceptions in one place as well as send them to Sentry.
    """
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code = error_codes.SERVER_ERROR
    message = str(error_code)
    headers: typing.Mapping[str, str] = {}
    field_errors: dict[str, list[str]] = {}
    non_field_errors: list[str] = []
    common_error_code_mapping = {
        400: error_codes.BAD_REQUEST,
        401: error_codes.AUTH_UNAUTHENTICATED,
        403: error_codes.PERMISSION_DENIED,
        404: error_codes.RESOURCE_NOT_FOUND,
        409: error_codes.RESOURCE_CONFLICT,
        422: error_codes.VALIDATION_ERROR,
        429: error_codes.RATE_LIMITED,
    }

    if isinstance(exc, StarletteHTTPException):
        status_code = exc.status_code
        message = exc.detail
        headers = exc.headers or {}
        error_code = common_error_code_mapping.get(status_code, error_codes.SERVER_ERROR)

    if isinstance(exc, HTTPException):
        message = exc.detail
        status_code = exc.status_code
        error_code = exc.error_code
        headers = exc.headers or {}
        field_errors = exc.field_errors
        non_field_errors = exc.non_field_errors

    # expose error code in headers for easier debugging
    response_headers = MutableHeaders(headers)
    response_headers.setdefault("x-error-code", error_code.code)

    if htmx.is_htmx_request(request):
        return htmx.response(status_code=status_code, headers=response_headers).error_toast(message)

    if "application/json" in request.headers.get("accept", ""):
        return JSONErrorResponse(
            message,
            status_code=status_code,
            error_code=error_code,
            headers=response_headers,
            field_errors=field_errors,
            non_field_errors=non_field_errors,
        )

    return templates.TemplateResponse(
        request,
        "web/service/http_error.html",
        {"status_code": status_code, "error_message": message},
        status_code=status_code,
        headers=response_headers,
    )
