from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from app.config.files import file_storage
from app.contexts.teams.models import Team
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


class TestGeneralSettings:
    def test_page_accessible(self, auth_client: TestClient) -> None:
        response = auth_client.get("/app/teams/settings")
        assert response.status_code == 200

    async def test_update_info(self, auth_client: TestClient, team: Team, dbsession_sync: Session) -> None:
        response = auth_client.post(
            "/app/teams/settings",
            data={
                "name": "Team Name",
            },
            files={
                "logo": ("logo.jpg", b"content", "image/jpeg"),
            },
        )
        assert response.status_code == 204

        dbsession_sync.refresh(team)
        assert team.name == "Team Name"
        assert team.logo == f"teams/{team.id}/logo.jpg"
        assert await file_storage.exists(f"teams/{team.id}/logo.jpg")

    async def test_remove_logo(self, auth_client: TestClient, team: Team, dbsession_sync: Session) -> None:
        team.logo = "teams/1/logo.jpg"
        await file_storage.write("teams/1/logo.jpg", b"content")
        dbsession_sync.commit()

        response = auth_client.post(
            "/app/teams/settings",
            data={
                "logo_clear": "y",
            },
        )
        assert response.status_code == 204

        dbsession_sync.refresh(team)
        assert team.logo is None
        assert not await file_storage.exists(f"teams/{team.id}/logo.jpg")
