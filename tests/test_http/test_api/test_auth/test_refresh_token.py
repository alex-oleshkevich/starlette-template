import pytest
from starlette.testclient import TestClient

from app import error_codes
from app.config.settings import Config
from app.contexts.users.models import User


class TestRefreshToken:
    def test_success_with_rolling(
        self, client: TestClient, user: User, settings: Config, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(settings, "session_rolling", True)
        response = client.post("/api/auth/login", json={"email": user.email, "password": "password"})
        assert response.status_code == 200
        data = response.json()
        access_token = data["access_token"]
        refresh_token = data["refresh_token"]

        response = client.post("/api/auth/refresh", json={"refresh_token": data["refresh_token"]})
        data = response.json()
        assert response.status_code == 200

        assert data["access_token"] != access_token, "Access token should be rotated."
        assert data["refresh_token"] != refresh_token, "Refresh token should be rotated."

        # token should be blacklisted
        response = client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
        assert response.status_code == 400, "Refresh token should be revoked."
        assert response.json()["code"] == error_codes.AUTH_INVALID_REFRESH_TOKEN

    def test_success_with_not_rolling(
        self, client: TestClient, user: User, settings: Config, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(settings, "session_rolling", False)
        response = client.post("/api/auth/login", json={"email": user.email, "password": "password"})
        assert response.status_code == 200
        data = response.json()
        access_token = data["access_token"]
        refresh_token = data["refresh_token"]

        response = client.post("/api/auth/refresh", json={"refresh_token": data["refresh_token"]})
        data = response.json()
        assert response.status_code == 200

        assert data["access_token"] != access_token, "Access token should be rotated."
        assert data["refresh_token"] == refresh_token, "Refresh token should be rotated."

    def test_invalid_token(self, client: TestClient, user: User) -> None:
        response = client.post("/api/auth/refresh", json={"refresh_token": "boom"})
        assert response.status_code == 400
        assert response.json()["code"] == error_codes.AUTH_INVALID_REFRESH_TOKEN
