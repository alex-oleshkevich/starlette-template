import pytest

from app.error_codes import ErrorCode
from app.exceptions import AppError


def test_apperror() -> None:
    with pytest.raises(AppError, match=""):
        raise AppError


def test_apperror_with_message() -> None:
    with pytest.raises(AppError, match="error"):
        raise AppError("error")


def test_apperror_with_error_code_message() -> None:
    code = ErrorCode("unknown_error", "Unknown error")
    with pytest.raises(AppError, match="Unknown error"):
        raise AppError(error_code=code)


def test_apperror_with_message_overrides_error_code() -> None:
    code = ErrorCode("unknown_error", "Unknown error")
    with pytest.raises(AppError, match="custom error"):
        raise AppError("custom error", error_code=code)


def test_apperror_with_message_from_attr() -> None:
    class Error(AppError):
        message = "Custom error"

    with pytest.raises(AppError, match="Custom error"):
        raise Error


def test_apperror_message_from_attr_error_code() -> None:
    class Error(AppError):
        error_code = ErrorCode("unknown_error", "Unknown error")

    with pytest.raises(AppError, match="Unknown error") as ex:
        raise Error
    assert ex.value.error_code == ErrorCode("unknown_error", "Unknown error")


def test_apperror_with_attr_code_override_attr_message() -> None:
    class Error(AppError):
        message = "Custom error"
        error_code = ErrorCode("unknown_error", "Code error")

    with pytest.raises(AppError, match="Code error"):
        raise Error
