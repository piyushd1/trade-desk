"""
Unit tests for configuration module.
"""

import pytest

from app.config import settings


class TestConfig:
    """Test configuration loading and validation."""
    
    def test_settings_loaded(self):
        """Test that settings are loaded properly."""
        assert settings is not None
        assert settings.APP_NAME == "TradeDesk"
    
    def test_environment_properties(self):
        """Test environment detection properties."""
        # In test environment, should be development by default
        assert settings.APP_ENV in ["development", "staging", "production"]
        
        # Test boolean properties
        if settings.APP_ENV == "development":
            assert settings.is_development is True
            assert settings.is_production is False
        elif settings.APP_ENV == "production":
            assert settings.is_production is True
            assert settings.is_development is False
    
    def test_jwt_settings(self):
        """Test JWT configuration."""
        assert settings.JWT_ALGORITHM == "HS256"
        assert settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES > 0
        assert settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS > 0
        
        # Test computed properties
        assert settings.access_token_expire_minutes == settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        assert settings.refresh_token_expire_minutes == settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60
    
    def test_risk_management_defaults(self):
        """Test risk management default values."""
        assert settings.MAX_POSITION_VALUE > 0
        assert settings.MAX_DAILY_LOSS > 0
        assert settings.MAX_POSITIONS > 0
        assert 0 < settings.MAX_DRAWDOWN_PCT <= 100
        assert 0 < settings.DEFAULT_STOP_LOSS_PCT < settings.DEFAULT_TARGET_PROFIT_PCT
    
    def test_required_settings_present(self):
        """Test that all required settings are present."""
        # These should be set in environment
        required_settings = [
            "SECRET_KEY",
            "DATABASE_URL",
            "REDIS_URL",
            "CELERY_BROKER_URL",
            "CELERY_RESULT_BACKEND",
            "JWT_SECRET_KEY",
            "ENCRYPTION_KEY",
            "STATIC_IP",
        ]
        
        for setting in required_settings:
            assert hasattr(settings, setting), f"Required setting {setting} is missing"
            assert getattr(settings, setting) is not None, f"Required setting {setting} is None"
