import uuid
from unittest import mock

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app import error_codes
from app.contexts.billing.exceptions import (
    BillingError,
    DuplicateSubscriptionError,
    SubscriptionPlanError,
    SubscriptionRequiredError,
)
from app.contexts.billing.models import Subscription
from app.contexts.billing.stripe import (
    cancel_stripe_subscription,
    create_stripe_subscription,
    map_stripe_to_subscription_status,
    update_stripe_subscription,
)
from app.contexts.teams.models import Team
from tests.factories import SubscriptionFactory, SubscriptionPlanFactory
from tests.test_contexts.test_billing.factories import (
    StripePriceFactory,
    StripeSessionFactory,
    StripeSubscriptionFactory,
    StripeSubscriptionItemFactory,
    StripeSubscriptionItemListFactory,
)


@pytest.mark.parametrize(
    "stripe_status,expected",
    [
        ("active", Subscription.Status.ACTIVE),
        ("incomplete", Subscription.Status.UNPAID),
        ("incomplete_expired", Subscription.Status.UNPAID),
        ("past_due", Subscription.Status.PAST_DUE),
        ("canceled", Subscription.Status.CANCELLED),
        ("unpaid", Subscription.Status.UNPAID),
        ("trialing", Subscription.Status.TRIALING),
        ("paused", Subscription.Status.PAUSED),
        ("invalid", Subscription.Status.CANCELLED),
    ],
)
def test_map_stripe_to_subscription_status(stripe_status: str, expected: Subscription.Status) -> None:
    assert map_stripe_to_subscription_status(stripe_status) == expected


class TestCreateSubscription:
    async def test_create_stripe_subscription_ok(self, dbsession: AsyncSession, team: Team) -> None:
        subscription_id = f"sub_{uuid.uuid4().hex}"
        stripe_price = StripePriceFactory.make()
        subscription = StripeSubscriptionFactory.make(
            id=subscription_id,
            status="active",
            current_period_end=1620000000,
            items=StripeSubscriptionItemListFactory(
                data=[StripeSubscriptionItemFactory(price=stripe_price)],
            ),
        )
        stripe_session = StripeSessionFactory.make(
            client_reference_id=str(team.id),
            subscription=subscription.id,
        )
        _ = SubscriptionPlanFactory(remote_product_id=stripe_price.product)

        with mock.patch("app.contexts.billing.stripe.stripe.Subscription.retrieve_async", return_value=subscription):
            sub = await create_stripe_subscription(dbsession, stripe_session)
            assert sub.team_id == team.id
            assert sub.remote_subscription_id == subscription_id
            assert sub.status == Subscription.Status.ACTIVE
            assert sub.expires_at
            assert sub.expires_at.timestamp() == 1620000000
            assert sub.plan.remote_product_id == stripe_price.product
            assert sub.remote_price_id == stripe_price.id
            assert sub.remote_customer_id == subscription.customer

    async def test_create_stripe_subscription_no_db_plan(self, dbsession: AsyncSession, team: Team) -> None:
        subscription_id = f"sub_{uuid.uuid4().hex}"
        stripe_price = StripePriceFactory.make()
        subscription = StripeSubscriptionFactory.make(
            id=subscription_id,
            status="active",
            current_period_end=1620000000,
            items=StripeSubscriptionItemListFactory(
                data=[StripeSubscriptionItemFactory(price=stripe_price)],
            ),
        )
        stripe_session = StripeSessionFactory.make(
            client_reference_id=str(team.id),
            subscription=subscription.id,
        )

        with mock.patch("app.contexts.billing.stripe.stripe.Subscription.retrieve_async", return_value=subscription):
            with pytest.raises(SubscriptionPlanError) as ex:
                await create_stripe_subscription(dbsession, stripe_session)
                assert ex.value.error_code == error_codes.SUBSCRIPTION_MISSING_PLAN

    async def test_create_stripe_subscription_duplicate_subscription(self, dbsession: AsyncSession, team: Team) -> None:
        subscription_id = f"sub_{uuid.uuid4().hex}"
        stripe_price = StripePriceFactory.make()
        subscription = StripeSubscriptionFactory.make(
            id=subscription_id,
            status="active",
            current_period_end=1620000000,
            items=StripeSubscriptionItemListFactory(
                data=[StripeSubscriptionItemFactory(price=stripe_price)],
            ),
        )
        stripe_session = StripeSessionFactory.make(
            client_reference_id=str(team.id),
            subscription=subscription.id,
        )

        _ = SubscriptionFactory(team=team, remote_subscription_id=subscription_id)
        with mock.patch("app.contexts.billing.stripe.stripe.Subscription.retrieve_async", return_value=subscription):
            with pytest.raises(DuplicateSubscriptionError) as ex:
                await create_stripe_subscription(dbsession, stripe_session)
                assert ex.value.error_code == error_codes.SUBSCRIPTION_DUPLICATE

    async def test_create_stripe_subscription_without_sub_items(self, dbsession: AsyncSession, team: Team) -> None:
        subscription_id = f"sub_{uuid.uuid4().hex}"
        subscription = StripeSubscriptionFactory.make(
            id=subscription_id,
            status="active",
            current_period_end=1620000000,
            items=StripeSubscriptionItemListFactory(),
        )
        stripe_session = StripeSessionFactory.make(
            client_reference_id=str(team.id),
            subscription=subscription.id,
        )

        with mock.patch("app.contexts.billing.stripe.stripe.Subscription.retrieve_async", return_value=subscription):
            with pytest.raises(BillingError, match="Subscription has not items."):
                await create_stripe_subscription(dbsession, stripe_session)


