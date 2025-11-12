"""
Base Broker Interface
Abstract base class for all broker integrations
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from enum import Enum
import pandas as pd
from datetime import datetime


class BrokerType(str, Enum):
    """Supported broker types"""
    ZERODHA = "zerodha"
    GROWW = "groww"


class BaseBroker(ABC):
    """
    Abstract base class for all broker integrations.
    Provides unified interface for order placement, data fetching, and WebSocket streams.
    
    All broker implementations must inherit from this class and implement all abstract methods.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize broker with configuration
        
        Args:
            config: Dictionary containing broker credentials and settings
                   {
                       "api_key": str,
                       "api_secret": str,
                       "access_token": Optional[str],
                       ...
                   }
        """
        self.config = config
        self.access_token: Optional[str] = None
        self.api_key: str = config.get('api_key', '')
        self.api_secret: str = config.get('api_secret', '')
        self.is_authenticated: bool = False
        
    @abstractmethod
    async def authenticate(self) -> bool:
        """
        Authenticate with broker and obtain access token
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def place_order(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """
        Place order with broker
        
        Args:
            order: Order parameters
                {
                    "tradingsymbol": str,
                    "exchange": str,
                    "transaction_type": str,  # "BUY" or "SELL"
                    "quantity": int,
                    "order_type": str,  # "MARKET", "LIMIT", "SL", "SL-M"
                    "price": Optional[float],
                    "product": str,  # "CNC", "MIS", "NRML"
                    "validity": str,  # "DAY", "IOC"
                    "tag": Optional[str]  # SEBI algo identifier
                }
        
        Returns:
            dict: {
                "status": "success" | "error",
                "order_id": str,
                "message": Optional[str]
            }
        """
        pass
    
    @abstractmethod
    async def cancel_order(self, order_id: str, variety: str = "regular") -> Dict[str, Any]:
        """
        Cancel existing order
        
        Args:
            order_id: Broker's order ID
            variety: Order variety (regular, co, amo, etc.)
        
        Returns:
            dict: Cancellation status
        """
        pass
    
    @abstractmethod
    async def modify_order(
        self,
        order_id: str,
        modifications: Dict[str, Any],
        variety: str = "regular"
    ) -> Dict[str, Any]:
        """
        Modify existing order
        
        Args:
            order_id: Broker's order ID
            modifications: Fields to modify (quantity, price, etc.)
            variety: Order variety
        
        Returns:
            dict: Modification status
        """
        pass
    
    @abstractmethod
    async def get_orders(self) -> List[Dict[str, Any]]:
        """
        Get all orders for the day
        
        Returns:
            list: List of order dictionaries
        """
        pass
    
    @abstractmethod
    async def get_order_history(self, order_id: str) -> List[Dict[str, Any]]:
        """
        Get order history/audit trail
        
        Args:
            order_id: Broker's order ID
        
        Returns:
            list: Order history events
        """
        pass
    
    @abstractmethod
    async def get_positions(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get current positions
        
        Returns:
            dict: {
                "net": [...],  # Net positions
                "day": [...]   # Day positions
            }
        """
        pass
    
    @abstractmethod
    async def get_holdings(self) -> List[Dict[str, Any]]:
        """
        Get holdings (delivery positions)
        
        Returns:
            list: List of holdings
        """
        pass
    
    @abstractmethod
    async def get_margins(self) -> Dict[str, Any]:
        """
        Get account margins
        
        Returns:
            dict: Margin information for all segments
        """
        pass
    
    @abstractmethod
    async def get_historical_data(
        self,
        instrument_token: str,
        from_date: str,
        to_date: str,
        interval: str
    ) -> pd.DataFrame:
        """
        Fetch historical OHLCV data
        
        Args:
            instrument_token: Instrument identifier
            from_date: Start date (YYYY-MM-DD or datetime string)
            to_date: End date (YYYY-MM-DD or datetime string)
            interval: Timeframe (minute, 5minute, day, etc.)
        
        Returns:
            DataFrame: Historical data with columns [date, open, high, low, close, volume]
        """
        pass
    
    @abstractmethod
    async def get_quote(self, instruments: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Get real-time quote for instruments
        
        Args:
            instruments: List of instrument identifiers
        
        Returns:
            dict: {instrument: quote_data}
        """
        pass
    
    @abstractmethod
    async def get_ltp(self, instruments: List[str]) -> Dict[str, float]:
        """
        Get last traded price for instruments
        
        Args:
            instruments: List of instrument identifiers
        
        Returns:
            dict: {instrument: ltp}
        """
        pass
    
    @abstractmethod
    def subscribe_live_data(
        self,
        instruments: List[str],
        callback: callable
    ) -> None:
        """
        Subscribe to live market data via WebSocket
        
        Args:
            instruments: List of instrument identifiers
            callback: Function to call when ticks are received
                     callback(ticks: List[Dict])
        """
        pass
    
    @abstractmethod
    def unsubscribe_live_data(self, instruments: List[str]) -> None:
        """
        Unsubscribe from live market data
        
        Args:
            instruments: List of instrument identifiers
        """
        pass
    
    @abstractmethod
    async def search_instruments(self, query: str, exchange: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search for instruments
        
        Args:
            query: Search query (symbol or name)
            exchange: Optional exchange filter (NSE, BSE, etc.)
        
        Returns:
            list: Matching instruments
        """
        pass
    
    # Helper methods (not abstract, can be overridden)
    
    def is_market_open(self) -> bool:
        """
        Check if market is currently open
        
        Returns:
            bool: True if market is open
        """
        # TODO: Implement market hours check
        # Consider NSE hours: 9:15 AM - 3:30 PM on weekdays
        # Exclude holidays
        return True
    
    def format_order_for_logging(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format order for audit logging
        
        Args:
            order: Order dictionary
        
        Returns:
            dict: Formatted order for logging
        """
        return {
            "symbol": order.get("tradingsymbol"),
            "exchange": order.get("exchange"),
            "type": order.get("transaction_type"),
            "quantity": order.get("quantity"),
            "order_type": order.get("order_type"),
            "price": order.get("price"),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def __repr__(self):
        return f"<{self.__class__.__name__}(authenticated={self.is_authenticated})>"

