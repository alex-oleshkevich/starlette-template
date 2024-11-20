import typing

from starlette import status
from starlette.exceptions import HTTPException as BaseHTTPException

from app import error_codes
from app.error_codes import ErrorCode


class HTTPException(BaseHTTPException):
    """Base exception class for all HTTP exceptions.

    HTTP exceptions should only be raised in HTTP context - web, api request, etc.
    Any other exception raised during the execution of the application
    should be caught and converted to an HTTP exception."""

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code: ErrorCode = error_codes.SERVER_ERROR

    def __init__(
        self,
        message: str = "",
        *,
        status_code: int | None = None,
        error_code: ErrorCode | None = None,
        headers: dict[str, typing.Any] | None = None,
        field_errors: dict[str, list[str]] | None = None,
        non_field_errors: list[str] | None = None,
    ) -> None:
        status_code = status_code or self.status_code
        error_code = error_code or self.error_code
        message = message or error_code.description
        self.error_code = error_code
        self.field_errors = field_errors or {}
        self.non_field_errors = non_field_errors or []

        super().__init__(status_code=status_code, detail=message, headers=headers)


class BadRequestError(HTTPException):
    """Raise if the request is malformed or invalid.
    For validation errors use ValidationError instead."""

    status_code = status.HTTP_400_BAD_REQUEST
    error_code = error_codes.BAD_REQUEST


class AuthenticationError(HTTPException):
    """Raise if the user is not authenticated but accesses the protected resource."""

    status_code = status.HTTP_401_UNAUTHORIZED
    error_code = error_codes.AUTH_UNAUTHENTICATED


class PermissionDeniedError(HTTPException):
    """Raise if the user is authenticated but does not have permission to access the resource."""

    status_code = status.HTTP_403_FORBIDDEN
    error_code = error_codes.PERMISSION_DENIED


class NotFoundError(HTTPException):
    """Raise if the requested resource does not exist."""

    status_code = status.HTTP_404_NOT_FOUND
    error_code = error_codes.RESOURCE_NOT_FOUND


class ResourceConflictError(HTTPException):
    """Raise if the resource already exists and cannot be created."""

    status_code = status.HTTP_409_CONFLICT
    error_code = error_codes.RESOURCE_CONFLICT


class ValidationError(HTTPException):
    """Raise if the request data is invalid or does not pass the validation.
    Enhance details with `field_errors` and `non_field_errors` to provide more context."""

    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    error_code = error_codes.VALIDATION_ERROR


class RateLimitedError(HTTPException):
    """Raise if the client has sent too many requests in a given amount of time."""

    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    error_code = error_codes.RATE_LIMITED
