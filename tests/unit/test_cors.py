"""
Unit tests for CORS configuration and middleware behavior.
"""

from fastapi.testclient import TestClient
from intellicluster.core.config import Settings
from intellicluster.main import app


def test_cors_settings_parsing():
    """Verify CORS_ORIGINS parses list, comma-separated string, and JSON array."""
    # Default
    s1 = Settings()
    assert "http://localhost:3000" in s1.CORS_ORIGINS
    assert "http://127.0.0.1:3000" in s1.CORS_ORIGINS

    # Comma-separated string
    s2 = Settings(CORS_ORIGINS="http://example.com, https://app.example.com")
    assert s2.CORS_ORIGINS == ["http://example.com", "https://app.example.com"]

    # JSON string
    s3 = Settings(CORS_ORIGINS='["http://sub.domain.com"]')
    assert s3.CORS_ORIGINS == ["http://sub.domain.com"]


def test_cors_headers_allowed_origin():
    """Verify that requests from an allowed origin receive CORS headers."""
    client = TestClient(app)
    response = client.get(
        "/health",
        headers={"Origin": "http://localhost:3000"},
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"
    assert response.headers.get("access-control-allow-credentials") == "true"


def test_cors_headers_disallowed_origin():
    """Verify that requests from an unauthorized origin do not receive CORS allow header."""
    client = TestClient(app)
    response = client.get(
        "/health",
        headers={"Origin": "http://malicious-attacker.com"},
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers


def test_cors_preflight_options():
    """Verify preflight OPTIONS request from allowed origin."""
    client = TestClient(app)
    response = client.options(
        "/api/v1/clusters/",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"
    assert "POST" in response.headers.get("access-control-allow-methods", "")
