"""
Position Model
Current position tracking and P&L calculation
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, DECIMAL, BigInteger, Date
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class Position(Base):
    """
    Position model for tracking open and closed positions
    
    Tracks both intraday and delivery positions
    """
    __tablename__ = "positions"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign Keys
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    broker_connection_id = Column(Integer, ForeignKey("broker_connections.id", ondelete="CASCADE"), nullable=False)
    strategy_instance_id = Column(Integer, ForeignKey("strategy_instances.id"))
    
    # Position Details
    exchange = Column(String(10), nullable=False)
    tradingsymbol = Column(String(50), nullable=False, index=True)
    instrument_token = Column(BigInteger)
    product = Column(String(10), nullable=False)  # CNC, MIS, NRML
    
    quantity = Column(Integer, nullable=False)  # Net quantity (positive for long, negative for short)
    average_price = Column(DECIMAL(12, 2), nullable=False)
    
    # P&L
    last_price = Column(DECIMAL(12, 2))
    pnl = Column(DECIMAL(15, 2))
    unrealised_pnl = Column(DECIMAL(15, 2))
    realised_pnl = Column(DECIMAL(15, 2))
    
    # Timestamps
    snapshot_date = Column(Date, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="positions")
    broker_connection = relationship("BrokerConnection", back_populates="positions")
    strategy_instance = relationship("StrategyInstance", back_populates="positions")
    
    def __repr__(self):
        return f"<Position(id={self.id}, symbol={self.tradingsymbol}, qty={self.quantity}, pnl={self.pnl})>"

