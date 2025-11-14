"""
Zerodha Order Service

Handles order placement, validation, and post-trade bookkeeping with Zerodha.
Integrates the risk manager for comprehensive pre-trade checks before placing
orders.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from kiteconnect import KiteConnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.models import Order, DailyRiskMetrics
from app.models.broker_connection import BrokerConnection, BrokerType
from app.services.audit_service import audit_service
from app.services.risk_manager import risk_manager, RiskCheckResult


RiskCheckNames = [
    "kill_switch",
    "trading_hours",
    "position_limits",
    "order_limits",
    "ops_limit",
    "loss_limits",
]


def _decimal(value: Optional[float]) -> Optional[Decimal]:
    if value is None:
        return None
    return Decimal(str(value))


def _serialize_risk_results(results: List[RiskCheckResult]) -> List[Dict]:
    payload = []
    for name, result in zip(RiskCheckNames, results):
        payload.append(
            {
                "check": name,
                "passed": result.passed,
                "reason": result.reason,
                "breach_type": result.breach_type,
                "details": result.details,
            }
        )
    return payload


async def _get_broker_connection(
    db: AsyncSession, user_id: int
) -> BrokerConnection:
    stmt = (
        select(BrokerConnection)
        .where(BrokerConnection.user_id == user_id)
        .where(BrokerConnection.broker == BrokerType.ZERODHA)
        .where(BrokerConnection.is_active.is_(True))
    )
    result = await db.execute(stmt)
    connection = result.scalars().first()
    if not connection:
        raise ValueError(f"No active Zerodha broker connection found for user {user_id}")
    if not connection.algo_identifier:
        raise ValueError(
            "Broker connection is missing algo_identifier. Update broker configuration."
        )
    return connection


async def _increment_order_metrics(
    db: AsyncSession, user_id: int, order_value: float
) -> None:
    metrics = await risk_manager.get_daily_metrics(user_id=user_id, db=db)
    metrics.orders_placed += 1
    metrics.total_turnover += order_value
    await db.commit()


async def preview_order(
    db: AsyncSession,
    kite: KiteConnect,
    user_id: int,
    symbol: str,
    quantity: int,
    price_for_risk: float,
    margin_params: Dict,
) -> Dict:
    """
    Run pre-trade risk checks and optionally compute margin requirements.
    """
    all_passed, results = await risk_manager.pre_trade_check(
        user_id=user_id,
        symbol=symbol,
        quantity=quantity,
        price=price_for_risk,
        db=db,
    )

    margin_breakdown = None
    try:
        margin_breakdown = await run_in_threadpool(kite.order_margins, [margin_params])
    except Exception:
        # Margin API may fail for some instruments (e.g., if offline or invalid request).
        margin_breakdown = None

    return {
        "all_checks_passed": all_passed,
        "risk_checks": _serialize_risk_results(results),
        "margin": margin_breakdown,
    }


async def place_order(
    db: AsyncSession,
    kite: KiteConnect,
    *,
    user_id: int,
    user_identifier: str,
    instrument_token: Optional[int],
    exchange: str,
    tradingsymbol: str,
    transaction_type: str,
    quantity: int,
    order_type: str,
    product: str,
    variety: str,
    price: Optional[float],
    trigger_price: Optional[float],
    disclosed_quantity: Optional[int],
    validity: str,
    tag: Optional[str],
    price_for_risk: float,
    strategy_instance_id: Optional[int] = None,
) -> Dict:
    """
    Perform pre-trade risk checks and place order via Zerodha.
    """
    connection = await _get_broker_connection(db, user_id)
    order_value = quantity * price_for_risk

    all_passed, risk_results = await risk_manager.pre_trade_check(
        user_id=user_id,
        symbol=tradingsymbol,
        quantity=quantity,
        price=price_for_risk,
        db=db,
    )

    serialized_results = _serialize_risk_results(risk_results)

    if not all_passed:
        return {
            "status": "rejected",
            "message": "Risk checks failed",
            "risk_checks": serialized_results,
        }

    order_params = {
        "variety": variety,
        "exchange": exchange,
        "tradingsymbol": tradingsymbol,
        "transaction_type": transaction_type,
        "quantity": quantity,
        "order_type": order_type,
        "product": product,
        "price": price if price is not None else 0,
        "validity": validity,
        "disclosed_quantity": disclosed_quantity or 0,
        "trigger_price": trigger_price if trigger_price is not None else 0,
        "tag": tag or connection.algo_identifier,
    }

    if order_type.upper() == "MARKET":
        order_params["price"] = 0

    if trigger_price is None and order_type.upper() in {"SL", "SL-M"}:
        raise ValueError("trigger_price is required for stop-loss orders")

    try:
        order_id = await run_in_threadpool(kite.place_order, **order_params)
    except Exception as exc:
        await audit_service.log_event(
            action="order_place_failed",
            entity_type="order",
            entity_id=None,
            user_id=user_id,
            details={
                "tradingsymbol": tradingsymbol,
                "transaction_type": transaction_type,
                "quantity": quantity,
                "order_type": order_type,
                "product": product,
                "reason": str(exc),
            },
            db=db,
        )
        raise

    order_record = Order(
        order_id=order_id,
        parent_order_id=None,
        user_id=user_id,
        broker_connection_id=connection.id,
        strategy_instance_id=strategy_instance_id,
        algo_identifier=connection.algo_identifier,
        exchange=exchange,
        tradingsymbol=tradingsymbol,
        instrument_token=instrument_token,
        transaction_type=transaction_type,
        order_type=order_type,
        product=product,
        variety=variety,
        quantity=quantity,
        price=_decimal(price),
        trigger_price=_decimal(trigger_price),
        disclosed_quantity=disclosed_quantity,
        status="PENDING",
        status_message="Order placed",
        filled_quantity=0,
        pending_quantity=quantity,
        cancelled_quantity=0,
        average_price=_decimal(0),
        placed_at=datetime.now(timezone.utc),
        exchange_timestamp=None,
        last_modified_at=None,
        placed_by="system",
    )

    db.add(order_record)
    await db.commit()

    await _increment_order_metrics(db, user_id, order_value)

    await audit_service.log_event(
        action="order_place",
        entity_type="order",
        entity_id=order_id,
        user_id=user_id,
        details={
            "tradingsymbol": tradingsymbol,
            "transaction_type": transaction_type,
            "quantity": quantity,
            "order_type": order_type,
            "product": product,
            "order_value": order_value,
            "user_identifier": user_identifier,
        },
        db=db,
    )

    return {
        "status": "accepted",
        "order_id": order_id,
        "risk_checks": serialized_results,
    }


async def cancel_order(
    kite: KiteConnect,
    *,
    order_id: str,
    variety: str,
) -> Dict:
    """Cancel an order via Zerodha."""
    result = await run_in_threadpool(kite.cancel_order, variety=variety, order_id=order_id)
    return {"status": "success", "order_id": result}


async def modify_order(
    kite: KiteConnect,
    *,
    order_id: str,
    variety: str,
    quantity: Optional[int] = None,
    price: Optional[float] = None,
    trigger_price: Optional[float] = None,
    order_type: Optional[str] = None,
    validity: Optional[str] = None,
) -> Dict:
    """Modify an existing order via Zerodha."""
    result = await run_in_threadpool(
        kite.modify_order,
        variety=variety,
        order_id=order_id,
        quantity=quantity,
        price=price,
        trigger_price=trigger_price,
        order_type=order_type,
        validity=validity,
    )
    return {"status": "success", "order_id": result}


