"""
User Model
Core user authentication and profile management
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class UserRole(str, enum.Enum):
    """User role enumeration"""
    ADMIN = "admin"
    TRADER = "trader"
    VIEWER = "viewer"


class User(Base):
    """
    User model for authentication and authorization
    
    SEBI Compliance:
    - Stores 2FA secret for two-factor authentication
    - Records static IP for API access whitelisting
    - Tracks last login for audit purposes
    """
    __tablename__ = "users"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Authentication
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # Profile
    full_name = Column(String(255))
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.TRADER)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # SEBI Compliance
    totp_secret = Column(String(32))  # For 2FA
    static_ip = Column(String(45))  # IPv4 or IPv6
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_login_at = Column(DateTime(timezone=True))
    
    # Relationships
    broker_connections = relationship("BrokerConnection", back_populates="user", cascade="all, delete-orphan")
    strategy_instances = relationship("StrategyInstance", back_populates="user", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="user", cascade="all, delete-orphan")
    positions = relationship("Position", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, role={self.role})>"

