"""
Unit tests for main entry point endpoints.
"""

import pytest
from unittest.mock import patch

from app.main import APP_VERSION
from app.config import settings

def test_root_endpoint(client):
    """Test the root API endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == settings.APP_NAME
    assert data["version"] == APP_VERSION
    assert "api" in data

@pytest.mark.asyncio
async def test_main_health_check_healthy(client):
    """Test the main /health endpoint - healthy scenario."""
    with patch("app.main.check_db_connection", return_value=True):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["services"]["database"] == "healthy"

@pytest.mark.asyncio
async def test_main_health_check_unhealthy(client):
    """Test the main /health endpoint - unhealthy scenario."""
    with patch("app.main.check_db_connection", return_value=False):
        response = client.get("/health")
        # According to main.py, it returns 503 if status is not healthy
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "degraded"
        assert data["services"]["database"] == "unhealthy"
