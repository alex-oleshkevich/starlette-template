"""Factories in this module are neither complete nor accurate.
They are used to generate fake real-like data for testing purposes only.
They may miss some fields or have incorrect types. Please be careful.

Reference https://docs.stripe.com/api
"""

import time
import typing
import uuid

import factory
import stripe


class StripeAutomaticTaxLiabilityFactory(factory.DictFactory):
    account: str | None = None
    type: typing.Literal["account", "self"] = "self"


class StripeAutomaticTaxFactory(factory.DictFactory):
    enabled: bool = False
    status: typing.Literal["complete", "failed", "requires_location_inputs"] = "complete"
    liability: dict[str, typing.Any] | None = factory.SubFactory(StripeAutomaticTaxLiabilityFactory)


class CustomerAddressFactory(factory.DictFactory):
    city: str | None = None
    country: str | None = None
    line1: str | None = None
    line2: str | None = None
    postal_code: str | None = None
    state: str | None = None


class StripeCustomerFactory(factory.DictFactory):
    id: str = factory.LazyFunction(lambda: f"cus_{int(time.time())}")
    address: dict[str, typing.Any] = factory.SubFactory(CustomerAddressFactory)
    name: str | None = None
    phone: str | None = None
    tax_exempt: typing.Literal["none"] = "none"
    tax_ids: list[dict[str, typing.Any]] = factory.LazyFunction(list)


class StripeConsentCollectionFactory(factory.DictFactory):
    payment_method_reuse_agreement: typing.Any | None = None
    promotions: typing.Any | None = None
    terms_of_service: typing.Any | None = None


class StripeSessionCustomTextFactory(factory.DictFactory):
    after_submit: str | None = None
    shipping_address: str | None = None
    submit: str | None = None
    terms_of_service_acceptance: str | None = None


class StripeSessionFactory(factory.DictFactory):
    """See https://docs.stripe.com/api/checkout/sessions/object"""

    _customer = factory.SubFactory(StripeCustomerFactory)

    id: str = factory.LazyFunction(lambda: f"cs_{int(time.time())}")
    object: typing.Literal["checkout.session"] = "checkout.session"
    adaptive_pricing: typing.Any | None = None
    after_expiration: typing.Any | None = None
    allow_promotion_codes: bool = True
    amount_subtotal: int = 20000
    amount_total: int = 20000
    automatic_tax: typing.Any | None = factory.SubFactory(StripeAutomaticTaxFactory)
    billing_address_collection: typing.Literal["auto"] = "auto"
    cancel_url: str = "https://example.com/cancel"
    client_reference_id: str | None = None
    client_secret: str | None = None
    consent: typing.Any | None = None
    consent_collection: dict[str, typing.Any] = factory.SubFactory(StripeConsentCollectionFactory)
    created: int = factory.LazyFunction(lambda: int(time.time()))
    currency: typing.Literal["usd"] | None = "usd"
    currency_conversion: typing.Any | None = None
    custom_fields: list[typing.Any] = factory.LazyFunction(list)
    custom_text: dict[str, typing.Any] = factory.SubFactory(StripeSessionCustomTextFactory)
    customer: str = factory.LazyAttribute(lambda self: self._customer["id"])
    customer_creation: typing.Literal["always"] = "always"
    customer_details: dict[str, typing.Any] = factory.SelfAttribute("_customer")
    customer_email: str | None = None
    expires_at: int | None = None
    invoice: str = factory.LazyFunction(lambda: StripeInvoiceFactory()["id"])
    invoice_creation: typing.Any | None = None
    live_mode: bool = False
    locale: typing.Literal["en"] = "en"
    metadata: dict[str, typing.Any] = factory.LazyFunction(dict)
    mode: typing.Literal["subscription", "payment", "setup"] = "subscription"
    payment_intent: str | None = None
    payment_method_options: dict[str, typing.Any] = factory.LazyFunction(dict)
    payment_method_types: list[str] = factory.LazyFunction(list)
    payment_status: typing.Literal["paid"] = "paid"
    setup_intent: str | None = None
    status: typing.Literal["complete"] = "complete"
    shipping: typing.Any | None = None
    shipping_address_collection: typing.Literal["auto"] = "auto"
    submit_type: typing.Literal["auto"] = "auto"
    subscription: str = factory.LazyFunction(lambda: StripeSubscriptionFactory()["id"])
    success_url: str = "https://example.com/success"
    total_details: dict[str, typing.Any] = factory.LazyFunction(dict)
    url: str = "https://example.com/checkout"

    @classmethod
    def make(cls, **kwargs: typing.Any) -> stripe.checkout.Session:
        return stripe.checkout.Session.construct_from(cls(**kwargs), "")


