import logging

from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.error_codes import SERVER_ERROR, ErrorCode
from app.exceptions import AppError

logger = logging.getLogger(__name__)


class ErrorResponse(JSONResponse):
    def __init__(
        self,
        message: str = "",
        status_code: int = 500,
        *,
        field_errors: dict[str, list[str]] | None = None,
        non_field_errors: list[str] | None = None,
        error_code: ErrorCode = SERVER_ERROR,
    ) -> None:
        message_code = error_code.code
        final_message = message or error_code.description
        non_field_errors = [str(x) for x in non_field_errors or []]
        field_errors = {field: [str(x) for x in errors] for field, errors in (field_errors or {}).items()}

        super().__init__(
            {
                "code": message_code,
                "message": str(final_message),
                "field_errors": field_errors,
                "non_field_errors": non_field_errors,
            },
            status_code=status_code,
        )


def on_app_error(request: Request, exc: AppError) -> Response:
    logger.error(f"app error: {exc}", exc_info=exc)
    if request.app.debug:
        raise exc

    if "application/json" in request.headers.get("accept", ""):
        return ErrorResponse(message=str(exc), status_code=500, error_code=exc.error_code or SERVER_ERROR)
    raise exc
