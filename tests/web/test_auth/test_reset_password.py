import limits
import pytest
from mailers.pytest_plugin import Mailbox
from sqlalchemy.orm import Session
from starlette.requests import Request
from starlette.testclient import TestClient

from app.config.crypto import make_password, verify_password
from app.config.rate_limit import RateLimiter
from app.contexts.auth.passwords import make_password_reset_link
from app.web.auth.routes import forgot_password_rate_limit
from tests.factories import UserFactory


@pytest.fixture(autouse=True)
async def _forgot_password_rate_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    limiter = RateLimiter(forgot_password_rate_limit, "login")
    await limiter.reset()

    monkeypatch.setattr("app.web.auth.routes.forgot_password_rate_limit", limits.parse("1000/second"))


def test_page_accessible(client: TestClient) -> None:
    response = client.get("/forgot-password")
    assert response.status_code == 200


def test_success_case(client: TestClient, mailbox: Mailbox) -> None:
    user = UserFactory()
    response = client.post("/forgot-password", data={"email": user.email})
    assert response.status_code == 302
    assert response.headers["location"] == "http://testserver/forgot-password/sent"
    assert len(mailbox) == 1


def test_missing_user(client: TestClient, mailbox: Mailbox) -> None:
    response = client.post("/forgot-password", data={"email": "nonexisting@user.tld"})
    assert response.status_code == 302
    assert response.headers["location"] == "http://testserver/forgot-password/sent"
    assert len(mailbox) == 0


def test_rate_limit(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.web.auth.routes.forgot_password_rate_limit", limits.parse("1/minute"))
    response = client.post("/forgot-password", data={"email": "nonexisting@user.tld"})
    assert response.status_code == 302
    response = client.post("/forgot-password", data={"email": "nonexisting@user.tld"})
    assert response.status_code == 429


def test_changes_password_accessible(client: TestClient, mailbox: Mailbox, http_request: Request) -> None:
    user = UserFactory()

    link = make_password_reset_link(http_request, user)
    response = client.get(link.path)
    assert response.status_code == 200


def test_changes_password(client: TestClient, dbsession_sync: Session, mailbox: Mailbox, http_request: Request) -> None:
    user = UserFactory()

    link = make_password_reset_link(http_request, user)
    response = client.post(link.path, data={"password": "newpassword", "password_confirm": "newpassword"})
    assert response.status_code == 302
    assert response.headers["location"] == "http://testserver/login"
    assert len(mailbox) == 1

    dbsession_sync.refresh(user)
    assert verify_password(user.password, "newpassword")


def test_invalid_password(client: TestClient, dbsession_sync: Session, mailbox: Mailbox, http_request: Request) -> None:
    user = UserFactory()

    link = make_password_reset_link(http_request, user)
    response = client.post(link.path, data={"password": "newpassword", "password_confirm": "anotherpassword"})
    assert response.status_code == 200
    assert len(mailbox) == 0

    dbsession_sync.refresh(user)
    assert not verify_password(user.password, "newpassword")
    assert "Passwords must match." in response.text


def test_invalid_email(client: TestClient, mailbox: Mailbox, http_request: Request) -> None:
    user = UserFactory()

    link = make_password_reset_link(http_request, user)
    *_, signature = link.path.split("/")
    response = client.get(f"/change-password/invalidmail/{signature}")
    assert response.status_code == 400


def test_invalid_signature(client: TestClient, mailbox: Mailbox, http_request: Request) -> None:
    user = UserFactory()

    link = make_password_reset_link(http_request, user)
    *_, email, _ = link.path.split("/")
    response = client.get(f"/change-password/{email}/invalidsignature")
    assert response.status_code == 400


def test_changes_password_second_attempt(client: TestClient, dbsession_sync: Session, http_request: Request) -> None:
    user = UserFactory()

    link = make_password_reset_link(http_request, user)

    # change user password in the meantime, this should invalidate the link signature
    user.password = make_password("alternatepassword")
    dbsession_sync.commit()

    response = client.post(link.path, data={"password": "newpassword", "password_confirm": "newpassword"})
    assert response.status_code == 400
