# 05 - Broker Integration & Data Management

[← Back to Master PRD](MASTER_PRD.md)

---

## 📊 Overview

This document details the integration with broker APIs (Zerodha Kite Connect and Groww Trade API), data management strategies, rate limiting implementation, and real-time data streaming architecture.

---

## 🔌 Broker Integration Architecture

### Multi-Broker Abstraction Layer

```python
# brokers/base_broker.py

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from enum import Enum

class BrokerType(Enum):
    ZERODHA = "zerodha"
    GROWW = "groww"

class BaseBroker(ABC):
    """
    Abstract base class for all broker integrations.
    Provides unified interface for order placement, data fetching, and WebSocket streams.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.access_token = None
        self.api_key = config.get('api_key')
        self.api_secret = config.get('api_secret')
        
    @abstractmethod
    async def authenticate(self) -> bool:
        """Authenticate with broker and obtain access token"""
        pass
    
    @abstractmethod
    async def place_order(self, order: Dict) -> Dict:
        """Place order with broker"""
        pass
    
    @abstractmethod
    async def cancel_order(self, order_id: str) -> Dict:
        """Cancel existing order"""
        pass
    
    @abstractmethod
    async def modify_order(self, order_id: str, modifications: Dict) -> Dict:
        """Modify existing order"""
        pass
    
    @abstractmethod
    async def get_orders(self) -> List[Dict]:
        """Get all orders for the day"""
        pass
    
    @abstractmethod
    async def get_positions(self) -> List[Dict]:
        """Get current positions"""
        pass
    
    @abstractmethod
    async def get_holdings(self) -> List[Dict]:
        """Get holdings"""
        pass
    
    @abstractmethod
    async def get_historical_data(
        self, 
        instrument_token: str,
        from_date: str,
        to_date: str,
        interval: str
    ) -> pd.DataFrame:
        """Fetch historical OHLCV data"""
        pass
    
    @abstractmethod
    async def get_quote(self, instruments: List[str]) -> Dict:
        """Get real-time quote for instruments"""
        pass
    
    @abstractmethod
    async def get_ltp(self, instruments: List[str]) -> Dict:
        """Get last traded price for instruments"""
        pass
    
    @abstractmethod
    def subscribe_live_data(self, instruments: List[str], callback: callable):
        """Subscribe to live market data via WebSocket"""
        pass
```

---

## 🔷 Zerodha Kite Connect Integration

### API Configuration

| Parameter | Value | Notes |
|-----------|-------|-------|
| **Base URL** | `https://api.kite.trade` | Production endpoint |
| **Login URL** | `https://kite.zerodha.com/connect/login` | OAuth initiation |
| **WebSocket URL** | `wss://ws.kite.trade` | Live data streaming |
| **API Cost** | ₹2,000/month | Required subscription |
| **Historical Data** | ₹2,000/month | Additional add-on |
| **Total Cost** | ₹4,000/month | - |

### Rate Limits

| Resource | Rate Limit | Notes |
|----------|-----------|-------|
| **Global API** | 10 requests/second | All API calls |
| **Historical Data** | 3 requests/second | 120 requests/minute |
| **Order Placement** | 200/minute | Account-level RMS limit |
| **Order Placement** | 2,000/day | Account-level RMS limit |
| **WebSocket** | 3,000 instruments | Max subscriptions |
| **WebSocket** | 3 connections | Max concurrent |

### Authentication Flow

