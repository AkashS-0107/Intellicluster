"""
Tests for FastAPI application health check probe and root endpoints.
"""

from fastapi.testclient import TestClient


def test_read_root(client: TestClient):
    """Verify GET / returns 200 with step and application metadata."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "IntelliCluster" in data["message"]
    assert data["step"] == "Step 1 of 10: Backend Foundation"
    assert data["health_url"] == "/health"


def test_health_check_endpoint(client: TestClient):
    """Verify GET /health returns 200 and healthy status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "healthy"
    assert data["app_name"] == "IntelliCluster Backend"
    assert data["step"] == "1 (Backend)"
    assert "timestamp" in data
