from app.error_codes import ACCOUNT_DISABLED, INVALID_CREDENTIALS
from app.exceptions import AppError


class AuthenticationError(AppError):
    pass


class InvalidCredentialsError(AuthenticationError):
    error_code = INVALID_CREDENTIALS


class UserDisabledError(AuthenticationError):
    error_code = ACCOUNT_DISABLED
