"""Tests for the FastAPI application routes."""

from fastapi.testclient import TestClient

from explainer_factory.api.app import app

client = TestClient(app)


def test_health_endpoint():
    """Test the /health endpoint."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


def test_render_submit_endpoint():
    """Test submitting a render job."""
    response = client.post(
        "/api/v1/render",
        json={"topic": "Black Holes", "difficulty": "beginner"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "pending"
    assert data["topic"] == "Black Holes"
