from starlette.testclient import TestClient


def test_logout(auth_client: TestClient) -> None:
    response = auth_client.post("/logout")
    assert response.status_code == 302
    assert response.headers["location"] == "http://testserver/login"

    response = auth_client.get("/app/")
    assert response.status_code == 302
    assert response.headers["location"] == "/login?next=%2Fapp%2F"


def test_logout_when_unauthenticated(client: TestClient) -> None:
    response = client.post("/logout")
    assert response.status_code == 302
    assert response.headers["location"] == "http://testserver/login"


def test_logout_get_request_disabled(client: TestClient) -> None:
    response = client.get("/logout")
    assert response.status_code == 405
