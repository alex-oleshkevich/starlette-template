from starlette.testclient import TestClient


def test_version_route(client: TestClient) -> None:
    assert client.get("/version").status_code == 200
