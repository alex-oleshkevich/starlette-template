import datetime
import logging
import typing

import click
import stripe
from sqlalchemy.ext.asyncio import AsyncSession
from starlette_babel import gettext_lazy as _

from app.config.settings import settings
from app.contexts.billing.exceptions import (
    BillingError,
    DuplicateSubscriptionError,
    SubscriptionPlanError,
    SubscriptionRequiredError,
)
from app.contexts.billing.models import Subscription, SubscriptionMetadata, SubscriptionPlan
from app.contexts.billing.repo import SubscriptionRepo
from app.contexts.teams.repo import TeamRepo

logger = logging.getLogger(__name__)


async def sync_stripe_products(dbsession: AsyncSession) -> None:
    repo = SubscriptionRepo(dbsession)
    our_plans = await repo.plans.all()
    our_plans_by_remote_id = {plan.remote_product_id: plan for plan in our_plans}
    our_plans_by_name = {plan.name: plan for plan in our_plans}
    products = await stripe.Product.list_async(active=True, type="service", api_key=settings.stripe_secret_key)
    for product in products:
        if product.id in our_plans_by_remote_id:
            click.echo(f'Product "{product.id}" is synced.')
            continue

        if product.name not in our_plans_by_name:
            subscription_plan = SubscriptionPlan(name=product.name, remote_product_id=product.id)
            dbsession.add(subscription_plan)
            click.echo(f'Product "{product.name}" has been added.')
            continue

        if click.confirm(
            f'Product "{product.name}", id={product.id} does not exist in the database, '
            f"but a product with the same name exists. Do you want to associate them?",
        ):
            our_plans_by_name[product.name].remote_product_id = product.id
            click.echo("  -> product has been associated.")

        click.secho(f'  -> product "{product.name}", id={product.id} skipped', fg="red")

    await dbsession.commit()


StripeStatus = typing.Literal[
    "active",
    "incomplete",
    "incomplete_expired",
    "past_due",
    "canceled",
    "unpaid",
    "trialing",
    "paused",
]


def map_stripe_to_subscription_status(stripe_status: str) -> Subscription.Status:  # noqa: PLR0911
    if stripe_status == "active":
        return Subscription.Status.ACTIVE
    if stripe_status == "incomplete":
        return Subscription.Status.UNPAID
    if stripe_status == "incomplete_expired":
        return Subscription.Status.UNPAID
    if stripe_status == "past_due":
        return Subscription.Status.PAST_DUE
    if stripe_status == "canceled":
        return Subscription.Status.CANCELLED
    if stripe_status == "unpaid":
        return Subscription.Status.UNPAID
    if stripe_status == "trialing":
        return Subscription.Status.TRIALING
    if stripe_status == "paused":
        return Subscription.Status.PAUSED
    return Subscription.Status.CANCELLED


async def create_stripe_subscription(dbsession: AsyncSession, stripe_session: stripe.checkout.Session) -> Subscription:
    """
    Create a subscription in the database based on the stripe checkout session.
    Notes:
        1. We will raise an error if the subscription already exists.
        Typically, this should not happen if database is in sync with Stripe.
        You can handle this by limiting the number of subscriptions per user on Stripe's side.

        2. We will raise an error if the plan does not exist in the database.
        Similar to the previous point, this should not happen if the database is in sync with Stripe.
        Automatic plan provisioning can lead to unexpected behavior depending on price and billing strategy.
    """
    repo = SubscriptionRepo(dbsession)
    if not isinstance(stripe_session.subscription, str):
        raise BillingError(_("Stripe session does not have a subscription."))

    if not stripe_session.client_reference_id:
        raise BillingError(_("Client reference id is missing."))

    stripe_subscription = await stripe.Subscription.retrieve_async(
        stripe_session.subscription, api_key=settings.stripe_secret_key
    )
    subscription = await repo.get_subscription_by_remote_id(stripe_subscription.id)
    if subscription is not None:
        raise DuplicateSubscriptionError()

    team_id = int(stripe_session.client_reference_id or 0)
    team_repo = TeamRepo(dbsession)
    team = await team_repo.get(team_id)
    try:
        stripe_price = stripe_subscription["items"].data[0].price
    except IndexError:
        raise BillingError(_("Subscription has not items."))

    plan = await repo.get_plan_by_remote_id(stripe_price.product)
    if plan is None:
        raise SubscriptionPlanError()

    stripe_period_end = stripe_subscription.current_period_end  # timestamp
    subscription = Subscription(
        team=team,
        plan=plan,
        status=map_stripe_to_subscription_status(stripe_subscription.status),
        created_at=datetime.datetime.now(datetime.UTC),
        expires_at=datetime.datetime.fromtimestamp(stripe_period_end, tz=datetime.UTC),
        remote_customer_id=stripe_subscription.customer,
        remote_subscription_id=stripe_subscription.id,
        remote_price_id=stripe_price.id,
        meta=SubscriptionMetadata(),
    )
    dbsession.add(subscription)
    await dbsession.flush()
    return subscription


async def update_stripe_subscription(dbsession: AsyncSession, stripe_subscription: stripe.Subscription) -> Subscription:
    repo = SubscriptionRepo(dbsession)
    subscription = await repo.get_subscription_by_remote_id(stripe_subscription.id)
    if subscription is None:
        raise SubscriptionRequiredError()

    try:
        stripe_price = stripe_subscription["items"].data[0].price
    except IndexError:
        raise BillingError(_("Subscription has not items."))

    subscription_plan = await repo.get_plan_by_remote_id(stripe_price.product)
    if not subscription_plan:
        raise SubscriptionPlanError()

    subscription.status = (
        Subscription.Status.CANCELLED
        if stripe_subscription.cancel_at
        else map_stripe_to_subscription_status(stripe_subscription.status)
    )

    subscription.plan = subscription_plan
    subscription.remote_price_id = stripe_price.id
    subscription.expires_at = datetime.datetime.fromtimestamp(stripe_subscription.current_period_end, tz=datetime.UTC)
    await dbsession.flush()
    return subscription


async def cancel_stripe_subscription(dbsession: AsyncSession, stripe_subscription: stripe.Subscription) -> int | None:
    """Cancel subscription. Return team_id."""
    repo = SubscriptionRepo(dbsession)
    subscription = await repo.get_subscription_by_remote_id(stripe_subscription.id)
    if subscription is None:
        return None

    team_id = subscription.team_id
    await dbsession.delete(subscription)
    await dbsession.flush()
    return team_id
