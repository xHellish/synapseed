from fastapi.testclient import TestClient

from app.main import create_app


client = TestClient(create_app())


def test_health_endpoint_returns_ok() -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_login_endpoint_returns_token() -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"identification": "1234567890", "password": "secret123"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["token_type"] == "bearer"
    assert body["user"]["identification"] == "1234567890"


def test_catalogs_endpoint_returns_seed_data() -> None:
    response = client.get("/api/v1/catalogs/crops")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert response.json()[0]["name"]
