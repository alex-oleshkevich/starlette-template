from starlette.testclient import TestClient


def test_google_login(auth_client: TestClient) -> None:
    response = auth_client.get("social/google")
    assert response.status_code == 302
    assert response.headers["location"].startswith("https://accounts.google.com/o/oauth2/v2/auth")