class TestUpdateSubscription:
    async def test_update_stripe_subscription(self, dbsession: AsyncSession, team: Team) -> None:
        subscription_id = f"sub_{uuid.uuid4().hex}"
        stripe_price = StripePriceFactory.make()
        stripe_subscription = StripeSubscriptionFactory.make(
            id=subscription_id,
            status="past_due",
            current_period_end=1620000001,
            items=StripeSubscriptionItemListFactory(
                data=[StripeSubscriptionItemFactory(price=stripe_price)],
            ),
        )
        plan = SubscriptionPlanFactory(remote_product_id=stripe_price.product)
        _ = SubscriptionFactory(team=team, remote_subscription_id=subscription_id, plan=plan)

        with mock.patch(
            "app.contexts.billing.stripe.stripe.Subscription.retrieve_async", return_value=stripe_subscription
        ):
            sub = await update_stripe_subscription(dbsession, stripe_subscription)
            assert sub.team_id == team.id
            assert sub.remote_subscription_id == subscription_id
            assert sub.status == Subscription.Status.PAST_DUE
            assert sub.expires_at
            assert sub.expires_at.timestamp() == 1620000001
            assert sub.plan.remote_product_id == stripe_price.product
            assert sub.remote_price_id == stripe_price.id

    async def test_update_stripe_subscription_with_invalid_sub(self, dbsession: AsyncSession, team: Team) -> None:
        subscription_id = f"sub_{uuid.uuid4().hex}"
        stripe_price = StripePriceFactory.make()
        stripe_subscription = StripeSubscriptionFactory.make(
            id=subscription_id,
            status="past_due",
            current_period_end=1620000001,
            items=StripeSubscriptionItemListFactory(
                data=[StripeSubscriptionItemFactory(price=stripe_price)],
            ),
        )
        _ = SubscriptionPlanFactory(remote_product_id=stripe_price.product)

        with mock.patch(
            "app.contexts.billing.stripe.stripe.Subscription.retrieve_async", return_value=stripe_subscription
        ):
            with pytest.raises(SubscriptionRequiredError):
                await update_stripe_subscription(dbsession, stripe_subscription)

    async def test_update_stripe_subscription_with_missing_plan(self, dbsession: AsyncSession, team: Team) -> None:
        subscription_id = f"sub_{uuid.uuid4().hex}"
        stripe_price = StripePriceFactory.make()
        stripe_subscription = StripeSubscriptionFactory.make(
            id=subscription_id,
            status="past_due",
            current_period_end=1620000001,
            items=StripeSubscriptionItemListFactory(
                data=[StripeSubscriptionItemFactory(price=stripe_price)],
            ),
        )

        plan = SubscriptionPlanFactory(remote_product_id="invalid")
        _ = SubscriptionFactory(team=team, remote_subscription_id=subscription_id, plan=plan)
        with mock.patch(
            "app.contexts.billing.stripe.stripe.Subscription.retrieve_async", return_value=stripe_subscription
        ):
            with pytest.raises(SubscriptionPlanError):
                await update_stripe_subscription(dbsession, stripe_subscription)

    async def test_update_stripe_subscription_without_items(self, dbsession: AsyncSession, team: Team) -> None:
        subscription_id = f"sub_{uuid.uuid4().hex}"
        stripe_subscription = StripeSubscriptionFactory.make(
            id=subscription_id,
            status="past_due",
            current_period_end=1620000001,
            items=StripeSubscriptionItemListFactory(),
        )

        plan = SubscriptionPlanFactory(remote_product_id="invalid")
        _ = SubscriptionFactory(team=team, remote_subscription_id=subscription_id, plan=plan)
        with mock.patch(
            "app.contexts.billing.stripe.stripe.Subscription.retrieve_async", return_value=stripe_subscription
        ):
            with pytest.raises(BillingError, match="Subscription has not items."):
                await update_stripe_subscription(dbsession, stripe_subscription)

    async def test_update_stripe_subscription_cancellation(self, dbsession: AsyncSession, team: Team) -> None:
        subscription_id = f"sub_{uuid.uuid4().hex}"
        stripe_price = StripePriceFactory.make()
        stripe_subscription = StripeSubscriptionFactory.make(
            id=subscription_id,
            status="past_due",
            current_period_end=1620000002,
            cancel_at=1620000002,
            items=StripeSubscriptionItemListFactory(
                data=[StripeSubscriptionItemFactory(price=stripe_price)],
            ),
        )

        plan = SubscriptionPlanFactory(remote_product_id=stripe_price.product)
        _ = SubscriptionFactory(team=team, remote_subscription_id=subscription_id, plan=plan)
        with mock.patch(
            "app.contexts.billing.stripe.stripe.Subscription.retrieve_async", return_value=stripe_subscription
        ):
            sub = await update_stripe_subscription(dbsession, stripe_subscription)
            assert sub.status == Subscription.Status.CANCELLED
            assert sub.expires_at
            assert sub.expires_at.timestamp() == 1620000002


