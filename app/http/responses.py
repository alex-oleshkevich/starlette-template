import typing

from pydantic import BaseModel
from starlette.background import BackgroundTask
from starlette.responses import JSONResponse

from app.error_codes import SERVER_ERROR, ErrorCode


class ErrorSchema(BaseModel):
    code: str
    message: str
    field_errors: dict[str, list[str]]
    non_field_errors: list[str]


class JSONErrorResponse(JSONResponse):
    """A specialized JSON response for error responses.
    Use this class to return error responses with a consistent structure."""

    def __init__(
        self,
        message: str = "",
        status_code: int = 500,
        *,
        field_errors: dict[str, list[str]] | None = None,
        non_field_errors: list[str] | None = None,
        error_code: ErrorCode = SERVER_ERROR,
        headers: typing.Mapping[str, str] | None = None,
        background: BackgroundTask | None = None,
    ) -> None:
        message_code = error_code.code
        final_message = message or error_code.description
        non_field_errors = [str(x) for x in non_field_errors or []]
        field_errors = {field: [str(x) for x in errors] for field, errors in (field_errors or {}).items()}

        schema = ErrorSchema(
            code=message_code,
            message=str(final_message),
            field_errors=field_errors,
            non_field_errors=non_field_errors,
        )
        super().__init__(
            schema.model_dump(),
            status_code=status_code,
            headers=headers,
            background=background,
        )
