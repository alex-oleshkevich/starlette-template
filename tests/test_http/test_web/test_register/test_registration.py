import faker
import limits
import pytest
import sqlalchemy as sa
from mailers.pytest_plugin import Mailbox
from sqlalchemy.orm import Session, joinedload
from starlette.testclient import TestClient

from app.config.rate_limit import RateLimiter
from app.contexts.teams.models import TeamMember
from app.contexts.users.models import User
from app.http.dependencies import Settings
from app.http.web.register.routes import register_rate_limit


@pytest.fixture(autouse=True)
async def _register_rate_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    limiter = RateLimiter(register_rate_limit, "register")
    await limiter.reset()
    monkeypatch.setattr("app.http.web.register.routes.register_rate_limit", limits.parse("1000/second"))


def test_registration_page_accessible(client: TestClient) -> None:
    response = client.get("/register")
    assert response.status_code == 200


def test_privacy_policy_page(client: TestClient) -> None:
    response = client.get("/register/privacy-policy")
    assert response.status_code == 200


def test_terms_of_service_page(client: TestClient) -> None:
    response = client.get("/register/terms-of-service")
    assert response.status_code == 200


def test_registration_with_valid_data_and_autologin(
    client: TestClient,
    dbsession_sync: Session,
    settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "register_auto_login", True)
    email = faker.Faker().email()
    response = client.post(
        "/register",
        data={
            "email": email,
            "first_name": "John",
            "last_name": "Doe",
            "password": "password",
            "password_confirm": "password",
            "terms": "1",
        },
    )
    assert response.status_code == 302
    assert response.headers["location"] == "http://testserver/app/"

    response = client.get("/login", follow_redirects=False)
    assert response.status_code == 302

    stmt = sa.select(User).where(User.email == email)
    assert dbsession_sync.scalars(stmt).one()


def test_registration_with_valid_data_without_autologin(
    client: TestClient,
    settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "register_auto_login", False)
    email = faker.Faker().email()
    response = client.post(
        "/register",
        data={
            "email": email,
            "first_name": "John",
            "last_name": "Doe",
            "password": "password",
            "password_confirm": "password",
            "terms": "1",
        },
    )
    assert response.status_code == 302
    assert response.headers["location"] == "http://testserver/login"

    response = client.get("/login", follow_redirects=False)
    assert response.status_code == 200


def test_registration_creates_team_and_role(
    client: TestClient,
    dbsession_sync: Session,
    settings: Settings,
) -> None:
    email = faker.Faker().email()
    response = client.post(
        "/register",
        data={
            "email": email,
            "first_name": "John",
            "last_name": "Doe",
            "password": "password",
            "password_confirm": "password",
            "terms": "1",
        },
    )
    assert response.status_code == 302

    user = dbsession_sync.scalars(sa.select(User).where(User.email == email)).one()
    team_member = dbsession_sync.scalars(
        sa.select(TeamMember)
        .where(TeamMember.user_id == user.id)
        .options(
            joinedload(TeamMember.team),
        )
    ).one()
    assert team_member
    assert team_member.role.is_admin
    assert team_member.team
    assert team_member.team.name == f"{user.first_name}'s team"


def test_registration_with_invalid_data(client: TestClient, mailbox: Mailbox) -> None:
    email = faker.Faker().email()
    response = client.post(
        "/register",
        data={
            "email": email,
            "first_name": "John",
            "last_name": "Doe",
            "password": "password",
            "password_confirm": "anotherpassword",
            "terms": "1",
        },
    )
    assert response.status_code == 400
    assert len(mailbox) == 0


def test_registration_with_email_confirmation(
    client: TestClient,
    mailbox: Mailbox,
    settings: Settings,
    dbsession_sync: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "register_require_email_confirmation", True)
    email = faker.Faker().email()
    response = client.post(
        "/register",
        data={
            "email": email,
            "first_name": "John",
            "last_name": "Doe",
            "password": "password",
            "password_confirm": "password",
            "terms": "1",
        },
    )
    assert response.status_code == 302
    assert len(mailbox) == 1

    stmt = sa.select(User).where(User.email == email)
    user = dbsession_sync.scalars(stmt).one()
    assert user.email_confirmed_at is None


def test_registration_without_email_confirmation(
    client: TestClient,
    mailbox: Mailbox,
    settings: Settings,
    dbsession_sync: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "register_require_email_confirmation", False)
    email = faker.Faker().email()
    response = client.post(
        "/register",
        data={
            "email": email,
            "first_name": "John",
            "last_name": "Doe",
            "password": "password",
            "password_confirm": "password",
            "terms": "1",
        },
    )
    assert response.status_code == 302
    assert len(mailbox) == 0

    stmt = sa.select(User).where(User.email == email)
    user = dbsession_sync.scalars(stmt).one()
    assert user.email_confirmed_at is not None


def test_register_rate_limit(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.http.web.register.routes.register_rate_limit", limits.parse("1/minute"))

    response = client.post(
        "/register",
        data={
            "email": faker.Faker().email(),
            "first_name": "John",
            "last_name": "Doe",
            "password": "password",
            "password_confirm": "password",
            "terms": "1",
        },
    )
    assert response.status_code == 302

    response = client.post(
        "/register",
        data={
            "email": faker.Faker().email(),
            "first_name": "John",
            "last_name": "Doe",
            "password": "password",
            "password_confirm": "password",
            "terms": "1",
        },
    )
    assert response.status_code == 429
