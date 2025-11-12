"""
Audit Service
Handles audit logging for SEBI compliance and system monitoring
"""

import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.audit import AuditLog, RiskBreachLog, SystemEvent

logger = logging.getLogger(__name__)


class AuditService:
    """
    Service for logging audit events, risk breaches, and system events
    
    SEBI Compliance:
    - All audit logs are immutable (insert-only)
    - 7-year retention requirement
    - Complete audit trail for all operations
    """
    
    @staticmethod
    async def log_event(
        action: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        db: Optional[AsyncSession] = None
    ) -> AuditLog:
        """
        Log an audit event
        
        Args:
            action: Action performed (e.g., 'oauth_initiate', 'token_refresh', 'order_place')
            entity_type: Type of entity affected (e.g., 'order', 'strategy', 'user')
            entity_id: ID of the entity affected
            details: Additional details as JSON-serializable dict
            user_id: User ID (if applicable)
            username: Username (if applicable)
            ip_address: IP address of the request
            user_agent: User agent string
            db: Database session (if None, creates a new one)
        
        Returns:
            AuditLog: Created audit log entry
        """
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True
        
        try:
            audit_log = AuditLog(
                user_id=user_id,
                username=username,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                details=details or {},
                ip_address=ip_address,
                user_agent=user_agent,
                created_at=datetime.now(timezone.utc)
            )
            
            db.add(audit_log)
            await db.commit()
            await db.refresh(audit_log)
            
            logger.debug(f"Audit log created: {action} by {username or 'system'}")
            
            return audit_log
        
        except Exception as e:
            logger.error(f"Failed to create audit log: {e}", exc_info=True)
            await db.rollback()
            raise
        finally:
            if should_close:
                await db.close()
    
    @staticmethod
    async def log_system_event(
        event_type: str,
        severity: str,
        message: str,
        component: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        stack_trace: Optional[str] = None,
        db: Optional[AsyncSession] = None
    ) -> SystemEvent:
        """
        Log a system event
        
        Args:
            event_type: Type of event ('startup', 'shutdown', 'error', 'warning', 'info')
            severity: Severity level ('critical', 'error', 'warning', 'info', 'debug')
            message: Event message
            component: Component that generated the event
            details: Additional details as JSON-serializable dict
            stack_trace: Stack trace (for errors)
            db: Database session (if None, creates a new one)
        
        Returns:
            SystemEvent: Created system event entry
        """
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True
        
        try:
            system_event = SystemEvent(
                event_type=event_type,
                severity=severity,
                component=component,
                message=message,
                details=details or {},
                stack_trace=stack_trace,
                created_at=datetime.now(timezone.utc)
            )
            
            db.add(system_event)
            await db.commit()
            await db.refresh(system_event)
            
            log_level = getattr(logging, severity.upper(), logging.INFO)
            logger.log(log_level, f"System event [{component}]: {message}")
            
            return system_event
        
        except Exception as e:
            logger.error(f"Failed to create system event: {e}", exc_info=True)
            await db.rollback()
            raise
        finally:
            if should_close:
                await db.close()
    
    @staticmethod
    async def log_risk_breach(
        breach_type: str,
        breach_details: Dict[str, Any],
        action_taken: Optional[str] = None,
        user_id: Optional[int] = None,
        strategy_instance_id: Optional[int] = None,
        db: Optional[AsyncSession] = None
    ) -> RiskBreachLog:
        """
        Log a risk breach
        
        Args:
            breach_type: Type of breach ('position_limit', 'loss_limit', 'ops_limit', etc.)
            breach_details: Details of the breach as JSON-serializable dict
            action_taken: Action taken in response ('order_rejected', 'strategy_stopped', etc.)
            user_id: User ID (if applicable)
            strategy_instance_id: Strategy instance ID (if applicable)
            db: Database session (if None, creates a new one)
        
        Returns:
            RiskBreachLog: Created risk breach log entry
        """
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True
        
        try:
            risk_breach = RiskBreachLog(
                user_id=user_id,
                strategy_instance_id=strategy_instance_id,
                breach_type=breach_type,
                breach_details=breach_details,
                action_taken=action_taken,
                created_at=datetime.now(timezone.utc)
            )
            
            db.add(risk_breach)
            await db.commit()
            await db.refresh(risk_breach)
            
            logger.warning(f"Risk breach logged: {breach_type} for user {user_id}, action: {action_taken}")
            
            return risk_breach
        
        except Exception as e:
            logger.error(f"Failed to create risk breach log: {e}", exc_info=True)
            await db.rollback()
            raise
        finally:
            if should_close:
                await db.close()
    
    @staticmethod
    async def get_audit_logs(
        action: Optional[str] = None,
        user_id: Optional[int] = None,
        entity_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        db: Optional[AsyncSession] = None
    ) -> list[AuditLog]:
        """
        Query audit logs with filters
        
        Args:
            action: Filter by action
            user_id: Filter by user ID
            entity_type: Filter by entity type
            limit: Maximum number of results
            offset: Offset for pagination
            db: Database session (if None, creates a new one)
        
        Returns:
            list: List of AuditLog entries
        """
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True
        
        try:
            query = select(AuditLog)
            
            if action:
                query = query.where(AuditLog.action == action)
            if user_id:
                query = query.where(AuditLog.user_id == user_id)
            if entity_type:
                query = query.where(AuditLog.entity_type == entity_type)
            
            query = query.order_by(AuditLog.created_at.desc()).limit(limit).offset(offset)
            
            result = await db.execute(query)
            logs = result.scalars().all()
            
            return list(logs)
        
        finally:
            if should_close:
                await db.close()
    
    @staticmethod
    async def get_system_events(
        event_type: Optional[str] = None,
        severity: Optional[str] = None,
        component: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        db: Optional[AsyncSession] = None
    ) -> list[SystemEvent]:
        """
        Query system events with filters
        
        Args:
            event_type: Filter by event type
            severity: Filter by severity
            component: Filter by component
            limit: Maximum number of results
            offset: Offset for pagination
            db: Database session (if None, creates a new one)
        
        Returns:
            list: List of SystemEvent entries
        """
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True
        
        try:
            query = select(SystemEvent)
            
            if event_type:
                query = query.where(SystemEvent.event_type == event_type)
            if severity:
                query = query.where(SystemEvent.severity == severity)
            if component:
                query = query.where(SystemEvent.component == component)
            
            query = query.order_by(SystemEvent.created_at.desc()).limit(limit).offset(offset)
            
            result = await db.execute(query)
            events = result.scalars().all()
            
            return list(events)
        
        finally:
            if should_close:
                await db.close()


# Global instance
audit_service = AuditService()

