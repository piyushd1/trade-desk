"""
Audit Logging Endpoints
SEBI-compliant audit log access and querying
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime

from app.database import get_db
from app.services.audit_service import audit_service

router = APIRouter()


@router.get("/audit/logs")
async def get_audit_logs(
    action: Optional[str] = Query(default=None, description="Filter by action"),
    user_id: Optional[int] = Query(default=None, description="Filter by user ID"),
    entity_type: Optional[str] = Query(default=None, description="Filter by entity type"),
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(default=0, ge=0, description="Offset for pagination"),
    db: AsyncSession = Depends(get_db)
):
    """
    Query audit logs with filters
    
    SEBI Compliance:
    - Read-only access to immutable audit records
    - Supports filtering and pagination for compliance reporting
    
    Returns:
        dict: Paginated list of audit log entries
    """
    logs = await audit_service.get_audit_logs(
        action=action,
        user_id=user_id,
        entity_type=entity_type,
        limit=limit,
        offset=offset,
        db=db
    )
    
    return {
        "status": "success",
        "count": len(logs),
        "limit": limit,
        "offset": offset,
        "logs": [
            {
                "id": log.id,
                "user_id": log.user_id,
                "username": log.username,
                "action": log.action,
                "entity_type": log.entity_type,
                "entity_id": log.entity_id,
                "details": log.details,
                "ip_address": log.ip_address,
                "user_agent": log.user_agent,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ]
    }


@router.get("/audit/logs/{log_id}")
async def get_audit_log(
    log_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific audit log entry by ID
    
    Returns:
        dict: Audit log entry details
    """
    from app.models.audit import AuditLog
    from sqlalchemy import select
    
    result = await db.execute(
        select(AuditLog).where(AuditLog.id == log_id)
    )
    log = result.scalar_one_or_none()
    
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit log with ID {log_id} not found"
        )
    
    return {
        "status": "success",
        "log": {
            "id": log.id,
            "user_id": log.user_id,
            "username": log.username,
            "action": log.action,
            "entity_type": log.entity_type,
            "entity_id": log.entity_id,
            "details": log.details,
            "ip_address": log.ip_address,
            "user_agent": log.user_agent,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
    }


@router.get("/system/events")
async def get_system_events(
    event_type: Optional[str] = Query(default=None, description="Filter by event type"),
    severity: Optional[str] = Query(default=None, description="Filter by severity"),
    component: Optional[str] = Query(default=None, description="Filter by component"),
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(default=0, ge=0, description="Offset for pagination"),
    db: AsyncSession = Depends(get_db)
):
    """
    Query system events with filters
    
    Returns:
        dict: Paginated list of system event entries
    """
    events = await audit_service.get_system_events(
        event_type=event_type,
        severity=severity,
        component=component,
        limit=limit,
        offset=offset,
        db=db
    )
    
    return {
        "status": "success",
        "count": len(events),
        "limit": limit,
        "offset": offset,
        "events": [
            {
                "id": event.id,
                "event_type": event.event_type,
                "severity": event.severity,
                "component": event.component,
                "message": event.message,
                "details": event.details,
                "stack_trace": event.stack_trace,
                "created_at": event.created_at.isoformat() if event.created_at else None,
            }
            for event in events
        ]
    }


@router.get("/system/events/{event_id}")
async def get_system_event(
    event_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific system event by ID
    
    Returns:
        dict: System event details
    """
    from app.models.audit import SystemEvent
    from sqlalchemy import select
    
    result = await db.execute(
        select(SystemEvent).where(SystemEvent.id == event_id)
    )
    event = result.scalar_one_or_none()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"System event with ID {event_id} not found"
        )
    
    return {
        "status": "success",
        "event": {
            "id": event.id,
            "event_type": event.event_type,
            "severity": event.severity,
            "component": event.component,
            "message": event.message,
            "details": event.details,
            "stack_trace": event.stack_trace,
            "created_at": event.created_at.isoformat() if event.created_at else None,
        }
    }