```python
# brokers/zerodha_broker.py

import hashlib
from kiteconnect import KiteConnect

class ZerodhaBroker(BaseBroker):
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.kite = KiteConnect(api_key=self.api_key)
        self.request_token = None
        
    async def authenticate(self) -> bool:
        """
        OAuth 2.0 Authentication Flow
        
        Step 1: Generate login URL
        Step 2: User logs in and authorizes
        Step 3: Exchange request_token for access_token
        """
        try:
            # Step 1: Get login URL (done manually)
            login_url = self.kite.login_url()
            print(f"Login URL: {login_url}")
            
            # Step 2: User authorizes and we get request_token
            # This is obtained from redirect URL after user login
            
            # Step 3: Generate access token
            data = self.kite.generate_session(
                self.request_token, 
                api_secret=self.api_secret
            )
            
            self.access_token = data["access_token"]
            self.kite.set_access_token(self.access_token)
            
            # Store encrypted access token in database
            await self.store_token_encrypted(self.access_token)
            
            return True
            
        except Exception as e:
            logger.error(f"Zerodha authentication failed: {e}")
            return False
    
    async def place_order(self, order: Dict) -> Dict:
        """
        Place order through Zerodha Kite Connect
        
        Args:
            order: {
                "tradingsymbol": "INFY",
                "exchange": "NSE",
                "transaction_type": "BUY",
                "quantity": 10,
                "order_type": "LIMIT",
                "price": 1450.50,
                "product": "CNC",
                "validity": "DAY",
                "tag": "algo_strategy_001"  # SEBI requirement
            }
        """
        try:
            # Apply rate limiting
            await self.check_rate_limit('order_placement')
            
            # Place order
            order_id = self.kite.place_order(
                variety=self.kite.VARIETY_REGULAR,
                exchange=order['exchange'],
                tradingsymbol=order['tradingsymbol'],
                transaction_type=order['transaction_type'],
                quantity=order['quantity'],
                order_type=order['order_type'],
                price=order.get('price'),
                product=order['product'],
                validity=order.get('validity', 'DAY'),
                tag=order.get('tag', '')  # Algo identifier
            )
            
            # Log to audit trail (SEBI requirement)
            await self.log_order_to_audit_trail(order_id, order)
            
            return {
                "status": "success",
                "order_id": order_id,
                "broker": "zerodha"
            }
            
        except Exception as e:
            logger.error(f"Order placement failed: {e}")
            return {
                "status": "error",
                "message": str(e),
                "broker": "zerodha"
            }
    
    async def get_historical_data(
        self,
        instrument_token: str,
        from_date: str,
        to_date: str,
        interval: str
    ) -> pd.DataFrame:
        """
        Fetch historical OHLCV data from Zerodha
        
        Args:
            instrument_token: Numeric token (e.g., "408065" for INFY)
            from_date: "2024-01-01 09:15:00"
            to_date: "2024-01-31 15:30:00"
            interval: "minute", "5minute", "15minute", "60minute", "day"
        
        Returns:
            DataFrame with columns: [date, open, high, low, close, volume]
        
        Note: Historical data limits per request:
            - 1min: 60 days
            - 5min: 100 days
            - 60min: 400 days
            - day: 2000 days
        """
        try:
            # Apply rate limiting (3 req/sec for historical data)
            await self.check_rate_limit('historical_data')
            
            # Fetch data
            data = self.kite.historical_data(
                instrument_token=instrument_token,
                from_date=from_date,
                to_date=to_date,
                interval=interval
            )
            
            # Convert to DataFrame
            df = pd.DataFrame(data)
            
            # Cache the data
            await self.cache_historical_data(
                instrument_token, from_date, to_date, interval, df
            )
            
            return df
            
        except Exception as e:
            logger.error(f"Historical data fetch failed: {e}")
            return pd.DataFrame()
```

### WebSocket Implementation

