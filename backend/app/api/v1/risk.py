"""
Risk Management Endpoints
Risk configuration, kill switch, and metrics monitoring
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import Optional
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel, Field

from app.database import get_db
from app.services.risk_manager import risk_manager
from app.services.audit_service import audit_service
from app.models import RiskConfig, DailyRiskMetrics, Position
from app.models.audit import RiskBreachLog
from app.models.user import User
from app.api.v1.auth import get_current_user_dependency
from sqlalchemy import func

router = APIRouter()


# Pydantic models for request/response
class RiskConfigUpdate(BaseModel):
    """Risk configuration update request"""
    max_position_value: Optional[float] = Field(None, gt=0, description="Max value per position (₹)")
    max_positions: Optional[int] = Field(None, gt=0, description="Max concurrent positions")
    max_position_pct: Optional[float] = Field(None, gt=0, le=100, description="Max % of portfolio per position")
    max_order_value: Optional[float] = Field(None, gt=0, description="Max value per order (₹)")
    max_orders_per_day: Optional[int] = Field(None, gt=0, description="Max orders per day")
    ops_limit: Optional[int] = Field(None, gt=0, le=100, description="Orders per second limit")
    max_daily_loss: Optional[float] = Field(None, gt=0, description="Max daily loss (₹)")
    max_weekly_loss: Optional[float] = Field(None, gt=0, description="Max weekly loss (₹)")
    max_monthly_loss: Optional[float] = Field(None, gt=0, description="Max monthly loss (₹)")
    max_drawdown_pct: Optional[float] = Field(None, gt=0, le=100, description="Max drawdown %")
    default_stop_loss_pct: Optional[float] = Field(None, gt=0, le=100, description="Default stop loss %")
    default_target_profit_pct: Optional[float] = Field(None, gt=0, le=100, description="Default target profit %")
    enforce_stop_loss: Optional[bool] = Field(None, description="Require stop loss on all orders")
    allow_pre_market: Optional[bool] = Field(None, description="Allow pre-market trading")
    allow_after_market: Optional[bool] = Field(None, description="Allow after-market trading")


class KillSwitchRequest(BaseModel):
    """Kill switch toggle request
    
    Emergency stop mechanism to immediately halt all trading.
    Requires JWT authentication.
    """
    enabled: bool = Field(
        ..., 
        description="Enable or disable trading. Set to false to activate kill switch (stop all trading).",
        example=False
    )
    reason: Optional[str] = Field(
        None, 
        description="Reason for toggling the kill switch (optional but recommended for audit trail)",
        example="Emergency stop - market volatility"
    )


class PreTradeCheckRequest(BaseModel):
    """Pre-trade check request
    
    Validates an order against all risk limits before placement.
    Requires JWT authentication.
    """
    user_id: int = Field(..., gt=0, description="Internal platform user ID", example=2)
    symbol: str = Field(..., min_length=1, description="Trading symbol (e.g., INFY, RELIANCE)", example="INFY")
    quantity: int = Field(..., gt=0, description="Order quantity (number of shares/lots)", example=10)
    price: float = Field(..., gt=0, description="Order price per unit (₹)", example=1500.0)


@router.get(
    "/risk/config",
    summary="Get Risk Configuration",
    description="""
    Get risk management configuration for a user or system-wide defaults.
    
    **Authentication:** Requires JWT Bearer token
    
    **Parameters:**
    - `user_id`: Optional. If provided, returns user-specific config. If null, returns system-wide config.
    
    **Returns:**
    - Risk limits (position limits, order limits, loss limits)
    - Trading hours settings
    - Stop loss defaults
    - Kill switch status
    
    **Example:**
    ```bash
    curl -H "Authorization: Bearer $ACCESS_TOKEN" \\
      "https://yourdomain.com/api/v1/risk/config?user_id=2"
    ```
    """
)
async def get_risk_config(
    current_user: User = Depends(get_current_user_dependency),
    user_id: Optional[int] = Query(
        default=None, 
        description="User ID (null for system-wide config). Example: 2",
        example=2
    ),
    db: AsyncSession = Depends(get_db)
):
    config = await risk_manager.get_risk_config(user_id=user_id, db=db)
    
    return {
        "status": "success",
        "config": {
            "id": config.id,
            "user_id": config.user_id,
            "max_position_value": config.max_position_value,
            "max_positions": config.max_positions,
            "max_position_pct": config.max_position_pct,
            "max_order_value": config.max_order_value,
            "max_orders_per_day": config.max_orders_per_day,
            "ops_limit": config.ops_limit,
            "max_daily_loss": config.max_daily_loss,
            "max_weekly_loss": config.max_weekly_loss,
            "max_monthly_loss": config.max_monthly_loss,
            "max_drawdown_pct": config.max_drawdown_pct,
            "default_stop_loss_pct": config.default_stop_loss_pct,
            "default_target_profit_pct": config.default_target_profit_pct,
            "enforce_stop_loss": config.enforce_stop_loss,
            "allow_pre_market": config.allow_pre_market,
            "allow_after_market": config.allow_after_market,
            "trading_enabled": config.trading_enabled,
            "additional_limits": config.additional_limits,
            "created_at": config.created_at.isoformat() if config.created_at else None,
            "updated_at": config.updated_at.isoformat() if config.updated_at else None,
        }
    }


@router.put("/risk/config")
async def update_risk_config(
    request: Request,
    config_update: RiskConfigUpdate,
    current_user: User = Depends(get_current_user_dependency),
    user_id: Optional[int] = Query(default=None, description="User ID (null for system-wide)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Update risk configuration
    
    Updates user-specific or system-wide risk limits.
    Only provided fields will be updated.
    
    Returns:
        dict: Updated risk configuration
    """
    # Get existing config
    config = await risk_manager.get_risk_config(user_id=user_id, db=db)
    
    # Track what changed
    changes = {}
    
    # Update fields
    update_data = config_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            old_value = getattr(config, field)
            if old_value != value:
                changes[field] = {"old": old_value, "new": value}
                setattr(config, field, value)
    
    if not changes:
        return {
            "status": "success",
            "message": "No changes made",
            "config_id": config.id
        }
    
    await db.commit()
    await db.refresh(config)
    
    # Log audit event
    await audit_service.log_event(
        action="risk_config_update",
        entity_type="risk_config",
        entity_id=str(config.id),
        details={
            "user_id": user_id,
            "changes": changes
        },
        username=current_user.username,
        user_id=current_user.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        db=db
    )
    
    return {
        "status": "success",
        "message": f"Risk configuration updated ({len(changes)} fields changed)",
        "changes": changes,
        "config_id": config.id
    }


