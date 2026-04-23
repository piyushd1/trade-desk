"""
Unit tests for health check endpoints.
"""

import pytest
from unittest.mock import patch, AsyncMock
from datetime import datetime

from app.main import app
from app.database import get_db

def test_ping(client):
    """Test the ping endpoint."""
    response = client.get("/api/v1/health/ping")
    assert response.status_code == 200
    data = response.json()
    assert data["ping"] == "pong"
    assert "timestamp" in data
    # Verify timestamp format
    datetime.fromisoformat(data["timestamp"])

@pytest.mark.asyncio
async def test_system_status_healthy(client):
    """Test the system status endpoint - healthy scenario."""
    # Mock the database execute method
    mock_db = AsyncMock()
    mock_db.execute.return_value = None

    with patch("app.api.v1.health.get_db", return_value=mock_db):
        # We need to override the dependency in the app
        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            response = client.get("/api/v1/health/status")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["components"]["database"]["status"] == "healthy"
            assert "latency_ms" in data["components"]["database"]
        finally:
            app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_system_status_unhealthy(client):
    """Test the system status endpoint - unhealthy scenario (DB failure)."""
    # Mock the database execute method to raise an exception
    mock_db = AsyncMock()
    mock_db.execute.side_effect = Exception("DB connection failed")

    with patch("app.api.v1.health.get_db", return_value=mock_db):
        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            response = client.get("/api/v1/health/status")
            # Note: The endpoint returns 200 even if components are unhealthy,
            # but the status field in the JSON will be "unhealthy"
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "unhealthy"
            assert data["components"]["database"]["status"] == "unhealthy"
            assert "DB connection failed" in data["components"]["database"]["error"]
        finally:
            app.dependency_overrides.clear()

def test_compliance_status(client):
    """Test the compliance status endpoint."""
    response = client.get("/api/v1/health/compliance")
    assert response.status_code == 200
    data = response.json()
    assert "sebi_compliance" in data
    assert "risk_limits" in data
    assert data["status"] == "configured"
    assert data["sebi_compliance"]["oauth_enabled"] is True
