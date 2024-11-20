import sqlalchemy as sa
from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from app.contexts.teams.models import Team, TeamMember
from app.contrib.testing import TestAuthClient
from tests.factories import TeamMemberFactory, UserFactory


class TestMemberships:
    def test_members_page(self, auth_client: TestClient, team: Team) -> None:
        response = auth_client.get("/app/teams/members")
        assert response.status_code == 200

    def test_suspend_membership(
        self, auth_client: TestAuthClient, team_member: TeamMember, dbsession_sync: Session
    ) -> None:
        response = auth_client.post("/app/teams/members/toggle-status/-1")
        assert response.status_code == 404

        user = UserFactory()
        team_member = TeamMemberFactory(team=team_member.team, user=user)
        response = auth_client.post(f"/app/teams/members/toggle-status/{team_member.id}")
        assert response.status_code == 204

        dbsession_sync.refresh(team_member)
        assert team_member.is_suspended

    def test_suspend_team_owner(
        self, auth_client: TestAuthClient, team_member: TeamMember, dbsession_sync: Session
    ) -> None:
        """Team owners cannot be suspended."""
        assert team_member.user == team_member.team.owner
        response = auth_client.post(f"/app/teams/members/toggle-status/{team_member.id}")
        assert response.status_code == 400
        assert dbsession_sync.scalars(sa.select(TeamMember).where(TeamMember.id == team_member.id)).one_or_none()

    async def test_leave_team(
        self, auth_client: TestAuthClient, team_member: TeamMember, dbsession_sync: Session
    ) -> None:
        """Any user can leave the team on their own."""
        user = UserFactory()
        team_member = TeamMemberFactory(team=team_member.team, user=user)
        await auth_client.force_user(user)
        response = auth_client.post("/app/teams/members/leave")
        assert response.status_code == 302
        assert response.headers["location"] == "http://testserver/app/"
        assert not dbsession_sync.scalars(
            sa.select(TeamMember).where(TeamMember.id == team_member.id, TeamMember.suspended_at.is_(None))
        ).one_or_none()

    def test_leave_team_owner(
        self, auth_client: TestAuthClient, team_member: TeamMember, dbsession_sync: Session
    ) -> None:
        """Team owners cannot leave the team."""
        assert team_member.user == team_member.team.owner
        response = auth_client.post("/app/teams/members/leave")
        assert response.status_code == 400
        assert dbsession_sync.scalars(sa.select(TeamMember).where(TeamMember.id == team_member.id)).one_or_none()

    def test_resume_membership(
        self, auth_client: TestAuthClient, team_member: TeamMember, dbsession_sync: Session
    ) -> None:
        user = UserFactory()
        team_member = TeamMemberFactory(team=team_member.team, user=user, suspended_at="2021-01-01")
        response = auth_client.post(f"/app/teams/members/toggle-status/{team_member.id}")
        assert response.status_code == 204

        dbsession_sync.refresh(team_member)
        assert not team_member.is_suspended