```python
# brokers/zerodha_websocket.py

from kiteconnect import KiteTicker

class ZerodhaWebSocket:
    
    def __init__(self, api_key: str, access_token: str):
        self.kws = KiteTicker(api_key, access_token)
        self.subscriptions = []
        
        # Set callbacks
        self.kws.on_ticks = self.on_ticks
        self.kws.on_connect = self.on_connect
        self.kws.on_close = self.on_close
        self.kws.on_error = self.on_error
        self.kws.on_reconnect = self.on_reconnect
        self.kws.on_noreconnect = self.on_noreconnect
        
    def on_ticks(self, ws, ticks):
        """
        Callback when ticks are received
        
        Tick structure:
        {
            'instrument_token': 408065,
            'timestamp': datetime,
            'last_price': 1450.5,
            'last_quantity': 100,
            'buy_quantity': 5000,
            'sell_quantity': 4500,
            'volume': 125000,
            'ohlc': {
                'open': 1445.0,
                'high': 1455.0,
                'low': 1440.0,
                'close': 1448.5
            }
        }
        """
        # Process ticks
        for tick in ticks:
            # Update Redis cache
            self.update_tick_cache(tick)
            
            # Emit to WebSocket server for frontend
            self.emit_to_frontend(tick)
            
            # Trigger strategy evaluation if needed
            self.trigger_strategy_check(tick)
    
    def on_connect(self, ws, response):
        """Called when WebSocket connection is established"""
        logger.info("Zerodha WebSocket connected")
        
        # Subscribe to instruments
        if self.subscriptions:
            ws.subscribe(self.subscriptions)
            ws.set_mode(ws.MODE_FULL, self.subscriptions)
    
    def subscribe(self, instrument_tokens: List[int]):
        """
        Subscribe to instruments
        
        Note: Max 3,000 instruments per connection
        """
        if len(instrument_tokens) > 3000:
            raise ValueError("Max 3000 instruments allowed per connection")
            
        self.subscriptions = instrument_tokens
        self.kws.subscribe(instrument_tokens)
        self.kws.set_mode(self.kws.MODE_FULL, instrument_tokens)
    
    def start(self):
        """Start WebSocket connection"""
        self.kws.connect(threaded=True)
    
    def stop(self):
        """Stop WebSocket connection"""
        self.kws.close()
```

---

## 🟢 Groww Trade API Integration

### API Configuration

| Parameter | Value | Notes |
|-----------|-------|-------|
| **Base URL** | `https://api.groww.in` | Production endpoint |
| **WebSocket URL** | `wss://ws.groww.in` | Live data streaming |
| **Auth Method 1** | Access Token | Daily expiry at 6 AM |
| **Auth Method 2** | TOTP | No expiry (recommended) |
| **API Cost** | Included in trading | No additional cost |

### Rate Limits

| Resource | Rate Limit | Notes |
|----------|-----------|-------|
| **Order Placement** | 15/second | Per account |
| **Order Placement** | 250/minute | Per account |
| **Order Placement** | 3,000/day | Per account |
| **Live Data** | 10/second | Better than Zerodha |
| **Live Data** | 300/minute | - |
| **Live Data** | 5,000/day | - |
| **WebSocket** | 1,000 instruments | Max subscriptions |

### Authentication Flow

```python
# brokers/groww_broker.py

import pyotp
from groww_trade_api import Groww

class GrowwBroker(BaseBroker):
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.groww = Groww()
        self.totp_secret = config.get('totp_secret')
        
    async def authenticate_with_totp(self) -> bool:
        """
        Authenticate using TOTP (Recommended)
        
        Advantages:
        - No token expiry
        - More secure
        - No daily re-authentication needed
        """
        try:
            # Generate TOTP
            totp = pyotp.TOTP(self.totp_secret)
            otp_code = totp.now()
            
            # Login with TOTP
            self.groww.login(
                api_key=self.api_key,
                api_secret=self.api_secret,
                totp=otp_code
            )
            
            # Store session
            await self.store_session()
            
            return True
            
        except Exception as e:
            logger.error(f"Groww TOTP authentication failed: {e}")
            return False
    
    async def authenticate_with_token(self) -> bool:
        """
        Authenticate using Access Token
        
        Note: Token expires daily at 6 AM
        Requires daily regeneration from Groww portal
        """
        try:
            access_token = self.config.get('access_token')
            
            self.groww.set_access_token(access_token)
            
            return True
            
        except Exception as e:
            logger.error(f"Groww token authentication failed: {e}")
            return False
    
    async def place_order(self, order: Dict) -> Dict:
        """
        Place order through Groww Trade API
        
        Better rate limits compared to Zerodha:
        - 15/second vs 200/minute
        """
        try:
            # Apply rate limiting
            await self.check_rate_limit('order_placement')
            
            # Place order
            response = self.groww.place_order(
                symbol=order['symbol'],
                exchange=order['exchange'],
                transaction_type=order['transaction_type'],
                quantity=order['quantity'],
                order_type=order['order_type'],
                price=order.get('price'),
                product=order['product'],
                validity=order.get('validity', 'DAY'),
                tag=order.get('tag', '')
            )
            
            # Log to audit trail
            await self.log_order_to_audit_trail(response['order_id'], order)
            
            return {
                "status": "success",
                "order_id": response['order_id'],
                "broker": "groww"
            }
            
        except Exception as e:
            logger.error(f"Groww order placement failed: {e}")
            return {
                "status": "error",
                "message": str(e),
                "broker": "groww"
            }
```

