"""
Broker Session Model
Stores broker access tokens securely for each user
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, UniqueConstraint
from sqlalchemy.sql import func

from app.database import Base


class BrokerSession(Base):
    """
    Broker session records storing encrypted tokens per user per broker
    """
    __tablename__ = "broker_sessions"
    __table_args__ = (
        UniqueConstraint("user_identifier", "broker", name="uq_broker_sessions_user_broker"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_identifier = Column(String(100), nullable=False, index=True)
    broker = Column(String(50), nullable=False, index=True)
    access_token_encrypted = Column(Text, nullable=False)
    refresh_token_encrypted = Column(Text)
    public_token = Column(String(100))
    status = Column(String(20), default="active")
    meta = Column(JSON)
    expires_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<BrokerSession(user={self.user_identifier}, broker={self.broker}, status={self.status})>"
