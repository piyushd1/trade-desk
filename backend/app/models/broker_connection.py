"""
Broker Connection Model
OAuth tokens and API credentials for broker integrations
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class BrokerType(str, enum.Enum):
    """Supported broker types"""
    ZERODHA = "zerodha"
    GROWW = "groww"


class BrokerConnection(Base):
    """
    Broker API connection and credentials
    
    SEBI Compliance:
    - Stores algo_identifier for order tagging
    - Tracks registration date for audit
    - OAuth tokens encrypted at rest
    """
    __tablename__ = "broker_connections"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign Keys
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Broker Info
    broker = Column(SQLEnum(BrokerType), nullable=False)
    api_key = Column(String(255), nullable=False)
    api_secret_encrypted = Column(Text, nullable=False)  # Encrypted at rest
    
    # OAuth Tokens
    access_token = Column(Text)  # Encrypted
    access_token_expires_at = Column(DateTime(timezone=True))
    refresh_token = Column(Text)  # Encrypted
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # SEBI Compliance
    algo_identifier = Column(String(50), unique=True)  # Exchange-provided algo ID
    algo_registered_at = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="broker_connections")
    orders = relationship("Order", back_populates="broker_connection")
    positions = relationship("Position", back_populates="broker_connection")
    
    def __repr__(self):
        return f"<BrokerConnection(id={self.id}, broker={self.broker}, user_id={self.user_id})>"