---

## 📈 Historical Data Management

### Data Fetching Strategy

```python
# data/historical_data_manager.py

class HistoricalDataManager:
    
    def __init__(self, broker: BaseBroker):
        self.broker = broker
        self.cache = Redis()
        self.db = PostgreSQL()
        
    async def get_historical_data(
        self,
        symbol: str,
        from_date: str,
        to_date: str,
        interval: str,
        force_fetch: bool = False
    ) -> pd.DataFrame:
        """
        Get historical data with smart caching
        
        Priority:
        1. Check Redis cache (for recent data)
        2. Check PostgreSQL/TimescaleDB (for older data)
        3. Fetch from broker API (if not available)
        """
        
        # Generate cache key
        cache_key = f"historical:{symbol}:{from_date}:{to_date}:{interval}"
        
        # Check Redis cache (TTL: 1 hour for recent data)
        if not force_fetch:
            cached_data = await self.cache.get(cache_key)
            if cached_data:
                logger.info(f"Cache hit for {symbol}")
                return pd.read_json(cached_data)
        
        # Check database
        db_data = await self.db.query_historical_data(
            symbol, from_date, to_date, interval
        )
        
        if not db_data.empty and not force_fetch:
            logger.info(f"Database hit for {symbol}")
            # Cache in Redis
            await self.cache.setex(
                cache_key, 
                3600,  # 1 hour TTL
                db_data.to_json()
            )
            return db_data
        
        # Fetch from broker
        logger.info(f"Fetching from broker for {symbol}")
        data = await self.broker.get_historical_data(
            symbol, from_date, to_date, interval
        )
        
        # Store in database
        await self.db.store_historical_data(data, symbol, interval)
        
        # Cache in Redis
        await self.cache.setex(cache_key, 3600, data.to_json())
        
        return data
    
    async def bulk_fetch_historical_data(
        self,
        symbols: List[str],
        from_date: str,
        to_date: str,
        interval: str
    ) -> Dict[str, pd.DataFrame]:
        """
        Fetch historical data for multiple symbols
        Respects rate limits
        """
        results = {}
        
        for symbol in symbols:
            try:
                # Apply rate limiting
                await self.broker.check_rate_limit('historical_data')
                
                # Fetch data
                data = await self.get_historical_data(
                    symbol, from_date, to_date, interval
                )
                
                results[symbol] = data
                
                # Small delay to respect rate limits
                await asyncio.sleep(0.35)  # ~3 req/sec for Zerodha
                
            except Exception as e:
                logger.error(f"Failed to fetch {symbol}: {e}")
                results[symbol] = pd.DataFrame()
        
        return results
```

### Data Storage Schema

```sql
-- TimescaleDB schema for historical data

CREATE TABLE market_data (
    id BIGSERIAL,
    symbol VARCHAR(50) NOT NULL,
    exchange VARCHAR(10) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    open DECIMAL(15, 2),
    high DECIMAL(15, 2),
    low DECIMAL(15, 2),
    close DECIMAL(15, 2),
    volume BIGINT,
    interval VARCHAR(10),  -- 'minute', '5minute', 'day', etc.
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    PRIMARY KEY (symbol, timestamp, interval)
);

-- Convert to TimescaleDB hypertable
SELECT create_hypertable('market_data', 'timestamp');

-- Create indexes
CREATE INDEX idx_market_data_symbol ON market_data(symbol);
CREATE INDEX idx_market_data_timestamp ON market_data(timestamp DESC);
CREATE INDEX idx_market_data_symbol_interval ON market_data(symbol, interval, timestamp DESC);

-- Enable compression (older data)
ALTER TABLE market_data SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'symbol,exchange,interval',
    timescaledb.compress_orderby = 'timestamp DESC'
);

-- Compress data older than 30 days
SELECT add_compression_policy('market_data', INTERVAL '30 days');
```

---

## ⚡ Rate Limiting Implementation

