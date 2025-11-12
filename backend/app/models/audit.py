"""
Audit and Compliance Models
Audit logging, risk breach tracking, and system events
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class AuditLog(Base):
    """
    Audit log for all critical operations
    
    SEBI Compliance:
    - 7-year retention requirement
    - Immutable records (no updates/deletes)
    - Complete audit trail for all algo orders
    """
    __tablename__ = "audit_logs"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Who
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    username = Column(String(50))
    
    # What
    action = Column(String(100), nullable=False, index=True)
    entity_type = Column(String(50))  # 'order', 'strategy', 'user', 'config', etc.
    entity_id = Column(String(100))
    
    # Details
    details = Column(JSON)  # Full audit trail data
    
    # Context
    ip_address = Column(String(45))
    user_agent = Column(Text)
    
    # When
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, action={self.action}, user_id={self.user_id})>"


class RiskBreachLog(Base):
    """
    Risk breach logging
    
    Tracks all risk limit breaches for monitoring and analysis
    """
    __tablename__ = "risk_breach_logs"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign Keys
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    strategy_instance_id = Column(Integer, ForeignKey("strategy_instances.id"))
    
    # Breach Details
    breach_type = Column(String(50), nullable=False, index=True)  # 'position_limit', 'loss_limit', 'ops_limit', etc.
    breach_details = Column(JSON, nullable=False)
    
    # Action Taken
    action_taken = Column(String(100))  # 'order_rejected', 'strategy_stopped', 'alert_sent', etc.
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    def __repr__(self):
        return f"<RiskBreachLog(id={self.id}, type={self.breach_type}, user_id={self.user_id})>"


class SystemEvent(Base):
    """
    System events and error logging
    
    Tracks system-level events, errors, and warnings
    """
    __tablename__ = "system_events"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Event Details
    event_type = Column(String(50), nullable=False, index=True)  # 'startup', 'shutdown', 'error', 'warning', 'info'
    severity = Column(String(20), nullable=False, index=True)  # 'critical', 'error', 'warning', 'info', 'debug'
    
    component = Column(String(100), index=True)  # 'strategy_engine', 'order_manager', 'data_fetcher', etc.
    
    message = Column(Text, nullable=False)
    details = Column(JSON)
    
    stack_trace = Column(Text)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    def __repr__(self):
        return f"<SystemEvent(id={self.id}, type={self.event_type}, severity={self.severity})>"

