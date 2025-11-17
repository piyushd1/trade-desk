"""
Fundamentals API Endpoints

REST API endpoints for fetching and managing fundamental data from Yahoo Finance.
"""

from typing import List, Optional
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.v1.auth import get_current_user_dependency
from app.services.fundamentals_service import FundamentalsService
from app.services.symbol_mapping_service import SymbolMappingService

router = APIRouter(prefix="/fundamentals", tags=["Fundamentals"])


# =====================
# Response Models
# =====================

class SymbolMappingResponse(BaseModel):
    """Symbol mapping information."""
    model_config = ConfigDict(from_attributes=True)
    
    instrument_token: int
    yfinance_symbol: str
    exchange_suffix: str
    mapping_status: str
    last_verified_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class FundamentalsResponse(BaseModel):
    """Fundamental ratios and metrics for a stock."""
    model_config = ConfigDict(from_attributes=True)
    
    instrument_token: int
    
    # Company Information
    long_name: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    full_time_employees: Optional[int] = None
    
    # Valuation Ratios
    trailing_pe: Optional[float] = Field(None, description="Price to Earnings (trailing)")
    forward_pe: Optional[float] = Field(None, description="Price to Earnings (forward)")
    price_to_book: Optional[float] = Field(None, description="Price to Book ratio")
    price_to_sales: Optional[float] = Field(None, description="Price to Sales ratio")
    enterprise_to_revenue: Optional[float] = None
    enterprise_to_ebitda: Optional[float] = None
    
    # Profitability Metrics
    trailing_eps: Optional[float] = Field(None, description="Earnings Per Share (trailing)")
    forward_eps: Optional[float] = Field(None, description="Earnings Per Share (forward)")
    earnings_quarterly_growth: Optional[float] = None
    revenue_growth: Optional[float] = None
    
    # Market Data
    market_cap: Optional[int] = Field(None, description="Market Capitalization")
    enterprise_value: Optional[int] = None
    shares_outstanding: Optional[int] = None
    float_shares: Optional[int] = None
    
    # Dividend Information
    dividend_yield: Optional[float] = None
    payout_ratio: Optional[float] = None
    trailing_annual_dividend_rate: Optional[float] = None
    trailing_annual_dividend_yield: Optional[float] = None
    
    # Performance Metrics
    fifty_two_week_high: Optional[float] = None
    fifty_two_week_low: Optional[float] = None
    beta: Optional[float] = None
    average_volume: Optional[int] = None
    average_volume_10days: Optional[int] = None
    
    # Additional Metrics
    book_value: Optional[float] = None
    profit_margins: Optional[float] = None
    return_on_assets: Optional[float] = None
    return_on_equity: Optional[float] = None
    
    # Meta
    data_source: str
    data_date: date
    updated_at: datetime


class AnalystDataResponse(BaseModel):
    """Analyst recommendations and estimates for a stock."""
    model_config = ConfigDict(from_attributes=True)
    
    instrument_token: int
    data_date: date
    
    # Target Price Data
    target_mean_price: Optional[float] = None
    target_high_price: Optional[float] = None
    target_low_price: Optional[float] = None
    target_median_price: Optional[float] = None
    current_price: Optional[float] = None
    
    # Analyst Recommendations
    recommendation_mean: Optional[float] = Field(None, description="1.0=Strong Buy, 5.0=Sell")
    recommendation_key: Optional[str] = Field(None, description="buy, hold, sell, etc.")
    number_of_analyst_opinions: Optional[int] = None
    
    # Recommendation Breakdown
    strong_buy_count: Optional[int] = None
    buy_count: Optional[int] = None
    hold_count: Optional[int] = None
    sell_count: Optional[int] = None
    strong_sell_count: Optional[int] = None
    
    # Earnings Estimates
    current_quarter_estimate: Optional[float] = None
    next_quarter_estimate: Optional[float] = None
    current_year_estimate: Optional[float] = None
    next_year_estimate: Optional[float] = None
    
    # Revenue Estimates
    current_quarter_revenue_estimate: Optional[int] = None
    next_quarter_revenue_estimate: Optional[int] = None
    current_year_revenue_estimate: Optional[int] = None
    next_year_revenue_estimate: Optional[int] = None
    
    # Earnings Calendar
    earnings_date: Optional[date] = None
    earnings_average: Optional[float] = None
    earnings_low: Optional[float] = None
    earnings_high: Optional[float] = None
    
    # Meta
    data_source: str
    updated_at: datetime


class BulkFetchRequest(BaseModel):
    """Request model for bulk fetching fundamentals."""
    instrument_tokens: List[int] = Field(..., description="List of instrument tokens")
    include_analyst: bool = Field(default=False, description="Also fetch analyst data")


class BulkFetchResponse(BaseModel):
    """Response model for bulk fetch operations."""
    success: int
    failed: int
    skipped: int
    total: int


class MappingSyncRequest(BaseModel):
    """Request model for syncing symbol mappings."""
    exchange: str = Field(..., description="Exchange code (NSE, BSE, etc.)")
    limit: Optional[int] = Field(None, description="Optional limit on instruments to process")


# =====================
# API Endpoints
# =====================

