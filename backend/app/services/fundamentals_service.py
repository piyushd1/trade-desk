"""
Fundamentals Service

Fetches and stores fundamental data from Yahoo Finance.
Implements caching, rate limiting, and error handling.
"""

from typing import Dict, Optional, List, Any
from datetime import datetime, date, timezone, timedelta
from decimal import Decimal
import logging
import asyncio

import yfinance as yf
from requests import Session
from requests_cache import CacheMixin, SQLiteCache
from requests_ratelimiter import LimiterMixin, MemoryQueueBucket
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from app.models.fundamentals import StockFundamentals, StockAnalystData
from app.services.symbol_mapping_service import SymbolMappingService

logger = logging.getLogger(__name__)


class CachedLimiterSession(CacheMixin, LimiterMixin, Session):
    """
    Custom session that combines caching and rate limiting.
    
    This prevents triggering Yahoo Finance's rate limiter by:
    - Caching responses at the HTTP level
    - Limiting requests to 1 per second
    """
    pass


class FundamentalsService:
    """Service for fetching and managing fundamental data from Yahoo Finance."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.symbol_mapping_service = SymbolMappingService(db)
        self.cache_ttl_hours = 24  # Default cache TTL
        self.rate_limit_delay = 0.5  # Reduced delay since we have request-level rate limiting
        
        # Create cached and rate-limited session for yfinance
        # This prevents triggering Yahoo Finance's 429 rate limiter
        self.session = CachedLimiterSession(
            per_second=1.0,  # Max 1 request per second
            bucket_class=MemoryQueueBucket,
            backend=SQLiteCache("/tmp/yfinance.cache", expire_after=3600),  # 1-hour HTTP cache
        )
        logger.info("FundamentalsService initialized with cached rate-limited session")
    
    def _safe_decimal(self, value: Any, precision: int = 2) -> Optional[Decimal]:
        """Safely convert value to Decimal."""
        if value is None or value == "":
            return None
        try:
            if isinstance(value, (int, float)):
                return Decimal(str(round(value, precision)))
            return Decimal(str(value))
        except (ValueError, TypeError, ArithmeticError):
            return None

    def _safe_int(self, value: Any) -> Optional[int]:
        """Safely convert value to int."""
        if value is None or value == "":
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None

    def _safe_date(self, value: Any) -> Optional[date]:
        """Safely convert value to date."""
        if value is None:
            return None
        try:
            if isinstance(value, datetime):
                return value.date()
            elif isinstance(value, date):
                return value
            # Try parsing string
            return datetime.fromisoformat(str(value)).date()
        except (ValueError, TypeError, AttributeError):
            return None
    
    async def _is_data_fresh(self, instrument_token: int) -> bool:
        """
        Check if cached fundamental data is still fresh.
        
        Args:
            instrument_token: Zerodha instrument token
        
        Returns:
            True if data is fresh (< cache_ttl_hours old), False otherwise
        """
        stmt = select(StockFundamentals).where(
            StockFundamentals.instrument_token == instrument_token
        )
        result = await self.db.execute(stmt)
        fundamentals = result.scalar_one_or_none()
        
        if not fundamentals:
            return False
        
        # Check if data is older than cache TTL
        age = datetime.now(timezone.utc) - fundamentals.updated_at.replace(tzinfo=timezone.utc)
        return age.total_seconds() < (self.cache_ttl_hours * 3600)
    
    def _extract_fundamentals_from_info(self, info: Dict[str, Any], instrument_token: int) -> Dict[str, Any]:
        """
        Extract fundamental data from yfinance info dict.
        
        Args:
            info: Dictionary from yf.Ticker().info
            instrument_token: Zerodha instrument token
        
        Returns:
            Dictionary of fundamental data ready for database
        """
        return {
            "instrument_token": instrument_token,
            "long_name": info.get("longName"),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "full_time_employees": self._safe_int(info.get("fullTimeEmployees")),
            
            # Valuation Ratios
            "trailing_pe": self._safe_decimal(info.get("trailingPE")),
            "forward_pe": self._safe_decimal(info.get("forwardPE")),
            "price_to_book": self._safe_decimal(info.get("priceToBook")),
            "price_to_sales": self._safe_decimal(info.get("priceToSalesTrailing12Months")),
            "enterprise_to_revenue": self._safe_decimal(info.get("enterpriseToRevenue")),
            "enterprise_to_ebitda": self._safe_decimal(info.get("enterpriseToEbitda")),
            
            # Profitability
            "trailing_eps": self._safe_decimal(info.get("trailingEps")),
            "forward_eps": self._safe_decimal(info.get("forwardEps")),
            "earnings_quarterly_growth": self._safe_decimal(info.get("earningsQuarterlyGrowth"), precision=4),
            "revenue_growth": self._safe_decimal(info.get("revenueGrowth"), precision=4),
            
            # Market Data
            "market_cap": self._safe_int(info.get("marketCap")),
            "enterprise_value": self._safe_int(info.get("enterpriseValue")),
            "shares_outstanding": self._safe_int(info.get("sharesOutstanding")),
            "float_shares": self._safe_int(info.get("floatShares")),
            
            # Dividends
            "dividend_yield": self._safe_decimal(info.get("dividendYield"), precision=4),
            "payout_ratio": self._safe_decimal(info.get("payoutRatio"), precision=4),
            "trailing_annual_dividend_rate": self._safe_decimal(info.get("trailingAnnualDividendRate")),
            "trailing_annual_dividend_yield": self._safe_decimal(info.get("trailingAnnualDividendYield"), precision=4),
            
            # Performance
            "fifty_two_week_high": self._safe_decimal(info.get("fiftyTwoWeekHigh")),
            "fifty_two_week_low": self._safe_decimal(info.get("fiftyTwoWeekLow")),
            "beta": self._safe_decimal(info.get("beta"), precision=3),
            "average_volume": self._safe_int(info.get("averageVolume")),
            "average_volume_10days": self._safe_int(info.get("averageDailyVolume10Day")),
            
            # Additional
            "book_value": self._safe_decimal(info.get("bookValue")),
            "profit_margins": self._safe_decimal(info.get("profitMargins"), precision=4),
            "return_on_assets": self._safe_decimal(info.get("returnOnAssets"), precision=4),
            "return_on_equity": self._safe_decimal(info.get("returnOnEquity"), precision=4),
            
            "data_source": "yfinance",
            "data_date": date.today(),
        }
    
    def _extract_analyst_data(self, ticker: yf.Ticker, instrument_token: int) -> Optional[Dict[str, Any]]:
        """
        Extract analyst data from yfinance Ticker object.
        
        Args:
            ticker: yfinance Ticker object
            instrument_token: Zerodha instrument token
        
        Returns:
            Dictionary of analyst data or None if not available
        """
        try:
            info = ticker.info
            
            # Get recommendations if available
            recommendations = None
            try:
                recs = ticker.recommendations
                if recs is not None and not recs.empty:
                    recommendations = recs
            except Exception as e:
                logger.debug(f"Could not fetch recommendations: {e}")
            
            # Extract analyst data
            analyst_data = {
                "instrument_token": instrument_token,
                "data_date": date.today(),
                
                # Target Price
                "target_mean_price": self._safe_decimal(info.get("targetMeanPrice")),
                "target_high_price": self._safe_decimal(info.get("targetHighPrice")),
                "target_low_price": self._safe_decimal(info.get("targetLowPrice")),
                "target_median_price": self._safe_decimal(info.get("targetMedianPrice")),
                "current_price": self._safe_decimal(info.get("currentPrice")),
                
                # Recommendations
                "recommendation_mean": self._safe_decimal(info.get("recommendationMean")),
                "recommendation_key": info.get("recommendationKey"),
                "number_of_analyst_opinions": self._safe_int(info.get("numberOfAnalystOpinions")),
                
                # Earnings Estimates (if available from calendar)
                "current_quarter_estimate": None,
                "next_quarter_estimate": None,
                "current_year_estimate": None,
                "next_year_estimate": None,
                
                # Revenue Estimates
                "current_quarter_revenue_estimate": None,
                "next_quarter_revenue_estimate": None,
                "current_year_revenue_estimate": None,
                "next_year_revenue_estimate": None,
                
                # Earnings Calendar
                "earnings_date": None,
                "earnings_average": None,
                "earnings_low": None,
                "earnings_high": None,
                
                "data_source": "yfinance",
            }
            
            # Try to get earnings calendar
            try:
                calendar = ticker.calendar
                if calendar is not None and not calendar.empty:
                    if "Earnings Date" in calendar:
                        earnings_dates = calendar["Earnings Date"]
                        if len(earnings_dates) > 0:
                            analyst_data["earnings_date"] = self._safe_date(earnings_dates[0])
                    if "Earnings Average" in calendar:
                        analyst_data["earnings_average"] = self._safe_decimal(calendar["Earnings Average"])
                    if "Earnings Low" in calendar:
                        analyst_data["earnings_low"] = self._safe_decimal(calendar["Earnings Low"])
                    if "Earnings High" in calendar:
                        analyst_data["earnings_high"] = self._safe_decimal(calendar["Earnings High"])
            except Exception as e:
                logger.debug(f"Could not fetch earnings calendar: {e}")
            
            return analyst_data
            
        except Exception as e:
            logger.error(f"Error extracting analyst data: {e}")
            return None
    
    async def fetch_fundamentals_from_yfinance(
        self,
        yfinance_symbol: str,
        instrument_token: int
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch fundamental data from Yahoo Finance.
        
        Args:
            yfinance_symbol: Yahoo Finance symbol (e.g., "RELIANCE.NS")
            instrument_token: Zerodha instrument token
        
        Returns:
            Dictionary of fundamental data or None if fetch failed
        """
        try:
            logger.info(f"Fetching fundamentals for {yfinance_symbol}")
            
            # Small delay for safety (session handles rate limiting)
            await asyncio.sleep(self.rate_limit_delay)
            
            # Fetch data from yfinance using our cached rate-limited session
            ticker = yf.Ticker(yfinance_symbol, session=self.session)
            info = ticker.info
            
            if not info or len(info) < 5:
                logger.warning(f"No data returned from yfinance for {yfinance_symbol}")
                return None
            
            # Extract fundamentals
            fundamentals = self._extract_fundamentals_from_info(info, instrument_token)
            
            logger.info(f"Successfully fetched fundamentals for {yfinance_symbol}")
            return fundamentals
            
        except Exception as e:
            logger.error(f"Error fetching fundamentals for {yfinance_symbol}: {e}")
            return None
    
    async def store_fundamentals(self, fundamentals_data: Dict[str, Any]) -> Optional[StockFundamentals]:
        """
        Store fundamental data in database (upsert).
        
        Args:
            fundamentals_data: Dictionary of fundamental data
        
        Returns:
            Stored StockFundamentals object or None
        """
        try:
            # Try SQLite insert first
            try:
                stmt = sqlite_insert(StockFundamentals).values(fundamentals_data)
                stmt = stmt.on_conflict_do_update(
                    index_elements=["instrument_token"],
                    set_={k: v for k, v in fundamentals_data.items() if k != "instrument_token"}
                )
            except Exception:
                # Fallback for PostgreSQL
                stmt = pg_insert(StockFundamentals).values(fundamentals_data)
                stmt = stmt.on_conflict_do_update(
                    constraint="stock_fundamentals_pkey",
                    set_={k: v for k, v in fundamentals_data.items() if k != "instrument_token"}
                )
            
            await self.db.execute(stmt)
            await self.db.commit()
            
            # Fetch and return the stored data
            stmt = select(StockFundamentals).where(
                StockFundamentals.instrument_token == fundamentals_data["instrument_token"]
            )
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Error storing fundamentals: {e}")
            await self.db.rollback()
            return None
    
    async def get_fundamentals(
        self,
        instrument_token: int,
        force_refresh: bool = False
    ) -> Optional[StockFundamentals]:
        """
        Get fundamental data for an instrument.
        
        Checks cache first, fetches from yfinance if needed.
        
        Args:
            instrument_token: Zerodha instrument token
            force_refresh: If True, bypass cache and fetch fresh data
        
        Returns:
            StockFundamentals object or None
        """
        # Check cache unless force_refresh is True
        if not force_refresh:
            if await self._is_data_fresh(instrument_token):
                logger.debug(f"Using cached fundamentals for {instrument_token}")
                stmt = select(StockFundamentals).where(
                    StockFundamentals.instrument_token == instrument_token
                )
                result = await self.db.execute(stmt)
                return result.scalar_one_or_none()
        
        # Get Yahoo Finance symbol
        yfinance_symbol = await self.symbol_mapping_service.get_yfinance_symbol(instrument_token)
        if not yfinance_symbol:
            logger.warning(f"Could not map instrument {instrument_token} to Yahoo Finance symbol")
            return None
        
        # Fetch from yfinance
        fundamentals_data = await self.fetch_fundamentals_from_yfinance(
            yfinance_symbol,
            instrument_token
        )
        
        if not fundamentals_data:
            return None
        
        # Store in database
        return await self.store_fundamentals(fundamentals_data)
    
    async def get_analyst_data(
        self,
        instrument_token: int,
        force_refresh: bool = False
    ) -> Optional[StockAnalystData]:
        """
        Get analyst data for an instrument.
        
        Args:
            instrument_token: Zerodha instrument token
            force_refresh: If True, fetch fresh data
        
        Returns:
            StockAnalystData object or None
        """
        # Check cache unless force_refresh
        if not force_refresh:
            stmt = select(StockAnalystData).where(
                StockAnalystData.instrument_token == instrument_token,
                StockAnalystData.data_date == date.today()
            )
            result = await self.db.execute(stmt)
            cached_data = result.scalar_one_or_none()
            if cached_data:
                logger.debug(f"Using cached analyst data for {instrument_token}")
                return cached_data
        
        # Get Yahoo Finance symbol
        yfinance_symbol = await self.symbol_mapping_service.get_yfinance_symbol(instrument_token)
        if not yfinance_symbol:
            return None
        
        try:
            # Add delay for rate limiting
            await asyncio.sleep(self.rate_limit_delay)
            
            # Fetch from yfinance using our cached rate-limited session
            ticker = yf.Ticker(yfinance_symbol, session=self.session)
            analyst_data_dict = self._extract_analyst_data(ticker, instrument_token)
            
            if not analyst_data_dict:
                return None
            
            # Store in database
            analyst_data = StockAnalystData(**analyst_data_dict)
            self.db.add(analyst_data)
            await self.db.commit()
            await self.db.refresh(analyst_data)
            
            return analyst_data
            
        except Exception as e:
            logger.error(f"Error fetching analyst data for {yfinance_symbol}: {e}")
            return None
    
    async def bulk_fetch_fundamentals(
        self,
        instrument_tokens: List[int],
        include_analyst: bool = False
    ) -> Dict[str, int]:
        """
        Fetch fundamentals for multiple instruments.
        
        Args:
            instrument_tokens: List of Zerodha instrument tokens
            include_analyst: Whether to also fetch analyst data
        
        Returns:
            Summary dictionary with counts of successful/failed fetches
        """
        success_count = 0
        failed_count = 0
        skipped_count = 0
        
        for instrument_token in instrument_tokens:
            try:
                # Check if data is already fresh
                if await self._is_data_fresh(instrument_token):
                    skipped_count += 1
                    continue
                
                # Fetch fundamentals
                fundamentals = await self.get_fundamentals(instrument_token, force_refresh=True)
                
                if fundamentals:
                    success_count += 1
                    
                    # Optionally fetch analyst data
                    if include_analyst:
                        await self.get_analyst_data(instrument_token, force_refresh=True)
                else:
                    failed_count += 1
                
                # Log progress
                if (success_count + failed_count) % 10 == 0:
                    logger.info(f"Progress: {success_count} success, {failed_count} failed, {skipped_count} skipped")
                    
            except Exception as e:
                logger.error(f"Error processing instrument {instrument_token}: {e}")
                failed_count += 1
        
        logger.info(f"Bulk fetch complete: {success_count} success, {failed_count} failed, {skipped_count} skipped")
        
        return {
            "success": success_count,
            "failed": failed_count,
            "skipped": skipped_count,
            "total": len(instrument_tokens),
        }

