"""
Risk Configuration Model
User-specific and system-wide risk limits
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class RiskConfig(Base):
    """
    Risk configuration for users and system
    
    Stores risk limits that can be configured per user or system-wide.
    All limits are enforced before order placement.
    """
    __tablename__ = "risk_configs"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # User-specific or system-wide
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)  # NULL = system-wide
    
    # Position Limits
    max_position_value = Column(Float, nullable=False, default=50000.0)  # Max value per position (₹)
    max_positions = Column(Integer, nullable=False, default=5)  # Max concurrent positions
    max_position_pct = Column(Float, nullable=False, default=25.0)  # Max % of portfolio per position
    
    # Order Limits
    max_order_value = Column(Float, nullable=False, default=100000.0)  # Max value per order (₹)
    max_orders_per_day = Column(Integer, nullable=False, default=50)  # Max orders per day
    ops_limit = Column(Integer, nullable=False, default=10)  # Orders per second limit
    
    # Loss Limits
    max_daily_loss = Column(Float, nullable=False, default=5000.0)  # Max daily loss (₹)
    max_weekly_loss = Column(Float, nullable=False, default=15000.0)  # Max weekly loss (₹)
    max_monthly_loss = Column(Float, nullable=False, default=50000.0)  # Max monthly loss (₹)
    max_drawdown_pct = Column(Float, nullable=False, default=15.0)  # Max drawdown %
    
    # Stop Loss & Target
    default_stop_loss_pct = Column(Float, nullable=False, default=2.0)  # Default stop loss %
    default_target_profit_pct = Column(Float, nullable=False, default=4.0)  # Default target %
    enforce_stop_loss = Column(Boolean, nullable=False, default=True)  # Require stop loss on all orders
    
    # Trading Hours
    allow_pre_market = Column(Boolean, nullable=False, default=False)
    allow_after_market = Column(Boolean, nullable=False, default=False)
    
    # Kill Switch
    trading_enabled = Column(Boolean, nullable=False, default=True)  # Master kill switch
    
    # Additional Settings
    additional_limits = Column(JSON, nullable=True)  # Extensible limits (sector exposure, etc.)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="risk_config")
    
    def __repr__(self):
        scope = f"user_id={self.user_id}" if self.user_id else "system-wide"
        return f"<RiskConfig({scope}, trading_enabled={self.trading_enabled})>"


class DailyRiskMetrics(Base):
    """
    Daily risk metrics tracking
    
    Tracks daily trading activity and P&L for risk limit enforcement.
    Reset daily at market open.
    """
    __tablename__ = "daily_risk_metrics"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # User
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Date
    trading_date = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Order Metrics
    orders_placed = Column(Integer, nullable=False, default=0)
    orders_executed = Column(Integer, nullable=False, default=0)
    orders_rejected = Column(Integer, nullable=False, default=0)
    
    # Position Metrics
    max_positions_held = Column(Integer, nullable=False, default=0)
    current_positions = Column(Integer, nullable=False, default=0)
    
    # P&L Metrics
    realized_pnl = Column(Float, nullable=False, default=0.0)  # Closed positions P&L
    unrealized_pnl = Column(Float, nullable=False, default=0.0)  # Open positions P&L
    total_pnl = Column(Float, nullable=False, default=0.0)  # realized + unrealized
    
    # Loss Tracking
    max_loss_hit = Column(Float, nullable=False, default=0.0)  # Worst loss during the day
    loss_limit_breached = Column(Boolean, nullable=False, default=False)
    
    # Volume Metrics
    total_turnover = Column(Float, nullable=False, default=0.0)  # Total value traded
    
    # Risk Breaches
    risk_breaches = Column(Integer, nullable=False, default=0)  # Number of risk limit breaches
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<DailyRiskMetrics(user_id={self.user_id}, date={self.trading_date}, pnl={self.total_pnl})>"

