"""
Zerodha Data Exploration API - Simple Version

These endpoints provide a lightweight façade over the Zerodha SDK for quick
ad-hoc exploration and testing. They operate on the *broker session* identified
by the OAuth `state` value (`user_identifier`), so multiple TradeDesk users can
share the same broker account.
"""

from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Body
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
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


def _success(data, **extra):
    payload = {"status": "success", "data": data}
    payload.update(extra)
    return payload


def _error(message: str):
    return {"status": "error", "message": message}


# ===== BASIC ENDPOINTS =====

@router.get(
    "/zerodha/profile",
    summary="Get Zerodha User Profile",
    description="""
    Get Zerodha account profile information.
    
    **Authentication:** Requires JWT Bearer token
    
    **Parameters:**
    - `user_identifier`: Zerodha OAuth user identifier (e.g., YOUR_USER_IDENTIFIER). Must be owned by authenticated user.
    
    **Returns:**
    - User ID, name, email
    - Enabled exchanges (NSE, BSE, NFO, etc.)
    - Enabled products (CNC, MIS, NRML, etc.)
    - Enabled order types (MARKET, LIMIT, SL, etc.)
    
    **Example:**
    ```bash
    curl -H "Authorization: Bearer $ACCESS_TOKEN" \\
      "https://your-domain.com/api/v1/data/zerodha/profile?user_identifier=YOUR_USER_IDENTIFIER"
    ```
    """
)
async def get_profile(
    current_user: User = Depends(get_current_user_dependency),
    user_identifier: str = Query(..., description="Zerodha OAuth user identifier (e.g., YOUR_USER_IDENTIFIER)", example="YOUR_USER_IDENTIFIER"),
    db: AsyncSession = Depends(get_db),
):
    try:
        # Validate user owns this session
        session = await validate_user_owns_session(current_user, user_identifier, db)
        access_token = decrypt_access_token(session)
        kite = get_kite_client(access_token)
        
        profile = await run_in_threadpool(kite.profile)
        return _success(profile)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to fetch profile")
        return _error(str(exc))


@router.get("/zerodha/margins")
async def get_margins(
    current_user: User = Depends(get_current_user_dependency),
    user_identifier: str = Query(..., description="Zerodha OAuth user identifier"),
    db: AsyncSession = Depends(get_db),
):
    try:
        session = await validate_user_owns_session(current_user, user_identifier, db)
        access_token = decrypt_access_token(session)
        kite = get_kite_client(access_token)
        
        margins = await run_in_threadpool(kite.margins)
        return _success(margins)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to fetch margins")
        return _error(str(exc))


@router.get("/zerodha/holdings")
async def get_holdings(
    current_user: User = Depends(get_current_user_dependency),
    user_identifier: str = Query(..., description="Zerodha OAuth user identifier"),
    db: AsyncSession = Depends(get_db),
):
    try:
        session = await validate_user_owns_session(current_user, user_identifier, db)
        access_token = decrypt_access_token(session)
        kite = get_kite_client(access_token)
        
        holdings = await run_in_threadpool(kite.holdings)
        return _success(holdings)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to fetch holdings")
        return _error(str(exc))


@router.get("/zerodha/positions")
async def get_positions(
    current_user: User = Depends(get_current_user_dependency),
    user_identifier: str = Query(..., description="Zerodha OAuth user identifier"),
    db: AsyncSession = Depends(get_db),
):
    try:
        session = await validate_user_owns_session(current_user, user_identifier, db)
        access_token = decrypt_access_token(session)
        kite = get_kite_client(access_token)
        
        positions = await run_in_threadpool(kite.positions)
        return _success(positions)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to fetch positions")
        return _error(str(exc))


@router.get("/zerodha/orders")
async def get_orders(
    current_user: User = Depends(get_current_user_dependency),
    user_identifier: str = Query(..., description="Zerodha OAuth user identifier"),
    db: AsyncSession = Depends(get_db),
):
    try:
        session = await validate_user_owns_session(current_user, user_identifier, db)
        access_token = decrypt_access_token(session)
        kite = get_kite_client(access_token)
        
        orders = await run_in_threadpool(kite.orders)
        return _success(orders)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to fetch orders")
        return _error(str(exc))


@router.get("/zerodha/trades")
async def get_trades(
    current_user: User = Depends(get_current_user_dependency),
    user_identifier: str = Query(..., description="Zerodha OAuth user identifier"),
    db: AsyncSession = Depends(get_db),
):
    try:
        session = await validate_user_owns_session(current_user, user_identifier, db)
        access_token = decrypt_access_token(session)
        kite = get_kite_client(access_token)
        
        trades = await run_in_threadpool(kite.trades)
        return _success(trades)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to fetch trades")
        return _error(str(exc))


