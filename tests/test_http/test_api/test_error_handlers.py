import json

import limits
import pydantic
import pytest
from fastapi.exceptions import HTTPException as FastAPIHTTPException
from starlette.exceptions import HTTPException as StarletteHTTPException

from app import error_codes
from app.error_codes import ErrorCode
from app.exceptions import RateLimitedError
from app.http.api.error_handlers import api_exception_handler, api_fastapi_validation_handler, api_rate_limited_handler
from app.http.exceptions import BadRequestError
from tests.factories import RequestFactory, RequestScopeFactory


class TestExceptionHandler:
    async def test_exception_handler_with_json_request(self) -> None:
        exc = Exception("Test exception")
        request = RequestFactory(scope=RequestScopeFactory())
        response = await api_exception_handler(request, exc)
        assert response.status_code == 500
        assert response.headers.get("content-type") == "application/json"
        assert response.headers.get("x-error-code") == error_codes.SERVER_ERROR.code
        assert json.loads(response.body) == {
            "message": "Application error, please try again later.",
            "code": "server_error",
            "field_errors": {},
            "non_field_errors": [],
        }

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
    async def test_converts_starlette_status_code_to_error_code(self, status_code: int, error_code: ErrorCode) -> None:
        exc = StarletteHTTPException(status_code=status_code)
        request = RequestFactory(scope=RequestScopeFactory())
        response = await api_exception_handler(request, exc)
        assert response.status_code == status_code
        assert json.loads(response.body)["code"] == error_code

    async def test_handle_starlette_exception(self) -> None:
        exc = StarletteHTTPException(status_code=422)
        request = RequestFactory(scope=RequestScopeFactory())
        response = await api_exception_handler(request, exc)
        assert response.status_code == 422
        assert json.loads(response.body)["code"] == error_codes.VALIDATION_ERROR

    async def test_handle_fastapi_exception(self) -> None:
        exc = FastAPIHTTPException(status_code=422)
        request = RequestFactory(scope=RequestScopeFactory())
        response = await api_exception_handler(request, exc)
        assert response.status_code == 422
        assert json.loads(response.body)["code"] == error_codes.VALIDATION_ERROR

    async def test_handle_app_http_exception(self) -> None:
        exc = BadRequestError()
        request = RequestFactory(scope=RequestScopeFactory())
        response = await api_exception_handler(request, exc)
        assert response.status_code == 400
        assert json.loads(response.body)["code"] == error_codes.BAD_REQUEST


class TestFastAPIValidationErrorHandler:
    async def test_field_errors(self) -> None:
        class Dummy(pydantic.BaseModel):
            username: str = pydantic.Field("", min_length=3, max_length=10)

        with pytest.raises(pydantic.ValidationError) as exc:
            Dummy.model_validate({"username": "a"})

        request = RequestFactory(scope=RequestScopeFactory())
        response = await api_fastapi_validation_handler(request, exc.value)
        assert response.status_code == 422
        assert json.loads(response.body)["code"] == error_codes.VALIDATION_ERROR
        assert json.loads(response.body)["message"] == "Validation error."
        assert json.loads(response.body)["field_errors"]["username"] == ["String should have at least 3 characters"]

    async def test_non_field_errors(self) -> None:
        class Dummy(pydantic.BaseModel):
            username: str = pydantic.Field("", min_length=3, max_length=10)

        with pytest.raises(pydantic.ValidationError) as exc:
            Dummy.model_validate("blah")

        request = RequestFactory(scope=RequestScopeFactory())
        response = await api_fastapi_validation_handler(request, exc.value)
        assert response.status_code == 422
        assert json.loads(response.body)["code"] == error_codes.VALIDATION_ERROR
        assert json.loads(response.body)["message"] == "Validation error."
        assert json.loads(response.body)["non_field_errors"] == [
            "Input should be a valid dictionary or instance of Dummy"
        ]


async def test_rate_limited_error_handler() -> None:
    exc = RateLimitedError(
        limits.WindowStats(
            reset_time=10,
            remaining=1,
        )
    )
    request = RequestFactory(scope=RequestScopeFactory())
    response = await api_rate_limited_handler(request, exc)
    assert response.status_code == 429
    assert json.loads(response.body)["code"] == error_codes.RATE_LIMITED
    assert response.headers.get("Retry-After") == "10"
    assert response.headers.get("X-RateLimit-Remaining") == "1"
