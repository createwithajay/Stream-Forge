from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert "status" in response.json()


def test_ingest():
    response = client.post(
        "/api/events",
        json={
            "event_id": "test-1",
            "source": "pytest",
            "temperature": 25,
            "timestamp": 1700000000,
        },
    )
    assert response.status_code == 200
    assert response.json()["accepted"] is True


def test_generate():
    response = client.post("/api/generate?count=10")
    assert response.status_code == 200
    assert response.json()["accepted"] >= 1
