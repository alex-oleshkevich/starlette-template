import datetime

import limits
import pytest
from starlette.testclient import TestClient

from tests.factories import UserFactory


@pytest.fixture(autouse=True)
def _login_limiter(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.web.login.routes.login_limiter", limits.parse("1000/second"))


def test_login_accessible(client: TestClient) -> None:
    response = client.get("/login")
    assert response.status_code == 200


def test_login_with_valid_credentials(client: TestClient) -> None:
    user = UserFactory()
    response = client.post("/login", data={"email": user.email, "password": "password"})
    assert response.status_code == 302
    assert response.headers["location"] == "/"
    assert not response.cookies.get("remember_me")


def test_login_redirects_authenticated(auth_client: TestClient) -> None:
    response = auth_client.get("/login")
    assert response.status_code == 302
    assert response.headers["location"] == "/"


def test_login_redirects_to_next_page(client: TestClient) -> None:
    user = UserFactory()
    response = client.post("/login?next=/app", data={"email": user.email, "password": "password"})
    assert response.status_code == 302
    assert response.headers["location"] == "/app"


def test_login_not_redirects_to_foreign_page(client: TestClient) -> None:
    user = UserFactory()
    response = client.post("/login?next=https://hacker.com/app", data={"email": user.email, "password": "password"})
    assert response.status_code == 302
    assert response.headers["location"] == "/"


def test_login_rate_limit(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.web.login.routes.login_limiter", limits.parse("1/minute"))

    client.post("/login", data={"email": "somebody@somewhere.tld", "password": "invalidpassword"})
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


def test_login_with_remember_me(client: TestClient) -> None:
    user = UserFactory()
    response = client.post("/login", data={"email": user.email, "password": "password", "remember_me": "1"})
    assert response.status_code == 302
    assert response.headers["location"] == "/"
    assert response.cookies.get("remember_me")
