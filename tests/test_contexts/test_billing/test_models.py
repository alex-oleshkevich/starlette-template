import datetime

from app.contexts.billing.models import Subscription


class TestSubscription:
    def test_is_cancelled(self) -> None:
        subscription = Subscription(status=Subscription.Status.CANCELLED)
        assert subscription.is_cancelled is True

    def test_is_expired(self) -> None:
        subscription = Subscription(expires_at=datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=1))
        assert subscription.is_expired is True

    def test_is_trialing(self) -> None:
        subscription = Subscription(status=Subscription.Status.TRIALING)
        assert subscription.is_trialing is True

    def test_is_expires_soon(self) -> None:
        subscription = Subscription(expires_at=datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=2))
        assert subscription.is_expires_soon is True
