import dataclasses

from starlette_babel import gettext_lazy as _


@dataclasses.dataclass
class ErrorCode:
    code: str
    description: str


SERVER_ERROR = ErrorCode("server_error", _("Application error, please try again later."))
AUTH_INVALID_CREDENTIALS = ErrorCode("auth.invalid_credentials", _("Invalid email or password."))
AUTH_ACCOUNT_DISABLED = ErrorCode("auth.account_disabled", _("This account is deactivated."))
BILLING_ERROR = ErrorCode("billing.error", _("Billing error."))
SUBSCRIPTION_ERROR = ErrorCode("subscription.error", _("Subscription error."))
SUBSCRIPTION_REQUIRED = ErrorCode("subscription.required", _("Subscription is required."))
SUBSCRIPTION_DUPLICATE = ErrorCode("subscription.duplicate", _("A subscription is already active."))
SUBSCRIPTION_MISSING_PLAN = ErrorCode("subscription.plan", _("Invalid or missing subscription plan."))
RATE_LIMITED = ErrorCode("rate_limited", _("Too many requests."))
