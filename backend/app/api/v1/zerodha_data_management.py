"""
Zerodha Data Management APIs

Endpoints to synchronize instrument metadata and historical OHLCV candles from
Zerodha into the local database for analysis and backtesting.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.v1.auth import get_current_user_dependency
from app.api.v1.zerodha_common import (
    decrypt_access_token,
    get_kite_client,
    validate_user_owns_session,
)
from app.database import get_db
from app.models.user import User
from app.services.zerodha_data_service import (
    cleanup_historical_data,
    fetch_and_store_historical_data,
    get_instrument,
    historical_data_stats,
    query_historical_data,
    search_instruments,
    sync_instruments,
)

router = APIRouter(prefix="/zerodha/data", tags=["Zerodha Data Management"])


# ---------------------------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------------------------


class InstrumentSyncRequest(BaseModel):
    user_identifier: str = Field(..., description="User identifier used during OAuth")
    exchange: Optional[str] = Field(
        None, description="Optional exchange filter (NSE, BSE, NFO, etc.)"
    )


class HistoricalFetchRequest(BaseModel):
    user_identifier: str = Field(..., description="User identifier used during OAuth")
    instrument_token: int = Field(..., description="Instrument token to fetch candles for")
    from_date: datetime = Field(..., description="Start date (inclusive)")
    to_date: datetime = Field(..., description="End date (inclusive)")
    interval: str = Field(..., description="Interval (minute, 3minute, 5minute, day, etc.)")
    continuous: bool = Field(False, description="Continuous data for F&O contracts")
    oi: bool = Field(False, description="Include open interest data")


class HistoricalQueryParams(BaseModel):
    instrument_token: int
    interval: str
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    limit: int = Field(500, ge=1, le=5000)


class HistoricalCleanupRequest(BaseModel):
    user_identifier: Optional[str] = Field(
        None,
        description="Optional user identifier for authentication (not used directly but maintained for parity)",
    )
    instrument_token: Optional[int] = Field(None, description="Instrument token to prune")
    older_than: Optional[datetime] = Field(None, description="Delete candles older than this timestamp")


# ---------------------------------------------------------------------------
# Instrument Endpoints
# ---------------------------------------------------------------------------


@router.post("/instruments/sync", summary="Sync instruments from Zerodha")
async def instruments_sync(
    request: InstrumentSyncRequest,
    current_user: User = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db)
):
    session = await validate_user_owns_session(current_user, request.user_identifier, db)
    access_token = decrypt_access_token(session)
    kite = get_kite_client(access_token)

    summary = await sync_instruments(db, kite, request.exchange)
    return {"status": "success", "summary": summary}


@router.get("/instruments/search", summary="Search instruments")
async def instruments_search(
    q: Optional[str] = Query(None, description="Search query (tradingsymbol or name)"),
    exchange: Optional[str] = Query(None, description="Exchange filter"),
    segment: Optional[str] = Query(None, description="Segment filter"),
    instrument_type: Optional[str] = Query(None, description="Instrument type filter"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of results"),
    db: AsyncSession = Depends(get_db),
):
    results = await search_instruments(
        db=db,
        query=q,
        exchange=exchange,
        segment=segment,
        instrument_type=instrument_type,
        limit=limit,
    )
    return {"count": len(results), "results": results}


@router.get("/instruments/{instrument_token}", summary="Get instrument details")
async def instrument_detail(
    instrument_token: int, db: AsyncSession = Depends(get_db)
):
    result = await get_instrument(db, instrument_token)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Instrument {instrument_token} not found",
        )
    return result


# ---------------------------------------------------------------------------
# Historical Data Endpoints
# ---------------------------------------------------------------------------


@router.post("/historical/fetch", summary="Fetch & store historical data")
async def historical_fetch(
    request: HistoricalFetchRequest,
    current_user: User = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db)
):
    session = await validate_user_owns_session(current_user, request.user_identifier, db)
    access_token = decrypt_access_token(session)
    kite = get_kite_client(access_token)

    from_date = request.from_date
    to_date = request.to_date

    summary = await fetch_and_store_historical_data(
        db=db,
        kite=kite,
        instrument_token=request.instrument_token,
        from_date=from_date,
        to_date=to_date,
        interval=request.interval,
        continuous=request.continuous,
        oi=request.oi,
    )
    return {"status": "success", "summary": summary}


@router.get("/historical", summary="Query stored historical data")
async def historical_query(
    instrument_token: int = Query(..., description="Instrument token"),
    interval: str = Query(..., description="Interval"),
    start: Optional[datetime] = Query(None, description="Start timestamp"),
    end: Optional[datetime] = Query(None, description="End timestamp"),
    limit: int = Query(500, ge=1, le=5000, description="Maximum number of candles"),
    db: AsyncSession = Depends(get_db),
):
    candles = await query_historical_data(
        db=db,
        instrument_token=instrument_token,
        interval=interval,
        start=start,
        end=end,
        limit=limit,
    )
    return {"count": len(candles), "candles": candles}


@router.get("/historical/stats", summary="Historical data statistics")
async def historical_stats(
    instrument_token: Optional[int] = Query(None, description="Instrument token"),
    interval: Optional[str] = Query(None, description="Interval"),
    db: AsyncSession = Depends(get_db),
):
    stats_payload = await historical_data_stats(
        db=db,
        instrument_token=instrument_token,
        interval=interval,
    )
    return stats_payload


@router.delete("/historical/cleanup", summary="Cleanup stored historical data")
async def historical_cleanup(
    request: HistoricalCleanupRequest,
    current_user: User = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db)
):
    # Note: Cleanup doesn't require Zerodha session validation, only JWT auth
    count = await cleanup_historical_data(
        db=db,
        instrument_token=request.instrument_token,
        older_than=request.older_than,
    )
    return {"status": "success", "deleted": count}


