import datetime

from mailers.pytest_plugin import Mailbox
from sqlalchemy.orm import Session
from starlette.requests import Request
from starlette.testclient import TestClient

from app.config import crypto
from app.contexts.register.verification import confirm_user_email, make_verification_token
from app.contexts.users.models import User
from tests.factories import UserFactory


def test_email_verification(client: TestClient, http_request: Request, dbsession_sync: Session) -> None:
    user = UserFactory()
    token = make_verification_token(user)
    verification_link = http_request.url_for("verify_email", token=token)
    response = client.get(str(verification_link))
    assert response.status_code == 200
    assert "has been verified" in response.text

    dbsession_sync.refresh(user)
    assert user.is_confirmed


def test_user_not_found(client: TestClient, http_request: Request) -> None:
    token = crypto.sign_value("some@email.tl")
    verification_link = http_request.url_for("verify_email", token=token)
    response = client.get(str(verification_link))
    assert response.status_code == 200
    assert "invalid or expired" in response.text


def test_already_confirmed(client: TestClient, http_request: Request) -> None:
    user = UserFactory(email_confirmed_at=datetime.datetime.now(datetime.UTC))
    token = make_verification_token(user)
    verification_link = http_request.url_for("verify_email", token=token)
    response = client.get(str(verification_link))
    assert response.status_code == 200
    assert "invalid or expired" in response.text


def test_resend_verification_email(auth_client: TestClient, mailbox: Mailbox) -> None:
    response = auth_client.post("/register/verify-email/resend")
    assert response.status_code == 204
    assert len(mailbox) == 1


def test_resend_verification_already_confirmed(
    auth_client: TestClient, mailbox: Mailbox, user: User, dbsession_sync: Session
) -> None:
    confirm_user_email(user)
    dbsession_sync.commit()

    response = auth_client.post("/register/verify-email/resend")
    assert response.status_code == 204
    assert len(mailbox) == 0


def test_resend_verification_requires_authenticated(client: TestClient, mailbox: Mailbox) -> None:
    response = client.post("/register/verify-email/resend")
    assert response.status_code == 302
    assert len(mailbox) == 0
