"""
Zerodha Streaming APIs

Endpoints to manage Zerodha Kite WebSocket streams, inspect latency metrics,
and validate broker sessions. These APIs are focused on data exploration to
understand the quality and timeliness of data delivered by Zerodha.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, validator
from kiteconnect import KiteConnect
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
from app.services.zerodha_streaming_service import zerodha_streaming_manager

router = APIRouter(prefix="/zerodha", tags=["Zerodha Data Streaming"])


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class InstrumentSubscription(BaseModel):
    instrument_token: Optional[int] = Field(
        None, description="Instrument token to subscribe to"
    )
    tradingsymbol: Optional[str] = Field(
        None, description="Trading symbol (e.g. INFY, RELIANCE)"
    )
    exchange: Optional[str] = Field(
        "NSE",
        description="Exchange for the trading symbol (NSE, BSE, NFO, etc.)",
    )

    @validator("instrument_token", always=True)
    def validate_token_or_symbol(cls, v, values):
        if v is None and not values.get("tradingsymbol"):
            raise ValueError("Either instrument_token or tradingsymbol must be provided")
        return v


class StartStreamRequest(BaseModel):
    user_identifier: str = Field(..., description="User identifier used during OAuth")
    instruments: List[InstrumentSubscription] = Field(
        ..., description="Instruments to subscribe for streaming"
    )
    mode: str = Field(
        "full",
        description="Streaming mode: full, quote, or ltp",
        pattern="^(full|quote|ltp)$",
    )


class StopStreamRequest(BaseModel):
    user_identifier: str = Field(..., description="User identifier to stop streaming for")


class UpdateSubscriptionRequest(BaseModel):
    user_identifier: str = Field(..., description="User identifier")
    instruments: List[InstrumentSubscription] = Field(
        ..., description="Updated list of instrument subscriptions"
    )
    mode: Optional[str] = Field(
        None,
        description="Optional streaming mode override (full, quote, ltp)",
        pattern="^(full|quote|ltp)$",
    )


class SessionStatusResponse(BaseModel):
    user_identifier: str
    broker: str
    status: str
    has_refresh_token: bool
    expires_at: Optional[str]
    expires_in_minutes: Optional[float]


class SessionValidationResponse(BaseModel):
    status: str
    message: str
    profile: Optional[dict] = None


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------


async def _resolve_instrument_tokens(
    kite: KiteConnect, subscriptions: List[InstrumentSubscription]
) -> List[int]:
    tokens: List[int] = []
    symbols_to_resolve: List[str] = []

    for item in subscriptions:
        if item.instrument_token is not None:
            tokens.append(int(item.instrument_token))
        else:
            exchange = item.exchange or "NSE"
            symbols_to_resolve.append(f"{exchange}:{item.tradingsymbol}")

    if symbols_to_resolve:
        try:
            quote = await run_in_threadpool(kite.quote, symbols_to_resolve)
            for tradingsymbol in symbols_to_resolve:
                data = quote.get(tradingsymbol)
                if data and "instrument_token" in data:
                    tokens.append(int(data["instrument_token"]))
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to resolve tradingsymbols: {exc}",
            ) from exc

    if not tokens:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid instruments resolved",
        )

    return tokens


# ---------------------------------------------------------------------------
# API endpoints
# ---------------------------------------------------------------------------


@router.post("/stream/start", summary="Start Zerodha data stream")
async def start_stream(
    request: StartStreamRequest,
    current_user: User = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db)
):
    """Start streaming real-time ticks for the specified user and instruments."""
    session = await validate_user_owns_session(current_user, request.user_identifier, db)
    access_token = decrypt_access_token(session)

    kite = get_kite_client(access_token)
    instrument_tokens = await _resolve_instrument_tokens(kite, request.instruments)

    try:
        status_payload = await run_in_threadpool(
            zerodha_streaming_manager.start_stream,
            user_identifier=request.user_identifier,
            access_token=access_token,
            instrument_tokens=instrument_tokens,
            mode=request.mode,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start Zerodha streaming: {exc}",
        ) from exc

    status_payload["instrument_tokens"] = instrument_tokens
    return status_payload


@router.post("/stream/stop", summary="Stop Zerodha data stream")
async def stop_stream(
    request: StopStreamRequest,
    current_user: User = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db)
):
    """Stop streaming for the specified user."""
    # Validate ownership before stopping stream
    await validate_user_owns_session(current_user, request.user_identifier, db)
    
    stopped = await run_in_threadpool(
        zerodha_streaming_manager.stop_stream, request.user_identifier
    )
    if not stopped:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active stream found for user {request.user_identifier}",
        )
    return {"status": "success", "message": "Streaming stopped"}


@router.post("/stream/update", summary="Update streaming subscription")
async def update_subscription(
    request: UpdateSubscriptionRequest,
    current_user: User = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db)
):
    """Update subscribed instruments for an active stream."""
    session = await validate_user_owns_session(current_user, request.user_identifier, db)
    access_token = decrypt_access_token(session)

    kite = get_kite_client(access_token)
    instrument_tokens = await _resolve_instrument_tokens(kite, request.instruments)

    try:
        status_payload = await run_in_threadpool(
            zerodha_streaming_manager.update_subscription,
            user_identifier=request.user_identifier,
            instrument_tokens=instrument_tokens,
            mode=request.mode,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return status_payload


@router.get("/stream/status", summary="Streaming status & metrics")
async def stream_status(
    current_user: User = Depends(get_current_user_dependency),
    user_identifier: Optional[str] = Query(None, description="Optional user identifier filter"),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve streaming status and metrics."""
    # If user_identifier provided, validate ownership
    if user_identifier:
        await validate_user_owns_session(current_user, user_identifier, db)
    
    status_payload = await run_in_threadpool(
        zerodha_streaming_manager.get_status, user_identifier
    )
    if user_identifier and not status_payload:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active stream found for user {user_identifier}",
        )
    return {"streams": status_payload}


