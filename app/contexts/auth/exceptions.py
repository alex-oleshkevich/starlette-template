from app.error_codes import AUTH_ACCOUNT_DISABLED, AUTH_INVALID_CREDENTIALS
from app.exceptions import AppError


class AuthenticationError(AppError):
    pass


class InvalidCredentialsError(AuthenticationError):
    error_code = AUTH_INVALID_CREDENTIALS


class UserDisabledError(AuthenticationError):
    error_code = AUTH_ACCOUNT_DISABLED


class UserNotRegisteredError(InvalidCredentialsError): ...