class TestCancelSubscription:
    async def test_cancel_stripe_subscription(
        self, dbsession: AsyncSession, dbsession_sync: Session, team: Team
    ) -> None:
        subscription_id = f"sub_{uuid.uuid4().hex}"
        stripe_price = StripePriceFactory.make()
        stripe_subscription = StripeSubscriptionFactory.make(
            id=subscription_id,
            status="past_due",
            current_period_end=1620000001,
            items=StripeSubscriptionItemListFactory(
                data=[StripeSubscriptionItemFactory(price=stripe_price)],
            ),
        )
        plan = SubscriptionPlanFactory(remote_product_id=stripe_price.product)
        _ = SubscriptionFactory(team=team, remote_subscription_id=subscription_id, plan=plan)

        with mock.patch(
            "app.contexts.billing.stripe.stripe.Subscription.retrieve_async", return_value=stripe_subscription
        ):
            await cancel_stripe_subscription(dbsession, stripe_subscription)
            await dbsession.commit()
            assert not dbsession_sync.scalars(
                sa.select(Subscription).where(Subscription.remote_subscription_id == subscription_id)
            ).one_or_none()

    async def test_cancel_stripe_subscription_missing_sub(
        self, dbsession: AsyncSession, dbsession_sync: Session, team: Team
    ) -> None:
        subscription_id = f"sub_{uuid.uuid4().hex}"
        stripe_price = StripePriceFactory.make()
        stripe_subscription = StripeSubscriptionFactory.make(
            id=subscription_id,
            status="past_due",
            current_period_end=1620000001,
            items=StripeSubscriptionItemListFactory(
                data=[StripeSubscriptionItemFactory(price=stripe_price)],
            ),
        )
        with mock.patch(
            "app.contexts.billing.stripe.stripe.Subscription.retrieve_async", return_value=stripe_subscription
        ):
            await cancel_stripe_subscription(dbsession, stripe_subscription)
            await dbsession.commit()
            assert not dbsession_sync.scalars(
                sa.select(Subscription).where(Subscription.remote_subscription_id == subscription_id)
            ).one_or_none()
