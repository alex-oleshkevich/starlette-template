from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from app.contexts.users.models import User
from tests.factories import TeamFactory, TeamMemberFactory, TeamRoleFactory, UserFactory


class TestTeamSelector:
    def test_selects_team(self, auth_client: TestClient, user: User, dbsession_sync: Session) -> None:
        team = TeamFactory(owner_id=user.id)
        TeamMemberFactory(user=user, team=team, role=TeamRoleFactory())

        response = auth_client.get("/app/teams/select")
        assert response.status_code == 200

        response = auth_client.post("/app/teams/select", data={"team_id": str(team.id)})
        assert response.status_code == 302
        assert response.cookies.get("team_id", path="/") == str(team.id)

    def test_cannot_access_others_team(self, auth_client: TestClient, dbsession_sync: Session) -> None:
        user = UserFactory()
        team = TeamFactory(owner_id=user.id)
        TeamMemberFactory(user=user, team=team, role=TeamRoleFactory())

        response = auth_client.get("/app/teams/select")
        assert response.status_code == 200

        response = auth_client.post("/app/teams/select", data={"team_id": str(team.id)})
        assert response.status_code == 200
        assert response.cookies.get("team_id", path="/") is None
        assert "Invalid team." in response.text
