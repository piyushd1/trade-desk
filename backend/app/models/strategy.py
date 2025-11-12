"""
Strategy Models
Strategy definitions and running instances
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, DECIMAL, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class Strategy(Base):
    """
    Trading strategy definition
    
    Stores strategy metadata, file path, parameters, and performance metrics
    """
    __tablename__ = "strategies"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Strategy Info
    name = Column(String(100), unique=True, nullable=False, index=True)
    display_name = Column(String(255), nullable=False)
    description = Column(Text)
    file_path = Column(String(500), nullable=False)
    file_hash = Column(String(64))  # SHA-256 hash for change detection
    version = Column(String(20), default="1.0.0")
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_system_strategy = Column(Boolean, default=False, nullable=False)
    
    # Configuration (JSON)
    parameters = Column(JSON)  # Default parameters
    
    # Strategy Type
    strategy_type = Column(String(50))  # 'momentum', 'mean_reversion', etc.
    timeframe = Column(String(20))  # '1min', '5min', '15min', 'daily'
    instruments = Column(JSON)  # List of instruments
    
    # Risk Parameters
    max_position_size = Column(Integer)
    max_loss_per_trade = Column(DECIMAL(10, 2))
    max_daily_trades = Column(Integer)
    
    # Performance Tracking
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    total_pnl = Column(DECIMAL(15, 2), default=0)
    
    # Ownership
    created_by = Column(Integer, ForeignKey("users.id"))
    last_modified_by = Column(Integer, ForeignKey("users.id"))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    instances = relationship("StrategyInstance", back_populates="strategy", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Strategy(id={self.id}, name={self.name}, active={self.is_active})>"


class StrategyInstance(Base):
    """
    Running instance of a strategy
    
    Each user can run multiple instances of the same strategy with different parameters
    """
    __tablename__ = "strategy_instances"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign Keys
    strategy_id = Column(Integer, ForeignKey("strategies.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    broker_connection_id = Column(Integer, ForeignKey("broker_connections.id", ondelete="CASCADE"), nullable=False)
    
    # Instance Info
    instance_name = Column(String(255), nullable=False)
    mode = Column(String(20), nullable=False)  # 'backtest', 'paper', 'live'
    
    # Parameters (override defaults)
    parameters = Column(JSON)
    
    # State
    is_running = Column(Boolean, default=False, nullable=False, index=True)
    started_at = Column(DateTime(timezone=True))
    stopped_at = Column(DateTime(timezone=True))
    
    # Performance
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    total_pnl = Column(DECIMAL(15, 2), default=0)
    current_drawdown = Column(DECIMAL(10, 2), default=0)
    max_drawdown = Column(DECIMAL(10, 2), default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    strategy = relationship("Strategy", back_populates="instances")
    user = relationship("User", back_populates="strategy_instances")
    orders = relationship("Order", back_populates="strategy_instance")
    positions = relationship("Position", back_populates="strategy_instance")
    
    def __repr__(self):
        return f"<StrategyInstance(id={self.id}, name={self.instance_name}, mode={self.mode}, running={self.is_running})>"