@router.post(
    "/risk/kill-switch",
    summary="Toggle Kill Switch",
    description="""
    Toggle the kill switch to enable or disable trading.
    
    **⚠️ CRITICAL ENDPOINT:** This endpoint can immediately halt all trading.
    
    **Authentication:** Requires JWT Bearer token
    
    **Parameters:**
    - `user_id`: Optional. If provided, applies to user-specific config. If null, applies system-wide.
    - `enabled`: Set to `false` to activate kill switch (stop trading), `true` to resume trading
    - `reason`: Optional reason for the toggle (recommended for audit trail)
    
    **Example - Activate Kill Switch:**
    ```bash
    curl -X POST -H "Authorization: Bearer $ACCESS_TOKEN" \\
      -H "Content-Type: application/json" \\
      -d '{"enabled": false, "reason": "Emergency stop"}' \\
      "https://yourdomain.com/api/v1/risk/kill-switch?user_id=2"
    ```
    
    **Example - Resume Trading:**
    ```bash
    curl -X POST -H "Authorization: Bearer $ACCESS_TOKEN" \\
      -H "Content-Type: application/json" \\
      -d '{"enabled": true, "reason": "Resuming normal operations"}' \\
      "https://yourdomain.com/api/v1/risk/kill-switch?user_id=2"
    ```
    """
)
async def toggle_kill_switch(
    request: Request,
    kill_switch: KillSwitchRequest,
    current_user: User = Depends(get_current_user_dependency),
    user_id: Optional[int] = Query(
        default=None, 
        description="User ID (null for system-wide). Example: 2",
        example=2
    ),
    db: AsyncSession = Depends(get_db)
):
    config = await risk_manager.get_risk_config(user_id=user_id, db=db)
    
    old_status = config.trading_enabled
    config.trading_enabled = kill_switch.enabled
    
    await db.commit()
    
    # Log audit event
    action = "kill_switch_enabled" if kill_switch.enabled else "kill_switch_disabled"
    await audit_service.log_event(
        action=action,
        entity_type="risk_config",
        entity_id=str(config.id),
        details={
            "user_id": user_id,
            "old_status": old_status,
            "new_status": kill_switch.enabled,
            "reason": kill_switch.reason
        },
        username=current_user.username,
        user_id=current_user.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        db=db
    )
    
    # Log system event for critical kill switch actions
    if not kill_switch.enabled:
        await audit_service.log_system_event(
            event_type="kill_switch",
            severity="warning",
            message=f"Trading disabled via kill switch: {kill_switch.reason or 'No reason provided'}",
            component="risk_manager",
            details={
                "user_id": user_id,
                "reason": kill_switch.reason
            }
        )
    
    return {
        "status": "success",
        "message": f"Trading {'enabled' if kill_switch.enabled else 'disabled'}",
        "trading_enabled": kill_switch.enabled,
        "reason": kill_switch.reason,
        "user_id": user_id
    }


