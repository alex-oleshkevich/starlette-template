import dataclasses

from starlette_babel import gettext_lazy as _


@dataclasses.dataclass(slots=True, frozen=True)
class ErrorCode:
    code: str
    description: str

    def __str__(self) -> str:
        return str(self.description)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, str):
            return other == self.code
        if not isinstance(other, ErrorCode):
            return NotImplemented
        return self.code == other.code


# Please keep the error codes sorted alphabetically
AUTH_UNAUTHENTICATED = ErrorCode("auth.unauthenticated", _("Unauthenticated."))
BAD_REQUEST = ErrorCode("bad_request", _("Bad request. Please check your input."))
PERMISSION_DENIED = ErrorCode("access.denied", _("You do not have permission to access this resource."))
RATE_LIMITED = ErrorCode("rate_limited", _("Too many requests."))
RESOURCE_CONFLICT = ErrorCode("resource_conflict", _("This object already exists."))
RESOURCE_NOT_FOUND = ErrorCode("resource.not_found", _("Requested resource does not exist."))
SERVER_ERROR = ErrorCode("server_error", _("Application error, please try again later."))
VALIDATION_ERROR = ErrorCode("validation_error", _("Invalid data. Please check your input."))

AUTH_ACCOUNT_DISABLED = ErrorCode("auth.account_disabled", _("This account is deactivated."))
AUTH_INVALID_CREDENTIALS = ErrorCode("auth.invalid_credentials", _("Invalid email or password."))
AUTH_INVALID_ACCESS_TOKEN = ErrorCode("auth.invalid_access_token", _("Invalid access token."))
AUTH_INVALID_REFRESH_TOKEN = ErrorCode("auth.invalid_refresh_token", _("Invalid refresh token."))
BILLING_ERROR = ErrorCode("billing.error", _("Billing error."))
SUBSCRIPTION_DUPLICATE = ErrorCode("subscription.duplicate", _("A subscription is already active."))
SUBSCRIPTION_ERROR = ErrorCode("subscription.error", _("Subscription error."))
SUBSCRIPTION_MISSING_PLAN = ErrorCode("subscription.plan", _("Invalid or missing subscription plan."))
SUBSCRIPTION_REQUIRED = ErrorCode("subscription.required", _("Subscription is required."))
