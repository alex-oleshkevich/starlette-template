from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from app.contexts.teams.models import TeamMember


def test_app_area_requires_login(client: TestClient, auth_client: TestClient) -> None:
    assert client.get("/app/").status_code == 302
    assert auth_client.get("/app/").status_code == 200


def test_inactive_team_member_should_not_access_app(
    auth_client: TestClient, team_member: TeamMember, dbsession_sync: Session
) -> None:
    team_member.suspend()
    dbsession_sync.commit()

    response = auth_client.get("/app/")
    assert response.status_code == 307
    assert response.headers["location"] == "http://testserver/app/teams/select"
