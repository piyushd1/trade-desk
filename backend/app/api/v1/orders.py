"""
Order Management APIs

Endpoints for pre-trade validation and order placement with Zerodha, including
comprehensive risk checks.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.api.v1.auth import get_current_user_dependency
from app.api.v1.zerodha_common import (
    decrypt_access_token,
    get_kite_client,
    validate_user_owns_session,
)
from app.database import get_db
from app.models.user import User
from app.services.zerodha_order_service import (
    cancel_order,
    modify_order,
    place_order,
    preview_order,
)

router = APIRouter(prefix="/orders", tags=["Order Management"])


class OrderBase(BaseModel):
    user_id: int = Field(..., description="Internal user ID")
    user_identifier: str = Field(..., description="Broker user identifier (OAuth state)")
    exchange: str = Field(..., description="Exchange (NSE, BSE, NFO, etc.)")
    tradingsymbol: str = Field(..., description="Trading symbol (e.g., INFY)")
    transaction_type: str = Field(..., pattern="^(BUY|SELL)$")
    quantity: int = Field(..., gt=0)
    order_type: str = Field(..., description="Order type (MARKET, LIMIT, SL, SL-M)")
    product: str = Field(..., description="Product (CNC, MIS, NRML, etc.)")
    variety: str = Field("regular", description="Order variety (regular, amo, iceberg, etc.)")
    validity: str = Field("DAY", description="Order validity (DAY, IOC, etc.)")
    price: Optional[float] = Field(None, description="Order price (if applicable)")
    trigger_price: Optional[float] = Field(None, description="Trigger price for SL/SL-M orders")
    disclosed_quantity: Optional[int] = Field(None, description="Disclosed quantity")
    tag: Optional[str] = Field(None, description="Custom tag (max 20 chars)")
    instrument_token: Optional[int] = Field(None, description="Instrument token (optional)")
    strategy_instance_id: Optional[int] = Field(None, description="Strategy instance ID")
    price_for_risk: Optional[float] = Field(
        None,
        description="Price used for risk calculations if different from order price",
    )


class OrderPreviewRequest(OrderBase):
    pass


class OrderPlaceRequest(OrderBase):
    pass


class OrderModifyRequest(BaseModel):
    user_identifier: str = Field(..., description="Broker user identifier")
    order_id: str = Field(..., description="Order ID")
    variety: str = Field(..., description="Order variety")
    quantity: Optional[int] = Field(None, gt=0)
    price: Optional[float] = None
    trigger_price: Optional[float] = None
    order_type: Optional[str] = None
    validity: Optional[str] = None


class OrderCancelRequest(BaseModel):
    user_identifier: str = Field(..., description="Broker user identifier")
    order_id: str = Field(..., description="Order ID")
    variety: str = Field(..., description="Order variety")


async def _ensure_price_for_risk(
    request: OrderBase, kite, instrument_token: Optional[int]
) -> tuple[float, Optional[int]]:
    price_for_risk = request.price_for_risk or request.price

    if price_for_risk is None:
        # Fetch last traded price for risk evaluation
        instrument = f"{request.exchange}:{request.tradingsymbol}"
        try:
            quote = await run_in_threadpool(kite.ltp, [instrument])
            price_for_risk = quote[instrument]["last_price"]
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unable to fetch last traded price: {exc}",
            ) from exc

    # Resolve instrument token if missing (reuse helper)
    if instrument_token is None:
        instrument = f"{request.exchange}:{request.tradingsymbol}"
        try:
            quote = await run_in_threadpool(kite.quote, [instrument])
            data = quote.get(instrument)
            if data:
                instrument_token = data.get("instrument_token")
        except Exception:
            instrument_token = None

    return price_for_risk, instrument_token


@router.post("/preview", summary="Preview order with risk checks")
async def preview_order_endpoint(
    request: OrderPreviewRequest,
    current_user: User = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db)
):
    session = await validate_user_owns_session(current_user, request.user_identifier, db)
    access_token = decrypt_access_token(session)
    kite = get_kite_client(access_token)

    # Calculate price for risk evaluation and resolve instrument token
    price_for_risk, _ = await _ensure_price_for_risk(request, kite, request.instrument_token)

    margin_params = {
        "exchange": request.exchange,
        "tradingsymbol": request.tradingsymbol,
        "transaction_type": request.transaction_type,
        "variety": request.variety,
        "product": request.product,
        "order_type": request.order_type,
        "quantity": request.quantity,
        "price": request.price or 0,
        "trigger_price": request.trigger_price or 0,
    }

    summary = await preview_order(
        db=db,
        kite=kite,
        user_id=request.user_id,
        symbol=request.tradingsymbol,
        quantity=request.quantity,
        price_for_risk=price_for_risk,
        margin_params=margin_params,
    )
    return summary


@router.post("/place", summary="Place order after risk checks")
async def place_order_endpoint(
    request: OrderPlaceRequest,
    current_user: User = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db)
):
    session = await validate_user_owns_session(current_user, request.user_identifier, db)
    access_token = decrypt_access_token(session)
    kite = get_kite_client(access_token)

    price_for_risk, instrument_token = await _ensure_price_for_risk(
        request, kite, request.instrument_token
    )

    try:
        result = await place_order(
            db=db,
            kite=kite,
            user_id=request.user_id,
            user_identifier=request.user_identifier,
            instrument_token=instrument_token,
            exchange=request.exchange,
            tradingsymbol=request.tradingsymbol,
            transaction_type=request.transaction_type,
            quantity=request.quantity,
            order_type=request.order_type,
            product=request.product,
            variety=request.variety,
            price=request.price,
            trigger_price=request.trigger_price,
            disclosed_quantity=request.disclosed_quantity,
            validity=request.validity,
            tag=request.tag,
            price_for_risk=price_for_risk,
            strategy_instance_id=request.strategy_instance_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Order placement failed: {exc}",
        ) from exc

    return result


@router.post("/modify", summary="Modify an existing order")
async def modify_order_endpoint(
    request: OrderModifyRequest,
    current_user: User = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db)
):
    session = await validate_user_owns_session(current_user, request.user_identifier, db)
    access_token = decrypt_access_token(session)
    kite = get_kite_client(access_token)

    result = await modify_order(
        kite=kite,
        order_id=request.order_id,
        variety=request.variety,
        quantity=request.quantity,
        price=request.price,
        trigger_price=request.trigger_price,
        order_type=request.order_type,
        validity=request.validity,
    )
    return result


@router.post("/cancel", summary="Cancel an order")
async def cancel_order_endpoint(
    request: OrderCancelRequest,
    current_user: User = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db)
):
    session = await validate_user_owns_session(current_user, request.user_identifier, db)
    access_token = decrypt_access_token(session)
    kite = get_kite_client(access_token)

    result = await cancel_order(
        kite=kite,
        order_id=request.order_id,
        variety=request.variety,
    )
    return result