class StripeCancellationDetailsFactory(factory.DictFactory):
    comment: str | None = None
    feedback: str | None = None
    reason: str | None = None


class StripePaymentMethodFactory(factory.DictFactory):
    id: str = factory.LazyFunction(lambda: f"pm_{int(time.time())}")


class StripeInvoiceCustomerBalanceSettingsFactory(factory.DictFactory):
    consume_applied_balance_on_void: bool = True


class StripeInvoiceSettingsFactory(factory.DictFactory):
    account_tax_ids: None
    issuer: dict[str, str] = factory.LazyFunction(lambda: {"type": "self"})


class StripeProductFactory(factory.DictFactory):
    id: str = factory.LazyFunction(lambda: f"pr_{uuid.uuid4().hex}")


class StripeInvoiceFactory(factory.DictFactory):
    id: str = factory.LazyFunction(lambda: f"in_{int(time.time())}")


class StripePlanFactory(factory.DictFactory):
    id: str = factory.LazyFunction(lambda: f"plan_{int(time.time())}")
    object: typing.Literal["plan"] = "plan"
    active: bool = True
    aggregate_usage: str | None = None
    amount: int = 20000
    amount_decimal: str = "20000"
    billing_scheme: str = "per_unit"
    created: int = factory.LazyFunction(lambda: int(time.time()))
    currency: typing.Literal["usd"] = "usd"
    interval: typing.Literal["month"] = "month"
    interval_count: int = 1
    livemode: bool = True
    metadata: dict[str, typing.Any] = factory.LazyFunction(dict)
    meter: str | None = None
    nickname: str | None = None
    product: str = factory.LazyFunction(lambda: StripeProductFactory()["id"])
    tiers: typing.Any = None
    tiers_mode: str | None = None
    transform_usage: str | None = None
    trial_period_days: int | None = None
    usage_type: typing.Literal["licensed"] = "licensed"

    @classmethod
    def make(cls, **kwargs: typing.Any) -> stripe.Plan:
        return stripe.Plan.construct_from(cls(**kwargs), "")


class StripePriceFactory(factory.DictFactory):
    id: str = factory.LazyFunction(lambda: f"price_{int(time.time())}")
    object: typing.Literal["price"] = "price"
    active: bool = True
    aggregate_usage: str | None = None
    amount: int = 20000
    amount_decimal: str = "20000"
    billing_scheme: str = "per_unit"
    created: int = factory.LazyFunction(lambda: int(time.time()))
    currency: typing.Literal["usd"] = "usd"
    interval: typing.Literal["month"] = "month"
    interval_count: int = 1
    livemode: bool = True
    metadata: dict[str, typing.Any] = factory.LazyFunction(dict)
    nickname: str | None = None
    product: str = factory.LazyFunction(lambda: StripeProductFactory()["id"])
    tiers: typing.Any = None
    tiers_mode: str | None = None
    transform_usage: str | None = None
    trial_period_days: int | None = None
    usage_type: typing.Literal["licensed"] = "licensed"

    @classmethod
    def make(cls, **kwargs: typing.Any) -> stripe.Price:
        return stripe.Price.construct_from(cls(**kwargs), "")


class StripeSubscriptionItemFactory(factory.DictFactory):
    id: str = factory.LazyFunction(lambda: f"si_{int(time.time())}")
    object: typing.Literal["subscription_item"] = "subscription_item"
    billing_thresholds: typing.Any | None = None
    created: int = factory.LazyFunction(lambda: int(time.time()))
    discounts: list[dict[str, typing.Any]] = factory.LazyFunction(list)
    metadata: dict[str, typing.Any] = factory.LazyFunction(dict)
    plan: dict[str, typing.Any] = factory.SubFactory(StripePriceFactory)
    price: dict[str, typing.Any] = factory.SubFactory(StripePriceFactory)
    quantity: int = 1
    subscription: str = factory.LazyFunction(lambda: StripeSubscriptionFactory()["id"])
    tax_rates: list[dict[str, typing.Any]] = factory.LazyFunction(list)


class StripeSubscriptionItemListFactory(factory.DictFactory):
    object: typing.Literal["subscription_item"] = "subscription_item"
    data: list[dict[str, typing.Any]] = factory.LazyFunction(list)
    has_more: bool = False
    total_count: int = 1
    url: str = "/v1/subscription_items?subscription=sub_1QKOZMKUxmARjXK3b5qId0su"


class StripePaymentMethodOptionsFactory(factory.DictFactory):
    acss_debit: typing.Any = None
    bancontact: typing.Any = None
    card: dict[str, typing.Any] = factory.LazyFunction(lambda: {"network": None, "request_three_d_secure": "automatic"})
    customer_balance: typing.Any = None
    konbini: typing.Any = None
    sepa_debit: typing.Any = None
    us_bank_account: typing.Any = None


