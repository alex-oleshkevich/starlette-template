import pytest

from app.error_codes import SERVER_ERROR
from app.http.exceptions import HTTPException


def test_with_default_status_code() -> None:
    with pytest.raises(HTTPException) as ex:
        raise HTTPException()
    assert ex.value.status_code == 500


def test_with_user_status_code() -> None:
    with pytest.raises(HTTPException) as ex:
        raise HTTPException(status_code=400)
    assert ex.value.status_code == 400


def test_with_error_code_message() -> None:
    with pytest.raises(HTTPException) as ex:
        raise HTTPException()
    assert ex.value.detail == SERVER_ERROR.description


def test_with_user_message() -> None:
    with pytest.raises(HTTPException) as ex:
        raise HTTPException(message="Custom message")
    assert ex.value.detail == "Custom message"
