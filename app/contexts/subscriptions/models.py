from __future__ import annotations

import decimal
import enum

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.config.sqla.columns import AutoCreatedAt, DateTimeTz, IntPk
from app.config.sqla.models import Base, WithTimestamps
from app.config.sqla.types import MoneyType
from app.contexts.teams.models import Team


class SubscriptionPlan(Base, WithTimestamps):
    __tablename__ = "subscriptions_plans"

    id: Mapped[IntPk]
    name: Mapped[str]
    description: Mapped[str] = mapped_column(sa.Text, default="", server_default="")
    price: Mapped[decimal.Decimal] = mapped_column(MoneyType)

    is_archived: Mapped[bool] = mapped_column(
        sa.Boolean,
        default=False,
        server_default=sa.false(),
        doc="Archived plans are not available for new subscriptions",
    )

    is_default: Mapped[bool] = mapped_column(
        sa.Boolean, default=False, server_default=sa.false(), doc="Default plan for new users"
    )

    subscriptions: Mapped[list[Subscription]] = sa.orm.relationship("Subscription", back_populates="plan")


class Subscription(Base):
    __tablename__ = "subscriptions"
    __table_args__ = (sa.UniqueConstraint("team_id", "plan_id"),)

    class Status(enum.StrEnum):
        ACTIVE = "active"
        TRIALING = "trialing"
        PAST_DUE = "past_due"
        CANCELLED = "cancelled"

    class BillingInterval(enum.StrEnum):
        MONTHLY = "monthly"
        ANNUALLY = "annually"

    id: Mapped[IntPk]
    plan_id: Mapped[int] = mapped_column(sa.ForeignKey("subscriptions_plans.id"))
    team_id: Mapped[int] = mapped_column(sa.ForeignKey("teams.id"))
    billing_interval: Mapped[BillingInterval] = mapped_column(
        sa.Text, default=BillingInterval.MONTHLY, server_default=BillingInterval.MONTHLY
    )
    auto_renew: Mapped[bool] = mapped_column(sa.Boolean, default=True, server_default=sa.true())
    status: Mapped[Status] = mapped_column(sa.Text, default=Status.ACTIVE, server_default=Status.ACTIVE)
    subscribed_at: Mapped[AutoCreatedAt]
    subscribed_until: Mapped[DateTimeTz | None]

    plan: Mapped[SubscriptionPlan] = sa.orm.relationship(SubscriptionPlan, back_populates="subscriptions")
    team: Mapped[Team] = sa.orm.relationship(Team)
    invoices: Mapped[list[SubscriptionInvoice]] = sa.orm.relationship(
        "SubscriptionInvoice", back_populates="subscription"
    )


class SubscriptionInvoice(Base):
    __tablename__ = "subscriptions_invoices"

    class Status(enum.StrEnum):
        UNPAID = "unpaid"
        PAID = "paid"

    id: Mapped[IntPk]
    number: Mapped[str]
    status: Mapped[Status] = mapped_column(sa.Text, default=Status.UNPAID, server_default=Status.UNPAID)
    amount: Mapped[decimal.Decimal] = mapped_column(MoneyType, default=0, server_default="0")
    tax: Mapped[decimal.Decimal] = mapped_column(MoneyType, default=0, server_default="0")
    tax_rate: Mapped[int] = mapped_column(sa.Integer, default=0, server_default="0")
    team_id: Mapped[int] = mapped_column(sa.ForeignKey("teams.id"))
    subscription_id: Mapped[int] = mapped_column(sa.ForeignKey("subscriptions.id"))
    created_at: Mapped[AutoCreatedAt]

    team: Mapped[Team] = sa.orm.relationship(Team)
    subscription: Mapped[Subscription] = sa.orm.relationship(Subscription, back_populates="invoices")
    payments: Mapped[list[SubscriptionPayment]] = sa.orm.relationship("SubscriptionPayment", back_populates="invoice")


class SubscriptionPayment(Base):
    __tablename__ = "subscriptions_payments"

    class Status(enum.StrEnum):
        PENDING = "pending"
        PAID = "paid"
        FAILED = "failed"

    id: Mapped[IntPk]
    team_id: Mapped[Team] = mapped_column(sa.ForeignKey("teams.id"))
    invoice_id: Mapped[SubscriptionInvoice] = mapped_column(sa.ForeignKey("subscriptions_invoices.id"))
    total: Mapped[decimal.Decimal] = mapped_column(MoneyType, default=0, server_default="0")
    paid_at: Mapped[DateTimeTz | None]
    status: Mapped[Status] = mapped_column(sa.Text, default=Status.PENDING, server_default=Status.PENDING)
    error: Mapped[str | None]
    created_at: Mapped[AutoCreatedAt]

    team: Mapped[Team] = sa.orm.relationship(Team)
    invoice: Mapped[SubscriptionInvoice] = sa.orm.relationship(SubscriptionInvoice, back_populates="payments")
