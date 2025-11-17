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
from pydantic import BaseModel, Field, model_validator
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
    """Instrument subscription for streaming
    
    Either `instrument_token` OR `tradingsymbol` must be provided.
    If using `tradingsymbol`, `exchange` is required.
    """
    instrument_token: Optional[int] = Field(
        None, 
        description="Instrument token to subscribe to (e.g., 408065 for INFY)",
        example=408065
    )
    tradingsymbol: Optional[str] = Field(
        None, 
        description="Trading symbol (e.g., INFY, RELIANCE). Required if instrument_token not provided.",
        example="INFY"
    )
    exchange: Optional[str] = Field(
        "NSE",
        description="Exchange for the trading symbol (NSE, BSE, NFO, etc.). Required if using tradingsymbol.",
        example="NSE"
    )

    @model_validator(mode='after')
    def validate_token_or_symbol(self):
        """Ensure either instrument_token or tradingsymbol is provided."""
        if self.instrument_token is None and not self.tradingsymbol:
            raise ValueError("Either instrument_token or tradingsymbol must be provided")
        return self


class StartStreamRequest(BaseModel):
    """Request to start a real-time data stream"""
    user_identifier: str = Field(
        ..., 
        description="Zerodha OAuth user identifier (e.g., YOUR_USER_IDENTIFIER)",
        example="YOUR_USER_IDENTIFIER"
    )
    instruments: List[InstrumentSubscription] = Field(
        ..., 
        description="List of instruments to subscribe for streaming",
        example=[
            {"instrument_token": 408065},
            {"tradingsymbol": "RELIANCE", "exchange": "NSE"}
        ]
    )
    mode: str = Field(
        "full",
        description="Streaming mode: 'full' (complete tick data), 'quote' (bid/ask depth), or 'ltp' (last traded price only)",
        pattern="^(full|quote|ltp)$",
        example="ltp"
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


@router.post(
    "/stream/start", 
    summary="Start Zerodha Data Stream",
    description="""
    Start a real-time WebSocket stream for market data.
    
    **Authentication:** Requires JWT Bearer token
    
    **Parameters:**
    - `user_identifier`: Zerodha OAuth user identifier (e.g., YOUR_USER_IDENTIFIER)
    - `instruments`: Array of instruments to subscribe to. Each instrument can use:
      - `instrument_token`: Direct token (e.g., 408065)
      - `tradingsymbol` + `exchange`: Symbol and exchange (e.g., "INFY", "NSE")
    - `mode`: Streaming mode - "full" (complete data), "quote" (bid/ask), or "ltp" (last price only)
    
    **Example:**
    ```bash
    curl -X POST -H "Authorization: Bearer $ACCESS_TOKEN" \\
      -H "Content-Type: application/json" \\
      -d '{
        "user_identifier": "YOUR_USER_IDENTIFIER",
        "instruments": [
          {"instrument_token": 408065},
          {"tradingsymbol": "RELIANCE", "exchange": "NSE"}
        ],
        "mode": "ltp"
      }' \\
      "https://piyushdev.com/api/v1/data/zerodha/stream/start"
    ```
    
    **Returns:** Stream status with connection metadata and resolved instrument tokens.
    """
)
async def start_stream(
    request: StartStreamRequest,
    current_user: User = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db)
):
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


@router.get(
    "/session/status", 
    response_model=SessionStatusResponse, 
    summary="Get Zerodha Session Status",
    description="""
    Get Zerodha session information including expiry and refresh token availability.
    
    **Authentication:** Requires JWT Bearer token
    
    **Parameters:**
    - `user_identifier`: Zerodha OAuth user identifier (e.g., YOUR_USER_IDENTIFIER)
    
    **Returns:**
    - Session status (active, expired, etc.)
    - Expiry timestamp and time remaining
    - Whether refresh token is available
    
    **Example:**
    ```bash
    curl -H "Authorization: Bearer $ACCESS_TOKEN" \\
      "https://your-domain.com/api/v1/data/zerodha/session/status?user_identifier=YOUR_USER_IDENTIFIER"
    ```
    """
)
async def session_status(
    current_user: User = Depends(get_current_user_dependency),
    user_identifier: str = Query(..., description="Zerodha OAuth user identifier (e.g., YOUR_USER_IDENTIFIER)", example="YOUR_USER_IDENTIFIER"),
    db: AsyncSession = Depends(get_db),
):
    session = await validate_user_owns_session(current_user, user_identifier, db)

    expires_at = session.expires_at.isoformat() if session.expires_at else None
    expires_in_minutes = None
    if session.expires_at:
        # Handle timezone: expires_at may be naive (stored as UTC) or aware
        if session.expires_at.tzinfo is None:
            # If naive, assume it's UTC and make it timezone-aware
            expires_at_aware = session.expires_at.replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
        else:
            # If already timezone-aware, use as-is
            expires_at_aware = session.expires_at
            now = datetime.now(expires_at_aware.tzinfo)
        expires_in_minutes = (expires_at_aware - now).total_seconds() / 60

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


