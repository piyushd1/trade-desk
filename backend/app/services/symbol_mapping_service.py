"""
Symbol Mapping Service

Maps Zerodha instrument tokens to Yahoo Finance symbols for fundamental data fetching.
Handles NSE/BSE exchange suffixes and caches mappings in the database.
"""

from typing import Dict, Optional, List
from datetime import datetime, timezone
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from app.models.fundamentals import SymbolMapping
from app.models.market_data import Instrument

logger = logging.getLogger(__name__)


class SymbolMappingService:
    """Service for managing Zerodha to Yahoo Finance symbol mappings."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    @staticmethod
    def _get_exchange_suffix(exchange: str) -> str:
        """
        Get Yahoo Finance suffix for an exchange.
        
        Args:
            exchange: Exchange code (NSE, BSE, etc.)
        
        Returns:
            Yahoo Finance suffix (.NS, .BO, etc.)
        """
        exchange_map = {
            "NSE": ".NS",
            "BSE": ".BO",
            # Add more exchanges as needed
            # "NFO": ".NS",  # Futures & Options on NSE
            # "BFO": ".BO",  # Futures & Options on BSE
        }
        return exchange_map.get(exchange.upper(), ".NS")  # Default to NSE
    
    @staticmethod
    def _create_yfinance_symbol(tradingsymbol: str, exchange: str) -> str:
        """
        Create Yahoo Finance symbol from Zerodha trading symbol and exchange.
        
        Args:
            tradingsymbol: Zerodha trading symbol (e.g., "RELIANCE")
            exchange: Exchange code (e.g., "NSE")
        
        Returns:
            Yahoo Finance symbol (e.g., "RELIANCE.NS")
        """
        # Clean the tradingsymbol (remove special characters that might cause issues)
        clean_symbol = tradingsymbol.strip().upper()
        
        # Get the appropriate suffix
        suffix = SymbolMappingService._get_exchange_suffix(exchange)
        
        return f"{clean_symbol}{suffix}"
    
    async def get_instrument(self, instrument_token: int) -> Optional[Instrument]:
        """
        Get instrument details from database.
        
        Args:
            instrument_token: Zerodha instrument token
        
        Returns:
            Instrument object or None if not found
        """
        stmt = select(Instrument).where(Instrument.instrument_token == instrument_token)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_mapping(self, instrument_token: int) -> Optional[SymbolMapping]:
        """
        Get existing symbol mapping from database.
        
        Args:
            instrument_token: Zerodha instrument token
        
        Returns:
            SymbolMapping object or None if not found
        """
        stmt = select(SymbolMapping).where(SymbolMapping.instrument_token == instrument_token)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def create_mapping(
        self,
        instrument_token: int,
        tradingsymbol: str,
        exchange: str,
        verify: bool = False
    ) -> SymbolMapping:
        """
        Create a new symbol mapping.
        
        Args:
            instrument_token: Zerodha instrument token
            tradingsymbol: Zerodha trading symbol
            exchange: Exchange code
            verify: Whether to verify the mapping with yfinance
        
        Returns:
            Created SymbolMapping object
        """
        yfinance_symbol = self._create_yfinance_symbol(tradingsymbol, exchange)
        exchange_suffix = self._get_exchange_suffix(exchange)
        
        mapping_status = "active"
        last_verified_at = None
        
        if verify:
            # Optionally verify with yfinance (can be implemented later)
            # For now, we'll just mark it as active
            last_verified_at = datetime.now(timezone.utc)
        
        # Use upsert to handle duplicates
        mapping_data = {
            "instrument_token": instrument_token,
            "yfinance_symbol": yfinance_symbol,
            "exchange_suffix": exchange_suffix,
            "mapping_status": mapping_status,
            "last_verified_at": last_verified_at,
        }
        
        # Try SQLite insert first, fall back to generic
        try:
            stmt = sqlite_insert(SymbolMapping).values(mapping_data)
            stmt = stmt.on_conflict_do_update(
                index_elements=["instrument_token"],
                set_={
                    "yfinance_symbol": yfinance_symbol,
                    "exchange_suffix": exchange_suffix,
                    "mapping_status": mapping_status,
                    "last_verified_at": last_verified_at,
                    "updated_at": datetime.now(timezone.utc),
                }
            )
        except Exception:
            # Fallback for PostgreSQL or other databases
            stmt = pg_insert(SymbolMapping).values(mapping_data)
            stmt = stmt.on_conflict_do_update(
                constraint="symbol_mapping_pkey",
                set_={
                    "yfinance_symbol": yfinance_symbol,
                    "exchange_suffix": exchange_suffix,
                    "mapping_status": mapping_status,
                    "last_verified_at": last_verified_at,
                    "updated_at": datetime.now(timezone.utc),
                }
            )
        
        await self.db.execute(stmt)
        await self.db.commit()
        
        # Fetch and return the mapping
        return await self.get_mapping(instrument_token)
    
    async def get_or_create_mapping(
        self,
        instrument_token: int
    ) -> Optional[SymbolMapping]:
        """
        Get existing mapping or create a new one.
        
        Args:
            instrument_token: Zerodha instrument token
        
        Returns:
            SymbolMapping object or None if instrument not found
        """
        # Check if mapping already exists
        mapping = await self.get_mapping(instrument_token)
        if mapping:
            logger.debug(f"Found existing mapping: {instrument_token} -> {mapping.yfinance_symbol}")
            return mapping
        
        # Get instrument details
        instrument = await self.get_instrument(instrument_token)
        if not instrument:
            logger.warning(f"Instrument {instrument_token} not found in database")
            return None
        
        # Create new mapping
        logger.info(f"Creating new mapping for {instrument.tradingsymbol} ({instrument_token})")
        mapping = await self.create_mapping(
            instrument_token=instrument_token,
            tradingsymbol=instrument.tradingsymbol,
            exchange=instrument.exchange
        )
        
        return mapping
    
    async def get_yfinance_symbol(self, instrument_token: int) -> Optional[str]:
        """
        Get Yahoo Finance symbol for an instrument token.
        
        Args:
            instrument_token: Zerodha instrument token
        
        Returns:
            Yahoo Finance symbol (e.g., "RELIANCE.NS") or None
        """
        mapping = await self.get_or_create_mapping(instrument_token)
        if mapping:
            return mapping.yfinance_symbol
        return None
    
    async def bulk_create_mappings(
        self,
        exchange: Optional[str] = None,
        limit: Optional[int] = None
    ) -> Dict:
        """
        Create mappings for multiple instruments.
        
        Args:
            exchange: Optional exchange filter (NSE, BSE, etc.)
            limit: Optional limit on number of instruments to process
        
        Returns:
            Dictionary with summary of created mappings
        """
        # Build query
        stmt = select(Instrument)
        if exchange:
            stmt = stmt.where(Instrument.exchange == exchange.upper())
        if limit:
            stmt = stmt.limit(limit)
        
        result = await self.db.execute(stmt)
        instruments = result.scalars().all()
        
        created_count = 0
        failed_count = 0
        skipped_count = 0
        
        for instrument in instruments:
            try:
                # Check if mapping already exists
                existing = await self.get_mapping(instrument.instrument_token)
                if existing:
                    skipped_count += 1
                    continue
                
                # Create mapping
                await self.create_mapping(
                    instrument_token=instrument.instrument_token,
                    tradingsymbol=instrument.tradingsymbol,
                    exchange=instrument.exchange
                )
                created_count += 1
                
                # Log progress every 100 instruments
                if created_count % 100 == 0:
                    logger.info(f"Created {created_count} mappings...")
                    
            except Exception as e:
                logger.error(f"Failed to create mapping for {instrument.instrument_token}: {e}")
                failed_count += 1
        
        logger.info(f"Bulk mapping complete: {created_count} created, {skipped_count} skipped, {failed_count} failed")
        
        return {
            "created": created_count,
            "skipped": skipped_count,
            "failed": failed_count,
            "total_processed": created_count + skipped_count + failed_count,
        }
    
    async def update_mapping_status(
        self,
        instrument_token: int,
        status: str
    ) -> Optional[SymbolMapping]:
        """
        Update the status of a symbol mapping.
        
        Args:
            instrument_token: Zerodha instrument token
            status: New status (active, invalid, not_found)
        
        Returns:
            Updated SymbolMapping object or None
        """
        mapping = await self.get_mapping(instrument_token)
        if not mapping:
            return None
        
        mapping.mapping_status = status
        mapping.updated_at = datetime.now(timezone.utc)
        
        await self.db.commit()
        await self.db.refresh(mapping)
        
        return mapping

