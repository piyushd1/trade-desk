"""
Technical Analysis API Endpoints

Provides endpoints to compute and retrieve technical indicators from stored historical data.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.technical_analysis_service import TechnicalAnalysisService
from app.api.v1.auth import get_current_user_dependency
from app.models.user import User

router = APIRouter(prefix="/technical-analysis", tags=["Technical Analysis"])


# ---------------------------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------------------------


class IndicatorRequest(BaseModel):
    """
    Request model for computing technical indicators.
    
    **Authentication:** Requires JWT Bearer token
    """
    instrument_token: int = Field(
        ...,
        description="Zerodha instrument token (e.g., 408065 for INFY)",
        example=408065
    )
    interval: str = Field(
        default="day",
        description="Time interval: minute, 3minute, 5minute, 15minute, 30minute, 60minute, day",
        example="day"
    )
    indicators: Optional[List[str]] = Field(
        default=None,
        description="List of indicator names. If None, computes all indicators. Examples: ['rsi', 'macd', 'bollinger_bands']",
        example=["rsi", "macd", "bollinger_bands"]
    )
    limit: int = Field(
        default=500,
        ge=1,
        le=5000,
        description="Number of candles to fetch for computation",
        example=200
    )
    # Custom parameters for indicators
    sma_periods: Optional[List[int]] = Field(
        default=None,
        description="SMA periods (default: [20, 50, 200])",
        example=[20, 50, 200]
    )
    ema_periods: Optional[List[int]] = Field(
        default=None,
        description="EMA periods (default: [12, 26])",
        example=[12, 26]
    )
    wma_periods: Optional[List[int]] = Field(
        default=None,
        description="WMA periods (default: [9])",
        example=[9]
    )


class IndicatorListResponse(BaseModel):
    """Response model for listing available indicators."""
    momentum: List[str]
    volume: List[str]
    volatility: List[str]
    trend: List[str]
    others: List[str]


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/compute",
    summary="Compute Technical Indicators",
    description="""
    Compute technical indicators for an instrument from stored historical data.
    
    **Authentication:** Requires JWT Bearer token
    
    **Available Indicators:**
    
    **Momentum (14):**
    - `rsi` - Relative Strength Index
    - `roc` - Rate of Change
    - `awesome_oscillator` - Awesome Oscillator
    - `kama` - Kaufman's Adaptive Moving Average
    - `ppo` - Percentage Price Oscillator (returns ppo, ppo_signal, ppo_hist)
    - `stochastic` - Stochastic Oscillator (returns stoch, stoch_signal)
    - `williams_r` - Williams %R
    
    **Volume (9):**
    - `ad` - Accumulation/Distribution
    - `cmf` - Chaikin Money Flow
    - `vwap` - Volume Weighted Average Price
    - `mfi` - Money Flow Index
    - `obv` - On-Balance Volume
    
    **Volatility (5):**
    - `atr` - Average True Range
    - `bollinger_bands` - Bollinger Bands (returns bb_high, bb_mid, bb_low, bb_width, bb_pct)
    - `keltner_channel` - Keltner Channel (returns kc_high, kc_mid, kc_low)
    - `donchian_channel` - Donchian Channel (returns dc_high, dc_mid, dc_low)
    
    **Trend (15):**
    - `sma` - Simple Moving Average (customizable periods)
    - `ema` - Exponential Moving Average (customizable periods)
    - `wma` - Weighted Moving Average (customizable periods)
    - `macd` - MACD (returns macd, macd_signal, macd_diff)
    - `adx` - Average Directional Index (returns adx, adx_pos, adx_neg)
    - `aroon` - Aroon (returns aroon_up, aroon_down)
    - `cci` - Commodity Channel Index
    - `ichimoku` - Ichimoku Cloud (returns ichimoku_a, ichimoku_b, ichimoku_base, ichimoku_conversion)
    - `psar` - Parabolic SAR (returns psar, psar_up, psar_down)
    - `vortex` - Vortex Indicator (returns vortex_pos, vortex_neg)
    
    **Others (3):**
    - `daily_return` - Daily Return
    - `cumulative_return` - Cumulative Return
    
    **Usage Examples:**
    
    Compute all indicators:
    ```json
    {
      "instrument_token": 408065,
      "interval": "day",
      "limit": 200
    }
    ```
    
    Compute specific indicators:
    ```json
    {
      "instrument_token": 408065,
      "interval": "day",
      "indicators": ["rsi", "macd", "bollinger_bands", "sma"],
      "sma_periods": [20, 50, 200],
      "limit": 200
    }
    ```
    
    **Response Format:**
    ```json
    {
      "instrument_token": 408065,
      "interval": "day",
      "count": 200,
      "columns": ["open", "high", "low", "close", "volume", "oi", "rsi", "macd", ...],
      "data": [
        {
          "timestamp": "2025-11-01T00:00:00Z",
          "open": 1450.0,
          "high": 1455.0,
          "low": 1445.0,
          "close": 1452.0,
          "volume": 1000000,
          "oi": 0,
          "rsi": 55.34,
          "macd": 2.45,
          ...
        }
      ]
    }
    ```
    
    **Notes:**
    - Requires historical data to be stored in database (use `/data/zerodha/data/historical/fetch` to fetch and store)
    - Computation is done at runtime (not pre-stored)
    - Some indicators may have NaN values for initial periods (warm-up period)
    - Custom parameters allow flexibility (e.g., different MA periods)
    """,
)
async def compute_indicators(
    request: IndicatorRequest,
    current_user: User = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db),
):
    """
    Compute technical indicators for an instrument.
    
    All indicators are computed at runtime from stored OHLCV data.
    """
    service = TechnicalAnalysisService(db)
    
    # Build custom parameters
    params = {}
    if request.sma_periods:
        params['sma_periods'] = request.sma_periods
    if request.ema_periods:
        params['ema_periods'] = request.ema_periods
    if request.wma_periods:
        params['wma_periods'] = request.wma_periods
    
    # Compute indicators
    df = await service.compute_indicators(
        instrument_token=request.instrument_token,
        interval=request.interval,
        indicators=request.indicators,
        limit=request.limit,
        **params,
    )
    
    if df.empty:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No historical data found for instrument token {request.instrument_token}. "
                   f"Please fetch and store historical data first using /data/zerodha/data/historical/fetch endpoint."
        )
    
    # Convert DataFrame to JSON
    # Reset index to include timestamp in data
    result_df = df.reset_index()
    
    # Replace NaN values with None (null in JSON) to avoid JSON serialization errors
    # Technical indicators produce NaN during their "warm-up" period
    result_df = result_df.replace({float('nan'): None})
    
    result = result_df.to_dict(orient='records')
    
    return {
        "instrument_token": request.instrument_token,
        "interval": request.interval,
        "count": len(result),
        "columns": list(result_df.columns),
        "data": result,
    }


@router.get(
    "/indicators/list",
    summary="List Available Indicators",
    description="""
    List all available technical indicators categorized by type.
    
    **Authentication:** Public endpoint (no JWT required)
    
    Returns a categorized list of all indicators that can be computed using the `/compute` endpoint.
    
    **Categories:**
    - **Momentum:** Price momentum and oscillators
    - **Volume:** Volume-based indicators
    - **Volatility:** Volatility and range indicators
    - **Trend:** Trend-following indicators and moving averages
    - **Others:** Returns and performance metrics
    
    **Response Example:**
    ```json
    {
      "momentum": ["rsi", "roc", "awesome_oscillator", ...],
      "volume": ["ad", "cmf", "vwap", ...],
      "volatility": ["atr", "bollinger_bands", ...],
      "trend": ["sma", "ema", "macd", ...],
      "others": ["daily_return", "cumulative_return"]
    }
    ```
    """,
    response_model=IndicatorListResponse,
)
async def list_available_indicators():
    """
    List all available technical indicators.
    
    No authentication required - this is a reference endpoint.
    """
    return {
        "momentum": [
            "rsi",
            "roc",
            "awesome_oscillator",
            "kama",
            "ppo",
            "stochastic",
            "williams_r",
        ],
        "volume": [
            "ad",
            "cmf",
            "vwap",
            "mfi",
            "obv",
        ],
        "volatility": [
            "atr",
            "bollinger_bands",
            "keltner_channel",
            "donchian_channel",
        ],
        "trend": [
            "sma",
            "ema",
            "wma",
            "macd",
            "adx",
            "aroon",
            "cci",
            "ichimoku",
            "psar",
            "vortex",
        ],
        "others": [
            "daily_return",
            "cumulative_return",
        ]
    }

