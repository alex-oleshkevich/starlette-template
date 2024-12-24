import limits
import pytest
from mailers.pytest_plugin import Mailbox
from starlette.testclient import TestClient

from app.config.rate_limit import RateLimiter
from app.http.api.auth.routes import forgot_password_rate_limit
from tests.factories import UserFactory


@pytest.fixture(autouse=True)
async def _forgot_password_rate_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    limiter = RateLimiter(forgot_password_rate_limit, "test_reset_password")
    await limiter.reset()

    monkeypatch.setattr("app.http.api.auth.routes.forgot_password_rate_limit", limits.parse("1000/second"))


def test_success_case(client: TestClient, mailbox: Mailbox) -> None:
    user = UserFactory()
    response = client.post("/api/auth/reset-password", json={"email": user.email})
    print(response.text)
    assert response.status_code == 200
    assert len(mailbox) == 1


def test_missing_user(client: TestClient, mailbox: Mailbox) -> None:
    response = client.post("/api/auth/reset-password", json={"email": "nonexisting@user.tld"})
    assert response.status_code == 200
    assert len(mailbox) == 0


def test_rate_limit(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.http.api.auth.routes.forgot_password_rate_limit", limits.parse("1/minute"))
    response = client.post("/api/auth/reset-password", json={"email": "nonexisting@user.tld"})
    assert response.status_code == 200
    response = client.post("/api/auth/reset-password", json={"email": "nonexisting@user.tld"})
    assert response.status_code == 429