class StripePaymentMethodSettingsFactory(factory.DictFactory):
    payment_method_type: typing.Any = None
    save_default_payment_method: str = "off"
    payment_method_options: dict[str, typing.Any] = factory.SubFactory(StripePaymentMethodOptionsFactory)


class StripeSubscriptionTrialSettingsFactory(factory.DictFactory):
    end_behavior: dict[str, str] = factory.LazyFunction(lambda: {"missing_payment_method": "create_invoice"})


class StripeSubscriptionFactory(factory.DictFactory):
    application: str | None = None
    application_fee_percent: float | None = None
    automatic_tax: dict[str, typing.Any] = factory.SubFactory(StripeAutomaticTaxFactory)
    billing: typing.Literal["charge_automatically"] = "charge_automatically"
    billing_cycle_anchor: int = 1731435124
    billing_cycle_anchor_config: dict[str, typing.Any] | None = None
    billing_thresholds: dict[str, typing.Any] | None = None
    cancel_at: int | None = None
    cancel_at_period_end: int | None = False
    canceled_at: int | None = None
    cancellation_details: dict[str, typing.Any] = factory.SubFactory(StripeCancellationDetailsFactory)
    collection_method: typing.Literal["charge_automatically"] = "charge_automatically"
    created: int = factory.LazyFunction(lambda: int(time.time()))
    currency: typing.Literal["usd"] = "usd"
    current_period_end: int = 1734027124
    current_period_start: int = 1731435124
    customer: str = factory.LazyFunction(lambda: StripeCustomerFactory()["id"])
    days_until_due: int | None = None
    default_payment_method: str = factory.LazyFunction(lambda: StripePaymentMethodFactory()["id"])
    default_source: typing.Any | None = None
    default_tax_rates: list[typing.Any] = factory.LazyFunction(list)
    description: str | None = None
    discount: typing.Any | str = None
    discounts: list[typing.Any] = factory.LazyFunction(list)
    ended_at: int | None = None
    id: str = factory.LazyFunction(lambda: f"sub_{int(time.time())}")
    invoice_customer_balance_settings: dict[str, typing.Any] = factory.SubFactory(
        StripeInvoiceCustomerBalanceSettingsFactory
    )
    invoice_settings: dict[str, typing.Any] = factory.SubFactory(StripeInvoiceSettingsFactory)
    items: dict[str, typing.Any] = factory.SubFactory(StripeSubscriptionItemListFactory)
    latest_invoice: str = factory.LazyFunction(lambda: StripeInvoiceFactory()["id"])
    livemode: bool = False
    metadata: dict[str, typing.Any] = factory.LazyFunction(dict)
    next_pending_invoice_item_invoice: typing.Any = None
    object: typing.Literal["subscription"] = "subscription"
    on_behalf_of: typing.Any | None = None
    pause_collection: typing.Any | None = None
    payment_settings: dict[str, typing.Any] = factory.SubFactory(StripePaymentMethodSettingsFactory)
    pending_invoice_item_interval: typing.Any | None = None
    pending_setup_intent: typing.Any | None = None
    pending_update: typing.Any | None = None
    plan: dict[str, typing.Any] = factory.SubFactory(StripePlanFactory)
    quantity: int = 1
    schedule: typing.Any | None = None
    start: int = 1731436408
    start_date: int = 1731435124
    status: typing.Literal["active"] = "active"
    tax_percent: float | None = None
    test_clock: int | None = None
    transfer_data: typing.Any | None = None
    trial_end: int | None = None
    trial_settings: dict[str, typing.Any] = factory.SubFactory(StripeSubscriptionTrialSettingsFactory)
    trial_start: int | None = None

    @classmethod
    def make(cls, **kwargs: typing.Any) -> stripe.Subscription:
        return stripe.Subscription.construct_from(cls(**kwargs), "")


class StripeEventFactory(factory.DictFactory):
    api_version: str = "2019-09-09"
    id: str = factory.LazyAttribute(lambda self: f"evt_{self.created}")
    created: int = factory.LazyFunction(lambda: int(time.time()))
    data: dict[str, typing.Any] = factory.LazyFunction(lambda: {"object": StripeSessionFactory()})
    type: str = "checkout.session.completed"
    livemode: bool = True
    object: typing.Literal["event"] = "event"
    pending_webhooks: int = 0
    account: str | None = None
    request: dict[str, typing.Any] = factory.LazyFunction(lambda: {"id": None, "idempotency_key": None})
