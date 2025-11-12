"""
Order and Trade Models
Order management and trade execution tracking
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, DECIMAL, BigInteger
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class Order(Base):
    """
    Order model for tracking all orders
    
    SEBI Compliance:
    - algo_identifier mandatory for all algo orders
    - Complete audit trail with timestamps
    - Order tagging for exchange surveillance
    """
    __tablename__ = "orders"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Order Identity
    order_id = Column(String(50), unique=True, nullable=False, index=True)  # Broker's order ID
    parent_order_id = Column(String(50))  # For bracket/cover orders
    
    # Foreign Keys
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    broker_connection_id = Column(Integer, ForeignKey("broker_connections.id"), nullable=False)
    strategy_instance_id = Column(Integer, ForeignKey("strategy_instances.id"))
    
    # SEBI Compliance
    algo_identifier = Column(String(50), nullable=False, index=True)  # SEBI algo tag
    
    # Order Details
    exchange = Column(String(10), nullable=False)  # NSE, BSE, NFO, etc.
    tradingsymbol = Column(String(50), nullable=False, index=True)
    instrument_token = Column(BigInteger)
    
    transaction_type = Column(String(10), nullable=False)  # BUY, SELL
    order_type = Column(String(10), nullable=False)  # MARKET, LIMIT, SL, SL-M
    product = Column(String(10), nullable=False)  # CNC, MIS, NRML, MTF
    variety = Column(String(20), nullable=False)  # regular, co, amo, iceberg, auction
    
    quantity = Column(Integer, nullable=False)
    price = Column(DECIMAL(12, 2))
    trigger_price = Column(DECIMAL(12, 2))
    disclosed_quantity = Column(Integer)
    
    # Status
    status = Column(String(20), nullable=False, index=True)  # PENDING, OPEN, COMPLETE, REJECTED, CANCELLED
    status_message = Column(Text)
    
    # Execution
    filled_quantity = Column(Integer, default=0)
    pending_quantity = Column(Integer)
    cancelled_quantity = Column(Integer, default=0)
    average_price = Column(DECIMAL(12, 2))
    
    # Timestamps
    placed_at = Column(DateTime(timezone=True), nullable=False)
    exchange_timestamp = Column(DateTime(timezone=True))
    last_modified_at = Column(DateTime(timezone=True))
    
    # Audit
    placed_by = Column(String(50))  # 'system', 'manual', 'strategy_name'
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="orders")
    broker_connection = relationship("BrokerConnection", back_populates="orders")
    strategy_instance = relationship("StrategyInstance", back_populates="orders")
    trades = relationship("Trade", back_populates="order", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Order(id={self.id}, order_id={self.order_id}, symbol={self.tradingsymbol}, status={self.status})>"


class Trade(Base):
    """
    Trade execution model
    
    Tracks individual trade fills (an order can have multiple fills)
    """
    __tablename__ = "trades"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Trade Identity
    trade_id = Column(String(50), unique=True, nullable=False, index=True)  # Broker's trade ID
    order_id = Column(String(50), ForeignKey("orders.order_id"), nullable=False)
    
    # Trade Details
    exchange = Column(String(10), nullable=False)
    tradingsymbol = Column(String(50), nullable=False)
    instrument_token = Column(BigInteger)
    
    transaction_type = Column(String(10), nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(DECIMAL(12, 2), nullable=False)
    
    # Timestamps
    exchange_timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    order = relationship("Order", back_populates="trades")
    
    def __repr__(self):
        return f"<Trade(id={self.id}, trade_id={self.trade_id}, symbol={self.tradingsymbol}, qty={self.quantity})>"

