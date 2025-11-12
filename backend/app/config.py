"""
Application Configuration
Centralized configuration management using Pydantic Settings
"""

from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field, validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    APP_NAME: str = "TradeDesk"
    APP_ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str
    APP_DOMAIN: Optional[str] = None    
    APP_URL: Optional[str] = None       
    
    # Server
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    WORKERS: int = 4
    
    # Database
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 0
    
    # Redis
    REDIS_URL: str
    REDIS_CACHE_TTL: int = 3600
    
    # Celery
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str
    
    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Encryption
    ENCRYPTION_KEY: str
    
    # SEBI Compliance
    STATIC_IP: str
    OPS_LIMIT: int = 10
    MAX_DAILY_TRADES: int = 50
    
    # Zerodha
    ZERODHA_API_KEY: Optional[str] = None
    ZERODHA_API_SECRET: Optional[str] = None
    ZERODHA_REDIRECT_URL: Optional[str] = None
    ZERODHA_AUTO_REFRESH_ENABLED: bool = True
    ZERODHA_REFRESH_INTERVAL_MINUTES: int = 15
    ZERODHA_REFRESH_EXPIRY_BUFFER_MINUTES: int = 60
    
    # Groww
    GROWW_API_KEY: Optional[str] = None
    GROWW_API_SECRET: Optional[str] = None
    GROWW_TOTP_SECRET: Optional[str] = None
    
    # Risk Management
    MAX_POSITION_VALUE: float = 50000
    MAX_DAILY_LOSS: float = 5000
    MAX_POSITIONS: int = 5
    MAX_DRAWDOWN_PCT: float = 15.0
    DEFAULT_STOP_LOSS_PCT: float = 2.0
    DEFAULT_TARGET_PROFIT_PCT: float = 4.0
    
    # Monitoring
    PROMETHEUS_PORT: int = 9090
    GRAFANA_PORT: int = 3001
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "/var/log/tradedesk/app.log"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.APP_ENV == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.APP_ENV == "development"


# Global settings instance
settings = Settings()