@router.get("/stream/ticks", summary="Recent ticks from stream")
async def stream_ticks(
    current_user: User = Depends(get_current_user_dependency),
    user_identifier: str = Query(..., description="User identifier"),
    limit: int = Query(50, ge=1, le=500, description="Maximum number of ticks to return"),
    db: AsyncSession = Depends(get_db)
):
    """Return the most recent ticks captured by the streaming service."""
    # Validate ownership
    await validate_user_owns_session(current_user, user_identifier, db)
    
    try:
        ticks = await run_in_threadpool(
            zerodha_streaming_manager.get_ticks, user_identifier, limit
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return {"user_identifier": user_identifier, "ticks": ticks}


@router.get("/session/status", response_model=SessionStatusResponse, summary="Zerodha session status")
async def session_status(
    current_user: User = Depends(get_current_user_dependency),
    user_identifier: str = Query(..., description="User identifier"),
    db: AsyncSession = Depends(get_db),
):
    """Return stored session information (without decrypting tokens)."""
    session = await validate_user_owns_session(current_user, user_identifier, db)

    expires_at = session.expires_at.isoformat() if session.expires_at else None
    expires_in_minutes = None
    if session.expires_at:
        now = datetime.now(session.expires_at.tzinfo or timezone.utc)
        expires_in_minutes = (session.expires_at - now).total_seconds() / 60

    return SessionStatusResponse(
        user_identifier=session.user_identifier,
        broker=session.broker,
        status=session.status,
        has_refresh_token=session.refresh_token_encrypted is not None,
        expires_at=expires_at,
        expires_in_minutes=expires_in_minutes,
    )


@router.post("/session/validate", response_model=SessionValidationResponse, summary="Validate Zerodha access token")
async def session_validate(
    current_user: User = Depends(get_current_user_dependency),
    user_identifier: str = Query(..., description="User identifier"),
    db: AsyncSession = Depends(get_db),
):
    """
    Validate that the stored access token is currently usable by fetching the user profile.
    """
    session = await validate_user_owns_session(current_user, user_identifier, db)

    access_token = decrypt_access_token(session)
    kite = get_kite_client(access_token)

    try:
        profile = await run_in_threadpool(kite.profile)
        return SessionValidationResponse(
            status="success",
            message="Access token is valid",
            profile=profile,
        )
    except Exception as exc:
        return SessionValidationResponse(
            status="error",
            message=f"Access token validation failed: {exc}",
            profile=None,
        )


# ---------------------------------------------------------------------------
# Shutdown hook (called from FastAPI lifespan)
# ---------------------------------------------------------------------------


def stop_all_streams():
    """Utility to stop all active streams (invoked during shutdown)."""
    zerodha_streaming_manager.stop_all()


