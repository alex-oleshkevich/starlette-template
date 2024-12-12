import typing

from fastapi import HTTPException as FastAPIHTTPException
from fastapi.exceptions import RequestValidationError
from starlette import status
from starlette.datastructures import MutableHeaders
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette_babel import gettext_lazy as _

from app import error_codes
from app.exceptions import RateLimitedError
from app.http.error_handlers import common_error_code_mapping
from app.http.exceptions import HTTPException
from app.http.responses import JSONErrorResponse


async def api_fastapi_validation_handler(_request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)

    error_code = error_codes.VALIDATION_ERROR
    message = str(_("Validation error."))
    non_field_error_types = ["model_attributes_type", "model_type"]
    non_field_errors = [str(error["msg"]) for error in exc.errors() if error["type"] in non_field_error_types]
    field_errors = {
        error["loc"][0]: [str(error["msg"])]
        for error in exc.errors()
        if len(error["loc"]) and error["type"] not in non_field_error_types
    }

    return JSONErrorResponse(
        message=message,
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        error_code=error_code,
        field_errors=field_errors,
        non_field_errors=non_field_errors,
    )


async def api_rate_limited_handler(request: Request, exc: RateLimitedError) -> Response:
    assert isinstance(exc, RateLimitedError)
    return JSONErrorResponse(
        message=str(exc),
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        error_code=error_codes.RATE_LIMITED,
        headers={
            "Retry-After": str(exc.stats.reset_time),
            "X-RateLimit-Remaining": str(exc.stats.remaining),
            "X-RateLimit-Reset": str(exc.stats.reset_time),
        },
    )


async def api_exception_handler(request: Request, exc: Exception) -> Response:
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

    if isinstance(exc, StarletteHTTPException | FastAPIHTTPException):
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

    return JSONErrorResponse(
        message,
        status_code=status_code,
        error_code=error_code,
        headers=response_headers,
        field_errors=field_errors,
        non_field_errors=non_field_errors,
    )