### Rate Limiter Service

```python
# services/rate_limiter.py

import asyncio
from datetime import datetime, timedelta
from collections import deque

class RateLimiter:
    """
    Token bucket rate limiter with multiple bucket support
    """
    
    def __init__(self):
        self.buckets = {
            'zerodha': {
                'global': TokenBucket(rate=10, period=1),  # 10/sec
                'historical_data': TokenBucket(rate=3, period=1),  # 3/sec
                'order_placement': TokenBucket(rate=200, period=60),  # 200/min
                'order_placement_daily': TokenBucket(rate=2000, period=86400),  # 2000/day
            },
            'groww': {
                'order_placement': TokenBucket(rate=15, period=1),  # 15/sec
                'order_placement_min': TokenBucket(rate=250, period=60),  # 250/min
                'order_placement_daily': TokenBucket(rate=3000, period=86400),  # 3000/day
                'live_data': TokenBucket(rate=10, period=1),  # 10/sec
            }
        }
    
    async def acquire(self, broker: str, resource: str):
        """
        Acquire token from rate limiter
        Blocks until token is available
        """
        bucket = self.buckets[broker][resource]
        await bucket.acquire()
    
    def check_available(self, broker: str, resource: str) -> bool:
        """Check if token is available without acquiring"""
        bucket = self.buckets[broker][resource]
        return bucket.available()


class TokenBucket:
    """
    Token bucket algorithm implementation
    """
    
    def __init__(self, rate: int, period: float):
        """
        Args:
            rate: Number of tokens per period
            period: Time period in seconds
        """
        self.rate = rate
        self.period = period
        self.tokens = rate
        self.last_update = datetime.now()
        self.lock = asyncio.Lock()
    
    def _refill(self):
        """Refill tokens based on time elapsed"""
        now = datetime.now()
        elapsed = (now - self.last_update).total_seconds()
        
        # Calculate tokens to add
        tokens_to_add = elapsed * (self.rate / self.period)
        
        self.tokens = min(self.rate, self.tokens + tokens_to_add)
        self.last_update = now
    
    async def acquire(self):
        """Acquire a token, wait if necessary"""
        async with self.lock:
            while True:
                self._refill()
                
                if self.tokens >= 1:
                    self.tokens -= 1
                    return
                
                # Calculate wait time
                wait_time = (1 - self.tokens) * (self.period / self.rate)
                await asyncio.sleep(wait_time)
    
    def available(self) -> bool:
        """Check if token is available"""
        self._refill()
        return self.tokens >= 1
```

### Rate Limit Monitoring

```python
# monitoring/rate_limit_monitor.py

class RateLimitMonitor:
    """
    Monitor rate limit usage and send alerts
    """
    
    def __init__(self):
        self.usage_stats = {}
        
    async def record_request(self, broker: str, resource: str):
        """Record API request for monitoring"""
        key = f"{broker}:{resource}"
        
        if key not in self.usage_stats:
            self.usage_stats[key] = {
                'count': 0,
                'window_start': datetime.now(),
                'limit': self.get_limit(broker, resource)
            }
        
        self.usage_stats[key]['count'] += 1
        
        # Check if approaching limit (80%)
        usage = self.usage_stats[key]
        if usage['count'] >= usage['limit'] * 0.8:
            await self.send_alert(
                f"Rate limit warning: {key} at {usage['count']}/{usage['limit']}"
            )
    
    async def get_usage_report(self) -> Dict:
        """Get current usage statistics"""
        report = {}
        
        for key, stats in self.usage_stats.items():
            report[key] = {
                'count': stats['count'],
                'limit': stats['limit'],
                'percentage': (stats['count'] / stats['limit']) * 100,
                'window_start': stats['window_start']
            }
        
        return report
```

---

## 🌐 Real-time Data Streaming

### WebSocket Server for Frontend

