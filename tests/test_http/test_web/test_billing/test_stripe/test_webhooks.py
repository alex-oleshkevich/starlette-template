import json
import time
import uuid
from unittest import mock

import sqlalchemy as sa
import stripe
from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from app import error_codes
from app.config.settings import Config
from app.contexts.billing.models import Subscription
from app.contexts.teams.models import Team
from tests.factories import SubscriptionFactory, SubscriptionPlanFactory
from tests.test_contexts.test_billing.factories import (
    StripeEventFactory,
    StripePriceFactory,
    StripeSessionFactory,
    StripeSubscriptionFactory,
    StripeSubscriptionItemFactory,
    StripeSubscriptionItemListFactory,
)


class SignatureMaker(stripe.WebhookSignature):
    @classmethod
    def make_signature(cls, payload: str, secret: str) -> str:
        timestamp = int(time.time())
        signed_payload = f"{timestamp}.{payload}"
        signature = cls._compute_signature(signed_payload, secret)  # type: ignore[no-untyped-call]
        return f"t={timestamp},v1={signature}"


def test_stripe_signature(settings: Config) -> None:
    payload = json.dumps({"foo": "bar"})
    header = SignatureMaker.make_signature(payload, settings.stripe_webhook_secret)
    assert stripe.WebhookSignature.verify_header(payload, header, settings.stripe_webhook_secret)  # type: ignore[no-untyped-call]


def test_create_subscription(team: Team, client: TestClient, dbsession_sync: Session, settings: Config) -> None:
    subscription_id = f"sub_{uuid.uuid4().hex}"
    stripe_price = StripePriceFactory.make()
    stripe_subscription = StripeSubscriptionFactory.make(
        id=subscription_id,
        status="active",
        current_period_end=1620000000,
        items=StripeSubscriptionItemListFactory(
            data=[StripeSubscriptionItemFactory(price=stripe_price)],
        ),
    )
    event_data = StripeEventFactory(
        type="checkout.session.completed",
        data={
            "object": StripeSessionFactory(
                subscription=stripe_subscription.id,
                client_reference_id=str(team.id),
            ),
        },
    )
    _ = SubscriptionPlanFactory(remote_product_id=stripe_price.product)
    with mock.patch("app.contexts.billing.stripe.stripe.Subscription.retrieve_async", return_value=stripe_subscription):
        payload = json.dumps(event_data)
        response = client.post(
            "/stripe/webhook",
            content=payload,
            headers={
                "Stripe-Signature": SignatureMaker.make_signature(payload, settings.stripe_webhook_secret),
            },
        )
        assert response.status_code == 200

    subscription = (
        dbsession_sync.execute(sa.select(Subscription).where(Subscription.team_id == team.id)).scalars().one()
    )
    assert subscription.status == Subscription.Status.ACTIVE


def test_update_subscription(team: Team, client: TestClient, dbsession_sync: Session, settings: Config) -> None:
    subscription_id = f"sub_{uuid.uuid4().hex}"
    stripe_price = StripePriceFactory.make()
    stripe_subscription = StripeSubscriptionFactory.make(
        id=subscription_id,
        status="trialing",
        current_period_end=1620000000,
        items=StripeSubscriptionItemListFactory(
            data=[StripeSubscriptionItemFactory(price=stripe_price)],
        ),
    )
    event_data = StripeEventFactory(
        type="customer.subscription.updated",
        data={"object": stripe_subscription},
    )
    subscription_plan = SubscriptionPlanFactory(remote_product_id=stripe_price.product)
    _ = SubscriptionFactory(team=team, remote_subscription_id=subscription_id, plan=subscription_plan)
    with mock.patch("app.contexts.billing.stripe.stripe.Subscription.retrieve_async", return_value=stripe_subscription):
        payload = json.dumps(event_data)
        response = client.post(
            "/stripe/webhook",
            content=payload,
            headers={
                "Stripe-Signature": SignatureMaker.make_signature(payload, settings.stripe_webhook_secret),
            },
        )
        assert response.status_code == 200

    subscription = (
        dbsession_sync.execute(sa.select(Subscription).where(Subscription.team_id == team.id)).scalars().one()
    )
    assert subscription.status == Subscription.Status.TRIALING


def test_delete_subscription(team: Team, client: TestClient, dbsession_sync: Session, settings: Config) -> None:
    subscription_id = f"sub_{uuid.uuid4().hex}"
    stripe_price = StripePriceFactory.make()
    stripe_subscription = StripeSubscriptionFactory.make(
        id=subscription_id,
        status="trialing",
        current_period_end=1620000000,
        items=StripeSubscriptionItemListFactory(
            data=[StripeSubscriptionItemFactory(price=stripe_price)],
        ),
    )
    event_data = StripeEventFactory(
        type="customer.subscription.deleted",
        data={"object": stripe_subscription},
    )
    subscription_plan = SubscriptionPlanFactory(remote_product_id=stripe_price.product)
    _ = SubscriptionFactory(team=team, remote_subscription_id=subscription_id, plan=subscription_plan)
    with mock.patch("app.contexts.billing.stripe.stripe.Subscription.retrieve_async", return_value=stripe_subscription):
        payload = json.dumps(event_data)
        response = client.post(
            "/stripe/webhook",
            content=payload,
            headers={
                "Stripe-Signature": SignatureMaker.make_signature(payload, settings.stripe_webhook_secret),
            },
        )
        assert response.status_code == 200

    assert not (dbsession_sync.scalars(sa.select(Subscription).where(Subscription.team_id == team.id)).one_or_none())


def test_raises_billing_error(team: Team, client: TestClient, dbsession_sync: Session, settings: Config) -> None:
    subscription_id = f"sub_{uuid.uuid4().hex}"
    stripe_price = StripePriceFactory.make()
    stripe_subscription = StripeSubscriptionFactory.make(
        id=subscription_id,
        status="trialing",
        current_period_end=1620000000,
        items=StripeSubscriptionItemListFactory(
            data=[StripeSubscriptionItemFactory(price=stripe_price)],
        ),
    )
    event_data = StripeEventFactory(
        type="customer.subscription.updated",
        data={"object": stripe_subscription},
    )
    with mock.patch("app.contexts.billing.stripe.stripe.Subscription.retrieve_async", return_value=stripe_subscription):
        payload = json.dumps(event_data)
        response = client.post(
            "/stripe/webhook",
            content=payload,
            headers={
                "Stripe-Signature": SignatureMaker.make_signature(payload, settings.stripe_webhook_secret),
            },
        )
        assert response.status_code == 400
        assert error_codes.SUBSCRIPTION_REQUIRED.code in response.text
