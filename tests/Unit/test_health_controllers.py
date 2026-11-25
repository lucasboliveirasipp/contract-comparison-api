from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


def test_liveness_returns_status_ok():
    response = client.get("/health/liveness")
    assert response.status_code == 200
    assert response.json()["status"] == "OK"


def test_readiness_returns_status_ok():
    response = client.get("/health/readiness")
    assert response.status_code == 200
    assert response.json()["status"] == "OK"
