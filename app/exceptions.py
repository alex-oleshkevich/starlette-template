import limits

from app import error_codes
from app.error_codes import ErrorCode


class AppError(Exception):
    """Base class for all exceptions in the application.

    Message precedence:
    1. message argument
    2. error_code.description
    3. self.message
    """

    error_code: ErrorCode | None = None
    message: str | None = None

    def __init__(
        self,
        message: str | None = None,
        *,
        error_code: ErrorCode | None = None,
    ) -> None:
        error_code = error_code or self.error_code
        error_message = error_code.description if error_code else ""
        self.message = str(message or error_message or self.message)
        self.error_code = error_code
        super().__init__(self.message)


class RateLimitedError(AppError):
    error_code = error_codes.RATE_LIMITED

    def __init__(self, stats: limits.WindowStats) -> None:
        super().__init__()
        self.stats = stats