@router.get(
    "/risk/kill-switch/status",
    summary="Get Kill Switch Status",
    description="""
    Get the current kill switch status (whether trading is enabled or disabled).
    
    **Authentication:** Requires JWT Bearer token
    
    **Parameters:**
    - `user_id`: Optional. If provided, returns user-specific status. If null, returns system-wide status.
    
    **Returns:**
    - `trading_enabled`: Boolean indicating if trading is currently enabled
    - `user_id`: The user ID this status applies to (or null for system-wide)
    - `config_id`: The risk config ID
    
    **Example:**
    ```bash
    curl -H "Authorization: Bearer $ACCESS_TOKEN" \\
      "https://yourdomain.com/api/v1/risk/kill-switch/status?user_id=2"
    ```
    """
)
async def get_kill_switch_status(
    current_user: User = Depends(get_current_user_dependency),
    user_id: Optional[int] = Query(
        default=None, 
        description="User ID (null for system-wide). Example: 2",
        example=2
    ),
    db: AsyncSession = Depends(get_db)
):
    config = await risk_manager.get_risk_config(user_id=user_id, db=db)
    
    return {
        "status": "success",
        "trading_enabled": config.trading_enabled,
        "user_id": user_id,
        "config_id": config.id
    }


@router.post(
    "/risk/pre-trade-check",
    summary="Pre-Trade Risk Check",
    description="""
    Run comprehensive risk checks before placing an order.
    
    **Authentication:** Requires JWT Bearer token
    
    **Validates:**
    - Kill switch status
    - Trading hours
    - Position limits
    - Order limits
    - OPS (Orders Per Second) limits
    - Loss limits
    
    **Request Body:**
    - `user_id`: Internal platform user ID
    - `symbol`: Trading symbol (e.g., INFY)
    - `quantity`: Number of shares/lots
    - `price`: Price per unit (₹)
    
    **Returns:**
    - `all_passed`: Boolean indicating if all checks passed
    - `order_value`: Calculated order value (quantity × price)
    - `checks`: Array of individual check results with reasons
    
    **Example:**
    ```bash
    curl -X POST -H "Authorization: Bearer $ACCESS_TOKEN" \\
      -H "Content-Type: application/json" \\
      -d '{
        "user_id": 2,
        "symbol": "INFY",
        "quantity": 10,
        "price": 1500.0
      }' \\
      "https://yourdomain.com/api/v1/risk/pre-trade-check"
    ```
    """
)
async def pre_trade_check(
    check_request: PreTradeCheckRequest,
    current_user: User = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db)
):
    all_passed, results = await risk_manager.pre_trade_check(
        user_id=check_request.user_id,
        symbol=check_request.symbol,
        quantity=check_request.quantity,
        price=check_request.price,
        db=db
    )
    
    return {
        "status": "success",
        "all_passed": all_passed,
        "order_value": check_request.quantity * check_request.price,
        "checks": [
            {
                "passed": result.passed,
                "reason": result.reason,
                "breach_type": result.breach_type if not result.passed else None,
                "details": result.details if not result.passed else None
            }
            for result in results
        ],
        "message": "All checks passed" if all_passed else "One or more checks failed"
    }


