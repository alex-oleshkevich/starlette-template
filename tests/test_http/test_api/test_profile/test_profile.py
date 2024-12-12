from starlette.testclient import TestClient

from app.contexts.users.models import User


class TestProfile:
    def test_success(self, api_client: TestClient, user: User) -> None:
        response = api_client.get("/api/profile")
        assert response.status_code == 200
