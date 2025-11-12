"""
PyTest Configuration and Fixtures

This module provides common fixtures and configuration for all tests.
"""

import asyncio
import os
import sys
from typing import AsyncGenerator, Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

# Add backend directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.config import settings
from app.database import Base, get_db
from app.main import app

# Test database URL - use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
TEST_SYNC_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    await engine.dispose()


@pytest.fixture(scope="function")
async def test_db(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    TestSessionLocal = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()


@pytest.fixture(scope="session")
def test_sync_engine():
    """Create synchronous test database engine for TestClient."""
    engine = create_engine(
        TEST_SYNC_DATABASE_URL,
        echo=False,
        future=True,
    )
    
    Base.metadata.create_all(bind=engine)
    
    yield engine
    
    engine.dispose()


@pytest.fixture(scope="function")
def test_sync_db(test_sync_engine) -> Generator[Session, None, None]:
    """Create synchronous test database session."""
    TestSessionLocal = sessionmaker(
        bind=test_sync_engine,
        autocommit=False,
        autoflush=False,
    )
    
    session = TestSessionLocal()
    
    yield session
    
    session.rollback()
    session.close()


@pytest.fixture(scope="function")
def client(test_sync_db) -> Generator[TestClient, None, None]:
    """Create test client with database override."""
    
    def override_get_db():
        try:
            yield test_sync_db
        finally:
            test_sync_db.rollback()
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers():
    """Create authentication headers for testing."""
    # TODO: Implement JWT token generation for tests
    return {"Authorization": "Bearer test-token"}


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "Test@123456",
        "full_name": "Test User",
    }


@pytest.fixture
def sample_risk_config():
    """Sample risk configuration for testing."""
    return {
        "max_position_value": 100000.0,
        "max_daily_loss": 10000.0,
        "max_positions": 10,
        "max_drawdown_pct": 20.0,
        "default_stop_loss_pct": 3.0,
        "default_target_profit_pct": 6.0,
        "is_active": True,
    }


@pytest.fixture
def mock_zerodha_response():
    """Mock Zerodha API responses."""
    return {
        "profile": {
            "user_id": "TEST123",
            "user_name": "Test User",
            "email": "test@example.com",
            "user_type": "individual",
            "broker": "ZERODHA",
        },
        "margins": {
            "equity": {
                "available": {"cash": 100000.0, "collateral": 0},
                "utilised": {"debits": 0, "exposure": 0},
            }
        },
        "positions": [],
        "orders": [],
    }


# Markers for different test types
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration
pytest.mark.slow = pytest.mark.slow
pytest.mark.requires_db = pytest.mark.requires_db
pytest.mark.requires_redis = pytest.mark.requires_redis
