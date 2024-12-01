import sqlalchemy as sa
from mailers.pytest_plugin import Mailbox
from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from app.config.crypto import verify_password
from app.contexts.teams.models import TeamMember
from app.contexts.users.models import User
from app.contrib.testing import TestAuthClient, as_htmx_response
from tests.factories import TeamMemberFactory, UserFactory


def test_profile_accessible(auth_client: TestClient) -> None:
    response = auth_client.get("/app/profile")
    assert response.status_code == 200


def test_updates_profile(auth_client: TestClient, user: User, dbsession_sync: Session) -> None:
    response = auth_client.post(
        "/app/profile/edit",
        data={
            "first_name": "John1",
            "last_name": "Doe1",
            "language": "en",
            "timezone": "Europe/Berlin",
        },
    )

    assert response.status_code == 204
    assert as_htmx_response(response).triggers("toast")

    dbsession_sync.refresh(user)
    assert user.first_name == "John1"
    assert user.last_name == "Doe1"
    assert user.language == "en"
    assert user.timezone == "Europe/Berlin"


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


def test_delete_profile(auth_client: TestClient, user: User, dbsession_sync: Session, mailbox: Mailbox) -> None:
    response = auth_client.delete("/app/profile")

    assert response.status_code == 302
    dbsession_sync.refresh(user)
    assert "deleted" in user.email

    assert auth_client.get("/app/profile").status_code == 302
    assert len(mailbox)
    assert mailbox[0]["subject"] == "Your account has been deleted"


async def test_leave_team(auth_client: TestAuthClient, team_member: TeamMember, dbsession_sync: Session) -> None:
    """Any user can leave the team on their own."""
    user = UserFactory()
    team_member = TeamMemberFactory(team=team_member.team, user=user)
    await auth_client.force_user(user)
    response = auth_client.post("/app/profile/leave")
    assert response.status_code == 302
    assert response.headers["location"] == "http://testserver/app/"
    assert not dbsession_sync.scalars(
        sa.select(TeamMember).where(TeamMember.id == team_member.id, TeamMember.suspended_at.is_(None))
    ).one_or_none()


def test_leave_team_owner(auth_client: TestAuthClient, team_member: TeamMember, dbsession_sync: Session) -> None:
    """Team owners cannot leave the team."""
    assert team_member.user == team_member.team.owner
    response = auth_client.post("/app/profile/leave")
    assert response.status_code == 403
    assert dbsession_sync.scalars(sa.select(TeamMember).where(TeamMember.id == team_member.id)).one_or_none()