```python
# websocket/realtime_server.py

import socketio
from aiohttp import web

class RealtimeServer:
    """
    WebSocket server to broadcast real-time data to frontend
    """
    
    def __init__(self):
        self.sio = socketio.AsyncServer(
            async_mode='aiohttp',
            cors_allowed_origins='*'
        )
        self.app = web.Application()
        self.sio.attach(self.app)
        
        # Register event handlers
        self.sio.on('connect', self.on_connect)
        self.sio.on('disconnect', self.on_disconnect)
        self.sio.on('subscribe', self.on_subscribe)
        self.sio.on('unsubscribe', self.on_unsubscribe)
        
        # Client subscriptions
        self.subscriptions = {}  # {sid: [symbols]}
    
    async def on_connect(self, sid, environ):
        """Client connected"""
        logger.info(f"Client {sid} connected")
        self.subscriptions[sid] = []
    
    async def on_disconnect(self, sid):
        """Client disconnected"""
        logger.info(f"Client {sid} disconnected")
        if sid in self.subscriptions:
            del self.subscriptions[sid]
    
    async def on_subscribe(self, sid, data):
        """
        Client subscribes to symbols
        
        Data: {
            "symbols": ["NSE:INFY", "NSE:SBIN"]
        }
        """
        symbols = data.get('symbols', [])
        
        if sid not in self.subscriptions:
            self.subscriptions[sid] = []
        
        self.subscriptions[sid].extend(symbols)
        
        logger.info(f"Client {sid} subscribed to {symbols}")
        
        # Send initial data
        for symbol in symbols:
            quote = await self.get_latest_quote(symbol)
            await self.sio.emit('tick', quote, room=sid)
    
    async def broadcast_tick(self, tick: Dict):
        """
        Broadcast tick to all subscribed clients
        
        Tick: {
            "symbol": "NSE:INFY",
            "last_price": 1450.5,
            "timestamp": "2025-11-11 10:30:00",
            ...
        }
        """
        symbol = tick['symbol']
        
        # Find clients subscribed to this symbol
        for sid, symbols in self.subscriptions.items():
            if symbol in symbols:
                await self.sio.emit('tick', tick, room=sid)
    
    async def broadcast_order_update(self, order: Dict):
        """Broadcast order updates to relevant clients"""
        user_id = order['user_id']
        
        # Find client sessions for this user
        # (User can have multiple active sessions)
        for sid, user in self.user_sessions.items():
            if user == user_id:
                await self.sio.emit('order_update', order, room=sid)
    
    def run(self, host='0.0.0.0', port=8001):
        """Start WebSocket server"""
        web.run_app(self.app, host=host, port=port)
```

---

## 💾 Data Caching Strategy

### Redis Cache Architecture

```python
# cache/redis_cache.py

class MarketDataCache:
    """
    Redis-based caching for market data
    """
    
    def __init__(self):
        self.redis = Redis(
            host='localhost',
            port=6379,
            db=0,
            decode_responses=True
        )
    
    async def cache_quote(self, symbol: str, quote: Dict, ttl: int = 60):
        """
        Cache latest quote
        
        Key pattern: quote:{symbol}
        TTL: 60 seconds
        """
        key = f"quote:{symbol}"
        await self.redis.setex(key, ttl, json.dumps(quote))
    
    async def get_quote(self, symbol: str) -> Optional[Dict]:
        """Get cached quote"""
        key = f"quote:{symbol}"
        data = await self.redis.get(key)
        return json.loads(data) if data else None
    
    async def cache_ohlc(self, symbol: str, interval: str, ohlc: Dict):
        """
        Cache OHLC data for specific interval
        
        Key pattern: ohlc:{symbol}:{interval}
        """
        key = f"ohlc:{symbol}:{interval}"
        await self.redis.setex(key, 300, json.dumps(ohlc))  # 5 min TTL
    
    async def cache_order_book(self, symbol: str, order_book: Dict):
        """
        Cache order book (depth)
        
        Key pattern: depth:{symbol}
        TTL: 5 seconds (very recent data)
        """
        key = f"depth:{symbol}"
        await self.redis.setex(key, 5, json.dumps(order_book))
    
    async def cache_positions(self, user_id: int, positions: List[Dict]):
        """
        Cache user positions
        
        Key pattern: positions:{user_id}
        TTL: 60 seconds
        """
        key = f"positions:{user_id}"
        await self.redis.setex(key, 60, json.dumps(positions))
```

---

## 📊 Data Quality & Validation

### Data Validator

