import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from starlette_sqlalchemy import Collection, Repo

from app.contexts.billing.models import Subscription, SubscriptionPlan


class SubscriptionPlanRepo(Repo[SubscriptionPlan]):
    model_class = SubscriptionPlan
    base_query = sa.select(SubscriptionPlan)


class SubscriptionRepo(Repo[Subscription]):
    model_class = Subscription
    base_query = sa.select(Subscription).options(
        joinedload(Subscription.plan),
        joinedload(Subscription.team),
    )

    def __init__(self, dbsession: AsyncSession) -> None:
        super().__init__(dbsession)
        self.plans = SubscriptionPlanRepo(dbsession)

    async def get_available_plans(self) -> Collection[SubscriptionPlan]:
        stmt = sa.select(SubscriptionPlan)
        return await self.query.all(stmt)

    async def get_team_subscription(self, team_id: int) -> Subscription | None:
        stmt = sa.select(Subscription).where(Subscription.team_id == team_id).options(joinedload(Subscription.plan))
        return await self.query.one_or_none(stmt)  # type: ignore[arg-type]

    async def get_plan_by_remote_id(self, remote_id: str) -> SubscriptionPlan | None:
        stmt = sa.select(SubscriptionPlan).where(SubscriptionPlan.remote_product_id == remote_id)
        return await self.query.one_or_none(stmt)  # type: ignore[arg-type]

    async def get_subscription_by_remote_id(self, remote_id: str) -> Subscription | None:
        stmt = sa.select(Subscription).where(Subscription.remote_subscription_id == remote_id)
        return await self.query.one_or_none(stmt)  # type: ignore[arg-type]
