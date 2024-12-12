from app import error_codes
from app.exceptions import AppError


class AuthenticationError(AppError):
    pass


class InvalidCredentialsError(AuthenticationError):
    error_code = error_codes.AUTH_INVALID_CREDENTIALS


class UserDisabledError(AuthenticationError):
    error_code = error_codes.AUTH_ACCOUNT_DISABLED


class UserNotRegisteredError(InvalidCredentialsError): ...


class TokenError(AuthenticationError): ...
