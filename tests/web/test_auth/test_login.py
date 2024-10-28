import datetime

import limits
import pytest
from starlette.testclient import TestClient

from app.config.rate_limit import RateLimiter
from app.web.auth.routes import login_rate_limit
from tests.factories import UserFactory


@pytest.fixture(autouse=True)
async def _login_rate_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    limiter = RateLimiter(login_rate_limit, "login")
    await limiter.reset()
    monkeypatch.setattr("app.web.auth.routes.login_rate_limit", limits.parse("1000/second"))


def test_login_accessible(client: TestClient) -> None:
    response = client.get("/login")
    assert response.status_code == 200


def test_login_with_valid_credentials(client: TestClient) -> None:
    user = UserFactory()
    response = client.post("/login", data={"email": user.email, "password": "password"})
    assert response.status_code == 302
    assert response.headers["location"] == "http://testserver/app/"
    assert not response.cookies.get("remember_me")


def test_login_redirects_authenticated(auth_client: TestClient) -> None:
    response = auth_client.get("/login")
    assert response.status_code == 302
    assert response.headers["location"] == "http://testserver/app/"


def test_login_redirects_unauthenticated(client: TestClient) -> None:
    response = client.get("/app/profile")
    assert response.status_code == 302
    assert response.headers["location"] == "/login?next=%2Fapp%2Fprofile"


def test_login_redirects_to_next_page(client: TestClient) -> None:
    user = UserFactory()
    response = client.post("/login?next=/app/profile", data={"email": user.email, "password": "password"})
    assert response.status_code == 302
    assert response.headers["location"] == "/app/profile"


def test_login_not_redirects_to_foreign_page(client: TestClient) -> None:
    user = UserFactory()
    response = client.post("/login?next=https://hacker.com/app", data={"email": user.email, "password": "password"})
    assert response.status_code == 302
    assert response.headers["location"] == "/"


def test_login_rate_limit(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.web.auth.routes.login_rate_limit", limits.parse("1/minute"))

    response = client.post("/login", data={"email": "somebody@somewhere.tld", "password": "invalidpassword"})
    assert response.status_code == 400
    response = client.post("/login", data={"email": "somebody@somewhere.tld", "password": "invalidpassword"})
    assert response.status_code == 429


def test_login_with_invalid_email(client: TestClient) -> None:
    response = client.post("/login", data={"email": "somebody@somewhere.tld", "password": "password"})
    assert response.status_code == 400


def test_login_with_invalid_password(client: TestClient) -> None:
    user = UserFactory()
    response = client.post("/login", data={"email": user.email, "password": "invalidpassword"})
    assert response.status_code == 400


def test_login_with_disabled_account(client: TestClient) -> None:
    user = UserFactory(disabled_at=datetime.datetime.now(tz=datetime.UTC))
    response = client.post("/login", data={"email": user.email, "password": "password"})
    assert response.status_code == 400
    assert "This account is deactivated." in response.text