```python
# validators/data_validator.py

class DataValidator:
    """
    Validate incoming market data for anomalies
    """
    
    @staticmethod
    def validate_ohlc(data: Dict) -> bool:
        """
        Validate OHLC data for consistency
        
        Rules:
        - High >= Open, Close, Low
        - Low <= Open, Close, High
        - Volume >= 0
        - Prices > 0
        """
        try:
            high = float(data['high'])
            low = float(data['low'])
            open_price = float(data['open'])
            close = float(data['close'])
            volume = int(data['volume'])
            
            # Basic validations
            if high < low:
                logger.warning(f"Invalid OHLC: high < low")
                return False
            
            if high < open_price or high < close:
                logger.warning(f"Invalid OHLC: high < open/close")
                return False
            
            if low > open_price or low > close:
                logger.warning(f"Invalid OHLC: low > open/close")
                return False
            
            if volume < 0:
                logger.warning(f"Invalid volume: {volume}")
                return False
            
            if any(p <= 0 for p in [high, low, open_price, close]):
                logger.warning(f"Invalid prices: negative or zero")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Data validation error: {e}")
            return False
    
    @staticmethod
    def detect_circuit_filter(
        current_price: float,
        previous_close: float,
        circuit_limit: float = 0.20
    ) -> bool:
        """
        Detect if stock hit circuit filter
        
        Args:
            current_price: Current market price
            previous_close: Previous day closing
            circuit_limit: Circuit filter percentage (default 20%)
        
        Returns:
            True if circuit filter hit
        """
        change_pct = abs(current_price - previous_close) / previous_close
        
        if change_pct >= circuit_limit:
            logger.warning(
                f"Circuit filter detected: {change_pct*100:.2f}% change"
            )
            return True
        
        return False
```

---

## 🔄 Data Synchronization

### Background Data Sync Service

```python
# services/data_sync_service.py

class DataSyncService:
    """
    Background service to keep historical data up-to-date
    """
    
    def __init__(self):
        self.broker = None  # Will be initialized
        self.scheduler = BackgroundScheduler()
        
    async def sync_daily_data(self):
        """
        Sync daily OHLC data for all tracked instruments
        Runs every day after market close (3:45 PM)
        """
        logger.info("Starting daily data sync")
        
        # Get list of tracked instruments
        instruments = await self.get_tracked_instruments()
        
        # Yesterday's date
        date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        for instrument in instruments:
            try:
                # Fetch daily data
                data = await self.broker.get_historical_data(
                    instrument['token'],
                    from_date=date,
                    to_date=date,
                    interval='day'
                )
                
                # Store in database
                await self.store_daily_data(instrument['symbol'], data)
                
                logger.info(f"Synced daily data for {instrument['symbol']}")
                
                # Rate limiting
                await asyncio.sleep(0.35)
                
            except Exception as e:
                logger.error(f"Failed to sync {instrument['symbol']}: {e}")
    
    def start(self):
        """Start background sync scheduler"""
        # Schedule daily sync at 3:45 PM (after market close)
        self.scheduler.add_job(
            self.sync_daily_data,
            trigger='cron',
            hour=15,
            minute=45,
            day_of_week='mon-fri'
        )
        
        self.scheduler.start()
        logger.info("Data sync service started")
```

---

## 📋 Summary

### Key Decisions

| Decision | Rationale |
|----------|-----------|
| **Multi-broker abstraction** | Future-proof, easy to add new brokers |
| **Redis caching** | Fast access to frequently used data |
| **TimescaleDB** | Optimized for time-series data |
| **Token bucket rate limiting** | Smooth request distribution |
| **On-demand fetching** | Avoid unnecessary API calls and costs |
| **WebSocket for real-time** | Low latency market data streaming |

### Data Flow

```
Broker API (Zerodha/Groww)
    ↓
Rate Limiter
    ↓
Data Validator
    ↓
Redis Cache (Fast access)
    ↓
TimescaleDB (Persistent storage)
    ↓
WebSocket Server
    ↓
Frontend (Real-time updates)
```

---

**Next:** [Risk Management System →](06_RISK_MANAGEMENT.md)

---

*Last Updated: November 11, 2025*
