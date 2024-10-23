from starlette_babel import gettext_lazy as _

from app.error_codes import ErrorCode
from app.exceptions import AppError


class RegisterError(AppError): ...


class InvalidVerificationTokenError(RegisterError):
    error_code = ErrorCode("register.invalid_token", _("Verification token invalid or expired."))
