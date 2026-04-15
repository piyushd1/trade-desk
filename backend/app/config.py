"""
Application Configuration Module

This module provides centralized configuration management for the TradeDesk application
using Pydantic Settings. All configuration values are loaded from environment variables
with sensible defaults where appropriate.

Key Features:
- Type-safe configuration with Pydantic validation
- Environment-based configuration loading
- Grouped settings by functionality
- SEBI compliance settings included
"""


from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    This class defines all configuration parameters needed by the application,
    grouped by functionality. Settings are loaded from environment variables
    and validated using Pydantic.

    Environment variables should be prefixed with the setting name in uppercase.
    For example: APP_NAME, DATABASE_URL, etc.
    """

    # ===== Application Settings =====
    APP_NAME: str = Field(default="TradeDesk", description="Application name used in logs and UI")
    APP_ENV: str = Field(
        default="development", description="Environment: development, staging, production"
    )
    DEBUG: bool = Field(default=True, description="Enable debug mode (disable in production)")
    SECRET_KEY: str = Field(..., description="Secret key for session management (required)")
    APP_DOMAIN: str | None = Field(
        default=None, description="Application domain (e.g., example.com)"
    )
    APP_URL: str | None = Field(
        default=None, description="Full application URL (e.g., https://example.com)"
    )
    API_BASE_URL: str = Field(
        default="http://localhost:8000", description="Backend API base URL"
    )
    FRONTEND_URL: str = Field(
        default="http://localhost:3000", description="Frontend application URL"
    )

    # ===== Server Configuration =====
    API_HOST: str = Field(default="0.0.0.0", description="API server host binding")
    API_PORT: int = Field(default=8000, description="API server port")
    WORKERS: int = Field(default=4, description="Number of worker processes")

    # ===== Database Configuration =====
    DATABASE_URL: str = Field(..., description="Database connection URL (required)")
    DATABASE_POOL_SIZE: int = Field(default=20, description="Database connection pool size")
    DATABASE_MAX_OVERFLOW: int = Field(
        default=0, description="Maximum overflow connections above pool size"
    )

    # ===== Redis Configuration =====
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL for caching (optional in development, required in production)",
    )
    REDIS_CACHE_TTL: int = Field(default=3600, description="Default cache TTL in seconds (1 hour)")

    # ===== Celery Configuration =====
    CELERY_BROKER_URL: str = Field(
        default="redis://localhost:6379/1",
        description="Celery broker URL (optional in development, required in production)",
    )
    CELERY_RESULT_BACKEND: str = Field(
        default="redis://localhost:6379/2",
        description="Celery result backend URL (optional in development, required in production)",
    )

    # ===== JWT Authentication =====
    JWT_SECRET_KEY: str = Field(..., description="JWT signing key (required)")
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT signing algorithm")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=15, description="Access token expiration time in minutes"
    )
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default=7, description="Refresh token expiration time in days"
    )

    # ===== Data Encryption =====
    ENCRYPTION_KEY: str = Field(
        ..., description="Fernet encryption key for sensitive data (required)"
    )

    # ===== Default Admin User Configuration =====
    ADMIN_USERNAME: str | None = Field(
        default=None, description="Default admin username for initial setup (optional)"
    )
    ADMIN_EMAIL: str | None = Field(
        default=None, description="Default admin email for initial setup (optional)"
    )
    ADMIN_PASSWORD: str | None = Field(
        default=None, description="Default admin password for initial setup (optional)"
    )

    # ===== Test Environment Configuration =====
    TEST_DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///:memory:", description="Test database URL"
    )
    TEST_SYNC_DATABASE_URL: str = Field(
        default="sqlite:///:memory:", description="Synchronous test database URL"
    )
    TEST_USER_USERNAME: str = Field(
        default="testuser", description="Test user username"
    )
    TEST_USER_PASSWORD: str = Field(
        default="testpass123", description="Test user password"
    )
    TEST_ADMIN_USERNAME: str = Field(
        default="admin", description="Test admin username"
    )
    TEST_ADMIN_PASSWORD: str = Field(
        default="admin123", description="Test admin password"
    )

    # ===== SEBI Compliance Settings =====
    STATIC_IP: str = Field(
        default="0.0.0.0",
        description="Static IP address for SEBI compliance (set to your actual static IP in production)",
    )
    OPS_LIMIT: int = Field(default=10, description="Operations per second limit (SEBI requirement)")
    MAX_DAILY_TRADES: int = Field(
        default=50, description="Maximum trades per day (SEBI requirement)"
    )

    # ===== Zerodha Broker Integration =====
    ZERODHA_API_KEY: str | None = Field(default=None, description="Zerodha API key")
    ZERODHA_API_SECRET: str | None = Field(default=None, description="Zerodha API secret")
    ZERODHA_REDIRECT_URL: str | None = Field(
        default=None, description="OAuth redirect URL for Zerodha"
    )
    ZERODHA_AUTO_REFRESH_ENABLED: bool = Field(
        default=True, description="Enable automatic token refresh"
    )
    ZERODHA_REFRESH_INTERVAL_MINUTES: int = Field(
        default=15, description="Token refresh check interval"
    )
    ZERODHA_REFRESH_EXPIRY_BUFFER_MINUTES: int = Field(
        default=60, description="Buffer time before token expiry to refresh"
    )
    ZERODHA_USER_IDENTIFIER: str | None = Field(
        default=None, description="Default Zerodha user identifier (e.g., YOUR_USER_IDENTIFIER). Can be overridden per request. Set in .env file."
    )

    # ===== IndStocks (IndMoney) Broker Integration =====
    # IndStocks uses a static access token pasted from web.indstocks.com rather
    # than OAuth. The token expires every 24 hours and has no programmatic
    # refresh, so the user must paste a fresh token daily. See
    # backend/app/brokers/indstocks.py for the full adapter docstring.
    INDSTOCKS_ACCESS_TOKEN: str | None = Field(
        default=None,
        description="IndStocks static bearer token from web.indstocks.com. "
                    "Expires every 24 hours. Paste fresh token daily. "
                    "Do NOT include a 'Bearer ' prefix — IndStocks uses the raw token.",
    )
    INDSTOCKS_USER_IDENTIFIER: str | None = Field(
        default=None,
        description="Default IndStocks user identifier for routing broker_sessions rows.",
    )

    # ===== Groww Broker Integration =====
    GROWW_API_KEY: str | None = Field(default=None, description="Groww API key")
    GROWW_API_SECRET: str | None = Field(default=None, description="Groww API secret")
    GROWW_TOTP_SECRET: str | None = Field(default=None, description="Groww TOTP secret for 2FA")

    # ===== Yahoo Finance / Fundamentals Configuration =====
    YFINANCE_CACHE_ENABLED: bool = Field(
        default=True, description="Enable database caching for yfinance data"
    )
    YFINANCE_CACHE_TTL_HOURS: int = Field(
        default=24, description="Cache TTL for fundamental data in hours"
    )
    YFINANCE_RATE_LIMIT_PER_SECOND: float = Field(
        default=0.9, description="Rate limit for yfinance API calls (requests per second)"
    )
    FUNDAMENTALS_UPDATE_THRESHOLD_HOURS: int = Field(
        default=24, description="Minimum hours between fundamental data updates"
    )

    # ===== Risk Management Parameters =====
    MAX_POSITION_VALUE: float = Field(
        default=50000.0, description="Maximum value per position in INR"
    )
    MAX_DAILY_LOSS: float = Field(default=5000.0, description="Maximum allowed daily loss in INR")
    MAX_POSITIONS: int = Field(default=5, description="Maximum concurrent positions")
    MAX_DRAWDOWN_PCT: float = Field(
        default=15.0, description="Maximum portfolio drawdown percentage"
    )
    DEFAULT_STOP_LOSS_PCT: float = Field(default=2.0, description="Default stop loss percentage")
    DEFAULT_TARGET_PROFIT_PCT: float = Field(
        default=4.0, description="Default target profit percentage"
    )

    # ===== Monitoring Configuration =====
    PROMETHEUS_PORT: int = Field(default=9090, description="Prometheus metrics port")
    GRAFANA_PORT: int = Field(default=3001, description="Grafana dashboard port")

    # ===== Logging Configuration =====
    LOG_LEVEL: str = Field(
        default="INFO", description="Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL"
    )
    LOG_FILE: str = Field(default="/var/log/tradedesk/app.log", description="Log file path")

    class Config:
        """Pydantic configuration"""

        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore unknown environment variables (e.g., from system env or .env extras)

    @field_validator("APP_ENV")
    @classmethod
    def validate_app_env(cls, v: str) -> str:
        """Validate application environment"""
        valid_envs = {"development", "staging", "production"}
        if v not in valid_envs:
            raise ValueError(f"APP_ENV must be one of: {valid_envs}")
        return v

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate logging level"""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of: {valid_levels}")
        return v.upper()

    @property
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.APP_ENV == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.APP_ENV == "development"

    @property
    def is_staging(self) -> bool:
        """Check if running in staging environment"""
        return self.APP_ENV == "staging"

    @property
    def jwt_access_token_expire_minutes(self) -> int:
        """Get JWT access token expiration in minutes"""
        # Alias for backward compatibility
        return self.JWT_ACCESS_TOKEN_EXPIRE_MINUTES

    @property
    def jwt_refresh_token_expire_minutes(self) -> int:
        """Get JWT refresh token expiration in minutes"""
        return self.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60

    @property
    def access_token_expire_minutes(self) -> int:
        """Alias for JWT access token expiration"""
        return self.JWT_ACCESS_TOKEN_EXPIRE_MINUTES

    @property
    def refresh_token_expire_minutes(self) -> int:
        """Alias for JWT refresh token expiration in minutes"""
        return self.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60

    @property
    def algorithm(self) -> str:
        """Alias for JWT algorithm"""
        return self.JWT_ALGORITHM


# Global settings instance - instantiated once on module import
settings = Settings()

# Aliases for backward compatibility
ACCESS_TOKEN_EXPIRE_MINUTES = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_MINUTES = settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60
ALGORITHM = settings.JWT_ALGORITHM