@router.get("/{instrument_token}", response_model=FundamentalsResponse)
async def get_fundamentals(
    instrument_token: int,
    force_refresh: bool = Query(default=False, description="Bypass cache and fetch fresh data"),
    current_user=Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db),
):
    """
    Get fundamental ratios and metrics for a stock.
    
    Returns cached data if fresh (< 24 hours old), otherwise fetches from Yahoo Finance.
    
    **Authentication:** Requires JWT Bearer token.
    
    **Example:**
    ```bash
    curl -H "Authorization: Bearer $TOKEN" \
      "https://piyushdev.com/api/v1/fundamentals/408065"
    ```
    """
    service = FundamentalsService(db)
    
    fundamentals = await service.get_fundamentals(instrument_token, force_refresh=force_refresh)
    
    if not fundamentals:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Could not fetch fundamentals for instrument {instrument_token}. "
                   f"Ensure the instrument exists and has a valid Yahoo Finance mapping."
        )
    
    return fundamentals


@router.get("/{instrument_token}/analyst", response_model=AnalystDataResponse)
async def get_analyst_data(
    instrument_token: int,
    force_refresh: bool = Query(default=False, description="Fetch fresh analyst data"),
    current_user=Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db),
):
    """
    Get analyst recommendations and estimates for a stock.
    
    Includes target prices, buy/sell recommendations, and earnings estimates.
    
    **Authentication:** Requires JWT Bearer token.
    
    **Example:**
    ```bash
    curl -H "Authorization: Bearer $TOKEN" \
      "https://piyushdev.com/api/v1/fundamentals/408065/analyst"
    ```
    """
    service = FundamentalsService(db)
    
    analyst_data = await service.get_analyst_data(instrument_token, force_refresh=force_refresh)
    
    if not analyst_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Could not fetch analyst data for instrument {instrument_token}. "
                   f"Data may not be available for this stock."
        )
    
    return analyst_data


@router.post("/fetch")
async def force_fetch_fundamentals(
    instrument_token: int = Query(..., description="Instrument token to fetch"),
    include_analyst: bool = Query(default=False, description="Also fetch analyst data"),
    current_user=Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db),
):
    """
    Force fetch fresh fundamental data from Yahoo Finance (bypass cache).
    
    Use this endpoint when you need the latest data and don't want to rely on cached values.
    
    **Authentication:** Requires JWT Bearer token.
    
    **Example:**
    ```bash
    curl -X POST -H "Authorization: Bearer $TOKEN" \
      "https://piyushdev.com/api/v1/fundamentals/fetch?instrument_token=408065&include_analyst=true"
    ```
    """
    service = FundamentalsService(db)
    
    # Fetch fundamentals
    fundamentals = await service.get_fundamentals(instrument_token, force_refresh=True)
    
    if not fundamentals:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Could not fetch fundamentals for instrument {instrument_token}"
        )
    
    # Optionally fetch analyst data
    analyst_data = None
    if include_analyst:
        analyst_data = await service.get_analyst_data(instrument_token, force_refresh=True)
    
    return {
        "message": "Fundamentals fetched successfully",
        "instrument_token": instrument_token,
        "fundamentals_updated": True,
        "analyst_data_updated": analyst_data is not None,
    }


@router.post("/bulk-fetch", response_model=BulkFetchResponse)
async def bulk_fetch_fundamentals(
    request: BulkFetchRequest,
    current_user=Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db),
):
    """
    Fetch fundamentals for multiple stocks in bulk.
    
    Useful for updating fundamentals for a portfolio or watchlist.
    Automatically skips stocks with fresh data (< 24 hours old).
    
    **Authentication:** Requires JWT Bearer token.
    
    **Example:**
    ```bash
    curl -X POST -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "instrument_tokens": [408065, 738561, 2953217],
        "include_analyst": true
      }' \
      "https://piyushdev.com/api/v1/fundamentals/bulk-fetch"
    ```
    """
    service = FundamentalsService(db)
    
    result = await service.bulk_fetch_fundamentals(
        request.instrument_tokens,
        include_analyst=request.include_analyst
    )
    
    return result


@router.get("/mapping/{instrument_token}", response_model=SymbolMappingResponse)
async def get_symbol_mapping(
    instrument_token: int,
    current_user=Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db),
):
    """
    Get or create symbol mapping for an instrument.
    
    Shows how Zerodha instrument tokens map to Yahoo Finance symbols.
    
    **Authentication:** Requires JWT Bearer token.
    
    **Example:**
    ```bash
    curl -H "Authorization: Bearer $TOKEN" \
      "https://piyushdev.com/api/v1/fundamentals/mapping/408065"
    ```
    """
    service = SymbolMappingService(db)
    
    mapping = await service.get_or_create_mapping(instrument_token)
    
    if not mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Instrument {instrument_token} not found in database. "
                   f"Please sync instruments first using /data/zerodha/data/instruments/sync"
        )
    
    return mapping


@router.post("/mapping/sync")
async def sync_symbol_mappings(
    request: MappingSyncRequest,
    current_user=Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db),
):
    """
    Bulk sync symbol mappings for an exchange.
    
    Creates mappings for all instruments in the specified exchange.
    Useful for initial setup or after syncing new instruments.
    
    **Authentication:** Requires JWT Bearer token.
    
    **Example:**
    ```bash
    curl -X POST -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d '{"exchange": "NSE", "limit": 100}' \
      "https://piyushdev.com/api/v1/fundamentals/mapping/sync"
    ```
    """
    service = SymbolMappingService(db)
    
    result = await service.bulk_create_mappings(
        exchange=request.exchange,
        limit=request.limit
    )
    
    return {
        "message": f"Symbol mapping sync complete for {request.exchange}",
        "exchange": request.exchange,
        **result
    }

