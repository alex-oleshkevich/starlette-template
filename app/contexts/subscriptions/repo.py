import sqlalchemy as sa
from starlette_sqlalchemy import Repo

from app.contexts.subscriptions.models import Subscription, SubscriptionPlan


class SubscriptionRepo(Repo[Subscription]):
    model_class = Subscription
    base_query = sa.select(Subscription)

    async def get_default_plan(self) -> SubscriptionPlan | None:
        stmt = sa.select(SubscriptionPlan).where(SubscriptionPlan.is_default.is_(True))
        return await self.query.one_or_none(stmt)  # type: ignore[arg-type]
