import datetime

import limits
import pytest
from starlette.testclient import TestClient

from app import error_codes
from app.config.rate_limit import RateLimiter
from app.contexts.users.models import User
from app.http.api.auth.routes import login_rate_limit
from tests.factories import UserFactory


class TestLogin:
    @pytest.fixture(autouse=True)
    async def _login_rate_limit(self, monkeypatch: pytest.MonkeyPatch) -> None:
        limiter = RateLimiter(login_rate_limit, "api_login")
        await limiter.reset()
        monkeypatch.setattr("app.http.api.auth.routes.login_rate_limit", limits.parse("1000/second"))

    def test_success(self, client: TestClient, user: User) -> None:
        response = client.post("/api/auth/login", json={"email": user.email, "password": "password"})
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_invalid_credentials(self, client: TestClient, user: User) -> None:
        response = client.post("/api/auth/login", json={"email": user.email, "password": "password123"})
        assert response.status_code == 400
        assert response.json()["code"] == error_codes.AUTH_INVALID_CREDENTIALS

    def test_inactive_user(self, client: TestClient) -> None:
        user = UserFactory(disabled_at=datetime.datetime.now(datetime.UTC))
        response = client.post("/api/auth/login", json={"email": user.email, "password": "password"})
        assert response.status_code == 400
        assert response.json()["code"] == error_codes.AUTH_ACCOUNT_DISABLED

    def test_login_rate_limit(self, client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("app.http.api.auth.routes.login_rate_limit", limits.parse("1/minute"))

        response = client.post(
            "/api/auth/login", json={"email": "somebody@somewhere.tld", "password": "invalidpassword"}
        )
        assert response.status_code == 400

        response = client.post(
            "/api/auth/login", json={"email": "somebody@somewhere.tld", "password": "invalidpassword"}
        )
        assert response.status_code == 429
        assert response.json()["code"] == error_codes.RATE_LIMITED


class TestLogout:
    def test_success(self, client: TestClient, user: User) -> None:
        response = client.post("/api/auth/login", json={"email": user.email, "password": "password"})
        assert response.status_code == 200
        data = response.json()

        response = client.post("/api/auth/logout", json={"refresh_token": data["refresh_token"]})
        assert response.status_code == 200

        response = client.get("/api/profile")
        assert response.status_code == 401
