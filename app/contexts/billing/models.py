from __future__ import annotations

import dataclasses
import enum

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.config.sqla.columns import AutoCreatedAt, DateTimeTz, IntPk
from app.config.sqla.models import Base, WithTimestamps
from app.config.sqla.types import EmbedType
from app.contexts.teams.models import Team


class SubscriptionPlan(Base, WithTimestamps):
    __tablename__ = "subscriptions_plans"

    id: Mapped[IntPk]
    name: Mapped[str]
    remote_product_id: Mapped[str] = mapped_column(
        sa.Text, default="", server_default="", doc="Payment processor product ID (like Stripe product ID)"
    )
    subscriptions: Mapped[list[Subscription]] = sa.orm.relationship("Subscription", back_populates="plan")


@dataclasses.dataclass
class SubscriptionMetadata:
    pass


class Subscription(Base):
    __tablename__ = "subscriptions"
    __table_args__ = (sa.UniqueConstraint("team_id", "plan_id"),)

    class Status(enum.StrEnum):
        ACTIVE = "active"
        TRIALING = "trialing"
        CANCELLED = "cancelled"
        UNPAID = "unpaid"
        PAUSED = "paused"
        PAST_DUE = "past_due"

    id: Mapped[IntPk]
    plan_id: Mapped[int] = mapped_column(sa.ForeignKey("subscriptions_plans.id"))
    team_id: Mapped[int] = mapped_column(sa.ForeignKey("teams.id"))
    status: Mapped[Status] = mapped_column(sa.Text, default=Status.ACTIVE, server_default=Status.ACTIVE)
    remote_customer_id: Mapped[str] = mapped_column(
        sa.Text, doc="Payment processor customer ID", index=True, default="", server_default=""
    )
    remote_subscription_id: Mapped[str] = mapped_column(
        sa.Text, doc="Payment processor subscription ID", default="", server_default=""
    )
    remote_price_id: Mapped[str] = mapped_column(
        sa.Text, doc="Payment processor price ID", default="", server_default=""
    )
    expires_at: Mapped[DateTimeTz | None] = mapped_column(doc="When the subscription will expire")
    created_at: Mapped[AutoCreatedAt] = mapped_column(doc="When the first subscription was created")
    meta: Mapped[SubscriptionMetadata] = mapped_column(
        EmbedType(SubscriptionMetadata), default=SubscriptionMetadata, server_default="{}"
    )

    plan: Mapped[SubscriptionPlan] = sa.orm.relationship(SubscriptionPlan, back_populates="subscriptions")
    team: Mapped[Team] = sa.orm.relationship(Team)

    @property
    def is_cancelled(self) -> bool:
        return self.status == self.Status.CANCELLED
