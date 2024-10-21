import dataclasses

from starlette_babel import gettext_lazy as _


@dataclasses.dataclass
class ErrorCode:
    code: str
    description: str


RATE_LIMITED = ErrorCode("rate_limited", _("Too many requests."))

# auth
INVALID_CREDENTIALS = ErrorCode("auth.invalid_credentials", _("Invalid email or password."))
ACCOUNT_DISABLED = ErrorCode("auth.account_disabled", _("This account is deactivated."))