@router.post("/zerodha/quote")
async def get_quote(
    current_user: User = Depends(get_current_user_dependency),
    user_identifier: str = Query(..., description="Zerodha OAuth user identifier"),
    instruments: List[str] = Body(..., description='List like ["NSE:INFY"]'),
    db: AsyncSession = Depends(get_db),
):
    try:
        session = await validate_user_owns_session(current_user, user_identifier, db)
        access_token = decrypt_access_token(session)
        kite = get_kite_client(access_token)
        
        quote = await run_in_threadpool(kite.quote, instruments)
        return _success(quote)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to fetch quote")
        return _error(str(exc))


@router.post("/zerodha/ltp")
async def get_ltp(
    current_user: User = Depends(get_current_user_dependency),
    user_identifier: str = Query(..., description="Zerodha OAuth user identifier"),
    instruments: List[str] = Body(..., description='List like ["NSE:INFY"]'),
    db: AsyncSession = Depends(get_db),
):
    try:
        session = await validate_user_owns_session(current_user, user_identifier, db)
        access_token = decrypt_access_token(session)
        kite = get_kite_client(access_token)
        
        ltp = await run_in_threadpool(kite.ltp, instruments)
        return _success(ltp)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to fetch LTP")
        return _error(str(exc))


@router.post("/zerodha/ohlc")
async def get_ohlc(
    current_user: User = Depends(get_current_user_dependency),
    user_identifier: str = Query(..., description="Zerodha OAuth user identifier"),
    instruments: List[str] = Body(..., description='List like ["NSE:INFY"]'),
    db: AsyncSession = Depends(get_db),
):
    try:
        session = await validate_user_owns_session(current_user, user_identifier, db)
        access_token = decrypt_access_token(session)
        kite = get_kite_client(access_token)
        
        ohlc = await run_in_threadpool(kite.ohlc, instruments)
        return _success(ohlc)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to fetch OHLC")
        return _error(str(exc))


@router.get("/zerodha/instruments")
async def get_instruments(
    current_user: User = Depends(get_current_user_dependency),
    user_identifier: str = Query(..., description="Zerodha OAuth user identifier"),
    exchange: Optional[str] = Query(None, description="Optional exchange filter (NSE, BSE, NFO, etc.)"),
    db: AsyncSession = Depends(get_db),
):
    try:
        session = await validate_user_owns_session(current_user, user_identifier, db)
        access_token = decrypt_access_token(session)
        kite = get_kite_client(access_token)
        
        if exchange:
            instruments = await run_in_threadpool(kite.instruments, exchange)
        else:
            instruments = await run_in_threadpool(kite.instruments)
        instruments_list = [dict(item) for item in instruments]
        return _success(instruments_list, count=len(instruments_list))
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to fetch instruments")
        return _error(str(exc))


@router.get("/zerodha/historical/{instrument_token}")
async def get_historical(
    instrument_token: int,
    current_user: User = Depends(get_current_user_dependency),
    user_identifier: str = Query(..., description="Zerodha OAuth user identifier"),
    from_date: date = Query(..., description="Start date"),
    to_date: date = Query(..., description="End date"),
    interval: str = Query(..., description="Interval (minute, day, etc.)"),
    continuous: bool = Query(default=False, description="Continuous data for F&O contracts"),
    oi: bool = Query(default=False, description="Include open interest"),
    db: AsyncSession = Depends(get_db),
):
    try:
        session = await validate_user_owns_session(current_user, user_identifier, db)
        access_token = decrypt_access_token(session)
        kite = get_kite_client(access_token)
        
        candles = await run_in_threadpool(
            kite.historical_data,
            instrument_token,
            from_date,
            to_date,
            interval,
            continuous,
            oi,
        )
        return _success(candles, count=len(candles))
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to fetch historical data")
        return _error(str(exc))


@router.get("/zerodha/capabilities")
async def get_capabilities():
    """Get API capabilities overview."""
    return {
        "status": "success",
        "message": "Zerodha Data API - Simple Version",
        "endpoints": {
            "account": [
                "GET /zerodha/profile - User profile",
                "GET /zerodha/margins - Account margins",
            ],
            "portfolio": [
                "GET /zerodha/holdings - Long-term holdings",
                "GET /zerodha/positions - Current positions",
            ],
            "orders": [
                "GET /zerodha/orders - All orders",
                "GET /zerodha/trades - Executed trades",
            ],
            "market_data": [
                "GET /zerodha/instruments - All instruments",
                "POST /zerodha/quote - Full quote with depth",
                "POST /zerodha/ltp - Last traded price",
                "POST /zerodha/ohlc - OHLC data",
            ],
            "historical": [
                "GET /zerodha/historical/{token} - Historical candles",
            ],
        },
        "note": "All endpoints use the broker `user_identifier` (Zerodha OAuth state)",
    }


