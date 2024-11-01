from starlette.testclient import TestClient


def test_app_area_requires_login(client: TestClient, auth_client: TestClient) -> None:
    assert client.get("/app/").status_code == 302
    assert auth_client.get("/app/").status_code == 200
