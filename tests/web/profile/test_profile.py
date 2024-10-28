from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from app.config.crypto import verify_password
from app.contexts.users.models import User
from app.contrib.testing import as_htmx_response


def test_profile_accessible(auth_client: TestClient) -> None:
    response = auth_client.get("/app/profile")
    assert response.status_code == 200


def test_updates_profile(auth_client: TestClient, user: User, dbsession_sync: Session) -> None:
    response = auth_client.post(
        "/app/profile/edit",
        data={
            "first_name": "John1",
            "last_name": "Doe1",
        },
    )

    assert response.status_code == 204
    assert as_htmx_response(response).triggers("toast")

    dbsession_sync.refresh(user)
    assert user.first_name == "John1"
    assert user.last_name == "Doe1"


def test_requires_current_password(auth_client: TestClient, user: User, dbsession_sync: Session) -> None:
    response = auth_client.post(
        "/app/profile/password",
        data={
            "current_password": "invalid_current_password",
            "password": "new_password",
            "password_confirm": "new_password",
        },
    )

    assert response.status_code == 200
    assert "Current password is incorrect." in response.text


def test_validates_passwords(auth_client: TestClient, user: User, dbsession_sync: Session) -> None:
    response = auth_client.post(
        "/app/profile/password",
        data={
            "current_password": "password",
            "password": "new_password",
            "password_confirm": "passwordnotmatch",
        },
    )

    assert response.status_code == 200
    assert "Passwords must match" in response.text


def test_changes_password(auth_client: TestClient, user: User, dbsession_sync: Session) -> None:
    response = auth_client.post(
        "/app/profile/password",
        data={
            "current_password": "password",
            "password": "new_password",
            "password_confirm": "new_password",
        },
    )

    assert response.status_code == 204
    dbsession_sync.refresh(user)
    assert verify_password(user.password, "new_password")


def test_delete_profile(auth_client: TestClient, user: User, dbsession_sync: Session) -> None:
    response = auth_client.delete("/app/profile")

    assert response.status_code == 302
    dbsession_sync.refresh(user)
    assert "deleted" in user.email

    assert auth_client.get("/app/profile").status_code == 302
