import json

import pytest
from starlette.exceptions import HTTPException as StarletteHTTPException

from app import error_codes
from app.error_codes import ErrorCode
from app.http.error_handlers import exception_handler
from app.http.exceptions import (
    AuthenticationError,
    BadRequestError,
    HTTPException,
    NotFoundError,
    PermissionDeniedError,
    RateLimitedError,
    ResourceConflictError,
    ValidationError,
)
from tests.factories import RequestFactory, RequestScopeFactory


class TestExceptionHandler:
    def test_exception_handler_with_htmx_request(self) -> None:
        exc = Exception("Test exception")
        request = RequestFactory(scope=RequestScopeFactory(headers=((b"hx-request", b"1"),)))
        response = exception_handler(request, exc)
        assert response.status_code == 500
        assert response.headers.get("x-error-code") == error_codes.SERVER_ERROR.code
        assert json.loads(response.headers.get("hx-trigger", "")) == {
            "toast": {"category": "error", "message": "Application error, please try again later."}
        }

    def test_exception_handler_with_json_request(self) -> None:
        exc = Exception("Test exception")
        request = RequestFactory(scope=RequestScopeFactory(headers=((b"accept", b"application/json"),)))
        response = exception_handler(request, exc)
        assert response.status_code == 500
        assert response.headers.get("content-type") == "application/json"
        assert response.headers.get("x-error-code") == error_codes.SERVER_ERROR.code
        assert json.loads(response.body) == {
            "message": "Application error, please try again later.",
            "code": "server_error",
            "field_errors": {},
            "non_field_errors": [],
        }

    def test_exception_handler_with_html_request(self) -> None:
        exc = Exception("Test exception")
        request = RequestFactory(scope=RequestScopeFactory(headers=((b"accept", b"text/html"),)))
        response = exception_handler(request, exc)
        assert response.status_code == 500
        assert response.headers.get("x-error-code") == error_codes.SERVER_ERROR.code
        assert b"Application error, please try again later." in response.body

    @pytest.mark.parametrize(
        "status_code, error_code",
        [
            (400, error_codes.BAD_REQUEST),
            (401, error_codes.AUTH_UNAUTHENTICATED),
            (403, error_codes.PERMISSION_DENIED),
            (404, error_codes.RESOURCE_NOT_FOUND),
            (409, error_codes.RESOURCE_CONFLICT),
            (422, error_codes.VALIDATION_ERROR),
            (429, error_codes.RATE_LIMITED),
            (503, error_codes.SERVER_ERROR),
        ],
    )
    def test_converts_starlette_status_code_to_error_code(self, status_code: int, error_code: ErrorCode) -> None:
        exc = StarletteHTTPException(status_code=status_code)
        request = RequestFactory(scope=RequestScopeFactory(headers=((b"accept", b"application/json"),)))
        response = exception_handler(request, exc)
        assert response.status_code == status_code
        assert json.loads(response.body)["code"] == error_code.code


class TestHTTPExceptionHandler:
    def test_exception_handler_with_htmx_request(self) -> None:
        exc = HTTPException()
        request = RequestFactory(scope=RequestScopeFactory(headers=((b"hx-request", b"1"),)))
        response = exception_handler(request, exc)
        assert response.status_code == 500
        assert json.loads(response.headers.get("hx-trigger", "")) == {
            "toast": {"category": "error", "message": "Application error, please try again later."}
        }

    def test_exception_handler_with_json_request(self) -> None:
        exc = HTTPException()
        request = RequestFactory(scope=RequestScopeFactory(headers=((b"accept", b"application/json"),)))
        response = exception_handler(request, exc)
        assert response.status_code == 500
        assert response.headers.get("content-type") == "application/json"
        assert json.loads(response.body) == {
            "message": "Application error, please try again later.",
            "code": "server_error",
            "field_errors": {},
            "non_field_errors": [],
        }

    def test_exception_handler_with_html_request(self) -> None:
        exc = HTTPException()
        request = RequestFactory(scope=RequestScopeFactory(headers=((b"accept", b"text/html"),)))
        response = exception_handler(request, exc)
        assert response.status_code == 500
        assert response.headers.get("content-type") == "text/html; charset=utf-8"
        assert b"Application error, please try again later." in response.body

    def test_exception_handler_with_json_request_with_field_errors(self) -> None:
        exc = HTTPException(field_errors={"field": ["error1", "error2"]}, non_field_errors=["error3"])
        request = RequestFactory(scope=RequestScopeFactory(headers=((b"accept", b"application/json"),)))
        response = exception_handler(request, exc)
        assert response.status_code == 500
        assert response.headers.get("content-type") == "application/json"
        assert json.loads(response.body) == {
            "message": "Application error, please try again later.",
            "code": "server_error",
            "field_errors": {"field": ["error1", "error2"]},
            "non_field_errors": ["error3"],
        }


@pytest.mark.parametrize(
    "exception, status_code, error_code",
    [
        (HTTPException, 500, error_codes.SERVER_ERROR),
        (BadRequestError, 400, error_codes.BAD_REQUEST),
        (AuthenticationError, 401, error_codes.AUTH_UNAUTHENTICATED),
        (PermissionDeniedError, 403, error_codes.PERMISSION_DENIED),
        (NotFoundError, 404, error_codes.RESOURCE_NOT_FOUND),
        (ResourceConflictError, 409, error_codes.RESOURCE_CONFLICT),
        (ValidationError, 422, error_codes.VALIDATION_ERROR),
        (RateLimitedError, 429, error_codes.RATE_LIMITED),
    ],
)
def test_known_http_exceptions(exception: type[Exception], status_code: int, error_code: ErrorCode) -> None:
    request = RequestFactory(scope=RequestScopeFactory())
    response = exception_handler(request, exception())
    assert response.status_code == status_code
    assert response.headers.get("x-error-code") == error_code.code
