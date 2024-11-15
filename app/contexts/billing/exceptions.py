from app import error_codes
from app.exceptions import AppError


class BillingError(AppError):
    error_code = error_codes.BILLING_ERROR


class SubscriptionError(BillingError):
    error_code = error_codes.SUBSCRIPTION_ERROR


class SubscriptionRequiredError(SubscriptionError):
    error_code = error_codes.SUBSCRIPTION_REQUIRED


class DuplicateSubscriptionError(SubscriptionError):
    error_code = error_codes.SUBSCRIPTION_DUPLICATE


class SubscriptionPlanError(SubscriptionError):
    error_code = error_codes.SUBSCRIPTION_MISSING_PLAN