@router.get("/risk/metrics/daily")
async def get_daily_metrics(
    current_user: User = Depends(get_current_user_dependency),
    user_id: int = Query(..., gt=0, description="User ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get daily risk metrics for a user
    
    Returns:
        dict: Daily trading metrics
    """
    metrics = await risk_manager.get_daily_metrics(user_id=user_id, db=db)
    
    return {
        "status": "success",
        "metrics": {
            "user_id": metrics.user_id,
            "trading_date": metrics.trading_date.isoformat() if metrics.trading_date else None,
            "orders_placed": metrics.orders_placed,
            "orders_executed": metrics.orders_executed,
            "orders_rejected": metrics.orders_rejected,
            "max_positions_held": metrics.max_positions_held,
            "current_positions": metrics.current_positions,
            "realized_pnl": metrics.realized_pnl,
            "unrealized_pnl": metrics.unrealized_pnl,
            "total_pnl": metrics.total_pnl,
            "max_loss_hit": metrics.max_loss_hit,
            "loss_limit_breached": metrics.loss_limit_breached,
            "total_turnover": metrics.total_turnover,
            "risk_breaches": metrics.risk_breaches,
            "created_at": metrics.created_at.isoformat() if metrics.created_at else None,
            "updated_at": metrics.updated_at.isoformat() if metrics.updated_at else None,
        }
    }


@router.get("/risk/breaches")
async def get_risk_breaches(
    current_user: User = Depends(get_current_user_dependency),
    user_id: Optional[int] = Query(default=None, description="Filter by user ID"),
    breach_type: Optional[str] = Query(default=None, description="Filter by breach type"),
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(default=0, ge=0, description="Offset for pagination"),
    db: AsyncSession = Depends(get_db)
):
    """
    Query risk breach logs
    
    Returns:
        dict: Paginated list of risk breaches
    """
    query = select(RiskBreachLog)
    
    if user_id:
        query = query.where(RiskBreachLog.user_id == user_id)
    if breach_type:
        query = query.where(RiskBreachLog.breach_type == breach_type)
    
    query = query.order_by(RiskBreachLog.created_at.desc()).limit(limit).offset(offset)
    
    result = await db.execute(query)
    breaches = result.scalars().all()
    
    return {
        "status": "success",
        "count": len(breaches),
        "limit": limit,
        "offset": offset,
        "breaches": [
            {
                "id": breach.id,
                "user_id": breach.user_id,
                "strategy_instance_id": breach.strategy_instance_id,
                "breach_type": breach.breach_type,
                "breach_details": breach.breach_details,
                "action_taken": breach.action_taken,
                "created_at": breach.created_at.isoformat() if breach.created_at else None,
            }
            for breach in breaches
        ]
    }


@router.get("/risk/breaches/{breach_id}")
async def get_risk_breach(
    breach_id: int,
    current_user: User = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db)
):
    """
    Get specific risk breach by ID
    
    Returns:
        dict: Risk breach details
    """
    result = await db.execute(
        select(RiskBreachLog).where(RiskBreachLog.id == breach_id)
    )
    breach = result.scalar_one_or_none()
    
    if not breach:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Risk breach with ID {breach_id} not found"
        )
    
    return {
        "status": "success",
        "breach": {
            "id": breach.id,
            "user_id": breach.user_id,
            "strategy_instance_id": breach.strategy_instance_id,
            "breach_type": breach.breach_type,
            "breach_details": breach.breach_details,
            "action_taken": breach.action_taken,
            "created_at": breach.created_at.isoformat() if breach.created_at else None,
        }
    }


@router.get("/risk/status")
async def get_risk_status(
    current_user: User = Depends(get_current_user_dependency),
    user_id: Optional[int] = Query(default=None, description="User ID (null for system-wide)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get comprehensive risk status
    
    Returns current risk configuration, daily metrics, and recent breaches.
    
    Returns:
        dict: Comprehensive risk status
    """
    # Get config
    config = await risk_manager.get_risk_config(user_id=user_id, db=db)
    
    # Get daily metrics if user_id provided
    daily_metrics = None
    if user_id:
        metrics = await risk_manager.get_daily_metrics(user_id=user_id, db=db)
        daily_metrics = {
            "orders_placed": metrics.orders_placed,
            "orders_executed": metrics.orders_executed,
            "orders_rejected": metrics.orders_rejected,
            "current_positions": metrics.current_positions,
            "total_pnl": metrics.total_pnl,
            "loss_limit_breached": metrics.loss_limit_breached,
            "risk_breaches": metrics.risk_breaches,
        }
    
    # Get recent breaches
    breach_query = select(RiskBreachLog).order_by(RiskBreachLog.created_at.desc()).limit(5)
    if user_id:
        breach_query = breach_query.where(RiskBreachLog.user_id == user_id)
    
    breach_result = await db.execute(breach_query)
    recent_breaches = breach_result.scalars().all()
    
    return {
        "status": "success",
        "trading_enabled": config.trading_enabled,
        "user_id": user_id,
        "limits": {
            "max_position_value": config.max_position_value,
            "max_positions": config.max_positions,
            "max_order_value": config.max_order_value,
            "max_orders_per_day": config.max_orders_per_day,
            "ops_limit": config.ops_limit,
            "max_daily_loss": config.max_daily_loss,
        },
        "daily_metrics": daily_metrics,
        "recent_breaches": [
            {
                "breach_type": breach.breach_type,
                "action_taken": breach.action_taken,
                "created_at": breach.created_at.isoformat() if breach.created_at else None,
            }
            for breach in recent_breaches
        ]
    }


@router.get("/risk/metrics/history")
async def get_metrics_history(
    current_user: User = Depends(get_current_user_dependency),
    user_id: int = Query(..., gt=0, description="User ID"),
    days: int = Query(default=7, ge=1, le=90, description="Number of days to fetch"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get historical daily metrics
    
    Returns:
        dict: Historical metrics for specified period
    """
    # Calculate date range
    ist = timezone(timedelta(hours=5, minutes=30))
    today = datetime.now(ist).replace(hour=0, minute=0, second=0, microsecond=0)
    start_date = today - timedelta(days=days)
    
    # Query metrics
    result = await db.execute(
        select(DailyRiskMetrics).where(
            and_(
                DailyRiskMetrics.user_id == user_id,
                DailyRiskMetrics.trading_date >= start_date
            )
        ).order_by(DailyRiskMetrics.trading_date.desc())
    )
    metrics_list = result.scalars().all()
    
    return {
        "status": "success",
        "user_id": user_id,
        "days": days,
        "count": len(metrics_list),
        "metrics": [
            {
                "trading_date": m.trading_date.isoformat() if m.trading_date else None,
                "orders_placed": m.orders_placed,
                "orders_executed": m.orders_executed,
                "orders_rejected": m.orders_rejected,
                "max_positions_held": m.max_positions_held,
                "total_pnl": m.total_pnl,
                "loss_limit_breached": m.loss_limit_breached,
                "total_turnover": m.total_turnover,
                "risk_breaches": m.risk_breaches,
            }
            for m in metrics_list
        ]
    }


@router.get("/risk/limits/check")
async def check_risk_limits(
    current_user: User = Depends(get_current_user_dependency),
    user_id: int = Query(..., gt=0, description="User ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    Check current status against all risk limits
    
    Returns which limits are close to being breached.
    
    Returns:
        dict: Risk limit status
    """
    config = await risk_manager.get_risk_config(user_id=user_id, db=db)
    metrics = await risk_manager.get_daily_metrics(user_id=user_id, db=db)
    
    # Calculate utilization percentages
    order_utilization = (metrics.orders_placed / config.max_orders_per_day) * 100
    loss_utilization = abs(metrics.total_pnl / config.max_daily_loss) * 100 if metrics.total_pnl < 0 else 0
    
    # Count current positions
    position_result = await db.execute(
        select(func.count()).select_from(Position).where(
            and_(
                Position.user_id == user_id,
                Position.quantity != 0
            )
        )
    )
    current_positions = position_result.scalar() or 0
    position_utilization = (current_positions / config.max_positions) * 100
    
    warnings = []
    if order_utilization >= 80:
        warnings.append(f"Order limit at {order_utilization:.1f}% utilization")
    if loss_utilization >= 80:
        warnings.append(f"Loss limit at {loss_utilization:.1f}% utilization")
    if position_utilization >= 80:
        warnings.append(f"Position limit at {position_utilization:.1f}% utilization")
    
    return {
        "status": "success",
        "trading_enabled": config.trading_enabled,
        "loss_limit_breached": metrics.loss_limit_breached,
        "utilization": {
            "orders": {
                "current": metrics.orders_placed,
                "limit": config.max_orders_per_day,
                "percentage": round(order_utilization, 2)
            },
            "positions": {
                "current": current_positions,
                "limit": config.max_positions,
                "percentage": round(position_utilization, 2)
            },
            "loss": {
                "current": metrics.total_pnl,
                "limit": -config.max_daily_loss,
                "percentage": round(loss_utilization, 2)
            }
        },
        "warnings": warnings,
        "risk_breaches_today": metrics.risk_breaches
    }

