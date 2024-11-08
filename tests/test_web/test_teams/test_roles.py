import sqlalchemy as sa
from sqlalchemy.orm import Session

from app.contexts.teams.models import Team, TeamRole
from app.contrib.testing import TestAuthClient
from tests.factories import TeamMemberFactory, TeamRoleFactory, UserFactory


class TestRoles:
    def test_roles_page(self, auth_client: TestAuthClient) -> None:
        response = auth_client.get("/app/teams/roles")
        assert response.status_code == 200

    def test_add_role(self, auth_client: TestAuthClient, team: Team, dbsession_sync: Session) -> None:
        response = auth_client.get("/app/teams/roles/new")
        assert response.status_code == 200

        response = auth_client.post(
            "/app/teams/roles/new",
            data={
                "name": "Test Role",
                "is_admin": "1",
            },
        )
        assert response.status_code == 204
        assert dbsession_sync.scalars(
            sa.select(TeamRole).filter(TeamRole.name == "Test Role", TeamRole.team == team)
        ).one_or_none()

    def test_edit_role(self, auth_client: TestAuthClient, team: Team, dbsession_sync: Session) -> None:
        role = TeamRoleFactory(team=team, name="Test Role")
        response = auth_client.get(f"/app/teams/roles/edit/{role.id}")
        assert response.status_code == 200

        response = auth_client.post(
            f"/app/teams/roles/edit/{role.id}",
            data={
                "name": "Test Role2",
                "is_admin": "1",
            },
        )
        assert response.status_code == 204
        assert dbsession_sync.scalars(
            sa.select(TeamRole).filter(TeamRole.name == "Test Role2", TeamRole.team == team)
        ).one_or_none()

    def test_delete_role(self, auth_client: TestAuthClient, team: Team, dbsession_sync: Session) -> None:
        role = TeamRoleFactory(team=team, name="Test Role")
        response = auth_client.post(f"/app/teams/roles/delete/{role.id}")
        assert response.status_code == 204
        assert not dbsession_sync.scalars(
            sa.select(TeamRole).filter(TeamRole.id == role.id, TeamRole.team == team)
        ).one_or_none()

    def test_delete_role_with_members(self, auth_client: TestAuthClient, team: Team, dbsession_sync: Session) -> None:
        """Role should not be deleted if it has members assigned."""
        role = TeamRoleFactory(team=team, name="Test Role")
        user = UserFactory()
        _ = TeamMemberFactory(user=user, team=team, role=role)

        response = auth_client.post(f"/app/teams/roles/delete/{role.id}")
        assert response.status_code == 400
        assert dbsession_sync.scalars(
            sa.select(TeamRole).filter(TeamRole.id == role.id, TeamRole.team == team)
        ).one_or_none()
