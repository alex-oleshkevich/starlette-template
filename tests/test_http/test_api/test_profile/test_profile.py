from mailers.pytest_plugin import Mailbox
from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from app.config.crypto import verify_password
from app.contexts.users.models import User


class TestProfile:
    def test_success(self, api_client: TestClient, user: User) -> None:
        response = api_client.get("/api/profile")
        assert response.status_code == 200

    def test_update(self, api_client: TestClient, dbsession_sync: Session, user: User) -> None:
        response = api_client.patch(
            "/api/profile",
            json={
                "first_name": "Jane",
                "last_name": "Air",
            },
        )

        dbsession_sync.refresh(user)
        assert response.status_code == 200
        assert user.first_name == "Jane"
        assert user.last_name == "Air"


class TestChangePassword:
    def test_change_password(
        self, api_client: TestClient, dbsession_sync: Session, user: User, mailbox: Mailbox
    ) -> None:
        response = api_client.post(
            "/api/profile/change-password",
            json={
                "current_password": "password",
                "password": "new_p@ssword!",
                "password_confirm": "new_p@ssword!",
            },
        )

        assert response.status_code == 200
        assert len(mailbox) == 1

        dbsession_sync.refresh(user)
        assert verify_password(user.password, "new_p@ssword!")

    def test_validates_current_password(
        self, api_client: TestClient, dbsession: Session, user: User, mailbox: Mailbox
    ) -> None:
        response = api_client.post(
            "/api/profile/change-password",
            json={
                "current_password": "invalidpassword",
                "password": "new_p@ssword!",
                "password_confirm": "new_p@ssword!",
            },
        )

        assert response.status_code == 422
        assert len(mailbox) == 0

    def test_validates_password_match(
        self, api_client: TestClient, dbsession: Session, user: User, mailbox: Mailbox
    ) -> None:
        response = api_client.post(
            "/api/profile/change-password",
            json={
                "current_password": "password",
                "password": "new_p@ssword!",
                "password_confirm": "new_p@ssword!gagaga",
            },
        )

        assert response.status_code == 422
        assert len(mailbox) == 0
