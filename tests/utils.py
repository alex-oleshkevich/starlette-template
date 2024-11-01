from starlette.testclient import TestClient

from app.contexts.users.models import User


def force_user(client: TestClient, user: User) -> TestClient:
    response = client.post("/app/login", data={"email": user.email, "password": "password"})
    assert response.status_code == 302, "Test client login failed"
    return client
