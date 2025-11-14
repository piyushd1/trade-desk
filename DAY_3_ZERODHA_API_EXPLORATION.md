# Day 3 - Zerodha API Exploration Complete! 🎉

**Date:** November 13, 2025  
**Objective:** ✅ **ACHIEVED** - Created comprehensive APIs to fetch and explore all available Zerodha data

---

## 🗓️ Day 3 Synopsis (November 13, 2025)

- Resolved `user_id` vs `user_identifier` confusion across APIs/docs so Zerodha sessions resolve reliably.
- Hardened instrument and historical sync with strict type conversions, multi-exchange support, and consistent candle upserts (including `oi` where provided).
- Expanded data-management and order APIs with guidance so historical fetch/store flows are reproducible.
- Locked down `piyushdev.com` behind Nginx HTTP Basic Auth (`.htpasswd`) to guard every endpoint.
- Switched the Zerodha OAuth callback to return JSON, giving clear post-login feedback without the dashboard UI.

## 🎯 What Was Accomplished

### 1. **Complete Zerodha API Coverage**

Created a full suite of REST APIs that expose ALL major Zerodha Kite Connect capabilities:

#### Account & User Management
- ✅ **Profile** - User details, exchanges, products, order types
- ✅ **Margins** - Available funds, utilization, buying power

#### Portfolio Management  
- ✅ **Holdings** - Long-term equity holdings with cost basis and P&L
- ✅ **Positions** - Current day and net positions with real-time P&L

#### Order Management
- ✅ **Orders** - Complete order book with status tracking
- ✅ **Trades** - Executed trades with fill prices and timestamps

#### Market Data
- ✅ **Instruments** - All 100K+ tradable instruments (stocks, F&O, commodities)
- ✅ **Quote** - Full market quotes with 5-level depth
- ✅ **LTP** - Last traded prices (lightweight)
- ✅ **OHLC** - Open, High, Low, Close data

#### Historical Data 
- ✅ **Historical Candles** - OHLCV data from 1-minute to daily
  - Up to 60 days of minute data
  - Up to 2000 days (~5.5 years) of daily data
  - **This is GOLD for algo trading and backtesting!**

#### Streaming & Session Health
- ✅ **Session Status & Validation** - Inspect expiry, refresh capabilities, and validate tokens
- ✅ **Real-Time Streams** - Start/stop WebSocket feeds with latency metrics and tick buffers

#### Data Storage & Instrument Sync
- ✅ **Instrument Master Sync** - Persist Zerodha instruments locally
- ✅ **Historical Store** - Fetch & upsert candles into TimescaleDB/PostgreSQL
- ✅ **Fast Queries** - Query stored candles without hitting Zerodha APIs

#### Risk-Checked Order Placement
- ✅ **Order Preview** - Run risk checks + Zerodha margin calculator before placing
- ✅ **Order Execution** - Place orders with kill switch, OPS, position, and loss checks enforced
- ✅ **Modify/Cancel** - Dedicated endpoints aligned with risk logs

---

## 📚 Documentation Created

### 1. **ZERODHA_API_EXPLORATION.md**
Comprehensive 400+ line guide covering:
- All available data categories
- Detailed endpoint documentation
- Usage examples with curl commands
- Data modeling recommendations
- Application architecture suggestions

### 2. **test_zerodha_apis.sh**
Automated test script to explore all endpoints:
```bash
./test_zerodha_apis.sh YOUR_USER_ID
```

Runs tests across all categories:
- Account management
- Portfolio 
- Orders
- Market data
- Historical data
- And more!

### 3. **Backend APIs**
All endpoints available at:
```
https://piyushdev.com/api/v1/data/zerodha/*
```

---

## 🚀 Quick Start Guide

### 1. Get Your User Identifier

Your `user_identifier` is what you used as the `state` parameter during Zerodha OAuth:

```bash
# List all sessions
curl "https://piyushdev.com/api/v1/auth/zerodha/session" | python3 -m json.tool
```

### 2. Test Basic Endpoints

```bash
USER_IDENTIFIER="YOUR_ZERODHA_STATE"  # Replace with the `state` you used in OAuth

# Get profile
curl "https://piyushdev.com/api/v1/data/zerodha/profile?user_identifier=$USER_IDENTIFIER" | python3 -m json.tool

# Get account margins
curl "https://piyushdev.com/api/v1/data/zerodha/margins?user_identifier=$USER_IDENTIFIER" | python3 -m json.tool

# Get holdings
curl "https://piyushdev.com/api/v1/data/zerodha/holdings?user_identifier=$USER_IDENTIFIER" | python3 -m json.tool

# Get positions
curl "https://piyushdev.com/api/v1/data/zerodha/positions?user_identifier=$USER_IDENTIFIER" | python3 -m json.tool
```

### 3. Market Data Examples

```bash
# Get last traded price
curl -X POST "https://piyushdev.com/api/v1/data/zerodha/ltp?user_identifier=$USER_IDENTIFIER" \
  -H "Content-Type: application/json" \
  -d '["NSE:INFY", "NSE:RELIANCE", "NSE:TCS"]' | python3 -m json.tool

# Get full quote with market depth
curl -X POST "https://piyushdev.com/api/v1/data/zerodha/quote?user_identifier=$USER_IDENTIFIER" \
  -H "Content-Type: application/json" \
  -d '["NSE:INFY"]' | python3 -m json.tool

# Get OHLC
curl -X POST "https://piyushdev.com/api/v1/data/zerodha/ohlc?user_identifier=$USER_IDENTIFIER" \
  -H "Content-Type: application/json" \
  -d '["NSE:RELIANCE"]' | python3 -m json.tool
```

### 4. Start a Streaming Session

```bash
# Start stream for INFY and RELIANCE (full mode)
curl -X POST "https://piyushdev.com/api/v1/data/zerodha/stream/start" \
  -H "Content-Type: application/json" \
  -d '{
    "user_identifier": "YOUR_ID",
    "mode": "full",
    "instruments": [
      {"tradingsymbol": "INFY", "exchange": "NSE"},
      {"tradingsymbol": "RELIANCE", "exchange": "NSE"}
    ]
  }' | python3 -m json.tool

# Inspect stream metrics
curl "https://piyushdev.com/api/v1/data/zerodha/stream/status?user_identifier=YOUR_ID" | python3 -m json.tool
```

### 5. Historical Data (🔥 For Backtesting!)

```bash
# Get daily candles for INFY (instrument_token: 408065)
curl "https://piyushdev.com/api/v1/data/zerodha/historical/408065?user_identifier=$USER_IDENTIFIER&from_date=2025-10-01&to_date=2025-11-13&interval=day" | python3 -m json.tool

# Get 5-minute intraday candles
curl "https://piyushdev.com/api/v1/data/zerodha/historical/408065?user_identifier=$USER_IDENTIFIER&from_date=2025-11-01&to_date=2025-11-13&interval=5minute" | python3 -m json.tool
```

### 5. Get All Instruments

```bash
# All NSE stocks
curl "https://piyushdev.com/api/v1/data/zerodha/instruments?user_identifier=$USER_IDENTIFIER&exchange=NSE" | python3 -m json.tool > nse_instruments.json

# All instruments (100K+, large file!)
curl "https://piyushdev.com/api/v1/data/zerodha/instruments?user_identifier=$USER_IDENTIFIER" | python3 -m json.tool > all_instruments.json
```

### 6. Run Automated Test Suite

```bash
cd /home/trade-desk
./test_zerodha_apis.sh YOUR_USER_ID
```

### 7. Preview & Place an Order

```bash
# Preview order (risk + margin)
curl -X POST "https://piyushdev.com/api/v1/orders/preview" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "user_identifier": "YOUR_ID",
    "exchange": "NSE",
    "tradingsymbol": "INFY",
    "transaction_type": "BUY",
    "quantity": 1,
    "order_type": "LIMIT",
    "product": "CNC",
    "price": 1500.0,
    "price_for_risk": 1500.0
  }' | python3 -m json.tool

# Place the order (real money!)
curl -X POST "https://piyushdev.com/api/v1/orders/place" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "user_identifier": "YOUR_ID",
    "exchange": "NSE",
    "tradingsymbol": "INFY",
    "transaction_type": "BUY",
    "quantity": 1,
    "order_type": "LIMIT",
    "product": "CNC",
    "price": 1500.0,
    "price_for_risk": 1500.0
  }' | python3 -m json.tool
```

---

## 📊 Available Data Summary

| Category | Data Available | Update Frequency | Primary Use |
|----------|----------------|------------------|-------------|
| **Profile** | User details, exchanges, products | Once | Account setup |
| **Margins** | Available funds, utilization | Real-time | Pre-trade checks |
| **Holdings** | Long-term equity, cost, P&L | End of day | Portfolio tracking |
| **Positions** | Current trades, P&L | Real-time | Active monitoring |
| **Orders** | Order status, fills, rejections | Real-time | Execution tracking |
| **Trades** | Fill prices, timestamps | Real-time | Slippage analysis |
| **Instruments** | All tradable symbols | Daily | Symbol discovery |
| **Quote** | Price, depth, volume, OI | Real-time | Strategy signals |
| **LTP** | Last price only | Real-time | Quick checks |
| **OHLC** | Day's range | Real-time | Volatility calc |
| **Historical** | OHLCV candles | Historical | Backtesting |

---

## 💡 How to Model Your Application

### For Algo Trading Platform

**Priority 1: Backtesting Foundation**
```
1. Fetch instruments → Build symbol database
2. Get historical data → Store candles in database
3. Build backtesting engine → Test strategies
4. Validate performance → Optimize parameters
```

**Priority 2: Live Trading**
```
1. Real-time data pipeline → Quote/LTP streaming
2. Order management system → Place/track orders
3. Position monitoring → Real-time P&L
4. Risk management → Pre-trade checks, limits
```

**Priority 3: Portfolio Management**
```
1. Holdings tracker → Long-term positions
2. Performance analytics → Returns, XIRR
3. Tax reporting → Contract notes
4. Rebalancing automation → Based on targets
```

### Database Schema Recommendations

#### 1. Instruments Table
```sql
CREATE TABLE instruments (
    instrument_token INTEGER PRIMARY KEY,
    exchange TEXT,
    tradingsymbol TEXT,
    name TEXT,
    instrument_type TEXT,  -- EQ, FUT, CE, PE
    expiry DATE,
    strike REAL,
    lot_size INTEGER,
    tick_size REAL,
    last_updated TIMESTAMP
);
CREATE INDEX idx_symbol ON instruments(tradingsymbol);
CREATE INDEX idx_type ON instruments(instrument_type);
```

#### 2. Historical Candles Table
```sql
CREATE TABLE candles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    instrument_token INTEGER,
    interval TEXT,  -- minute, 5minute, day
    timestamp TIMESTAMP,
    open REAL,
    high REAL,
    low REAL,
    close REAL,
    volume INTEGER,
    oi INTEGER,  -- open interest for F&O
    created_at TIMESTAMP,
    UNIQUE(instrument_token, interval, timestamp)
);
CREATE INDEX idx_candles_lookup ON candles(instrument_token, interval, timestamp);
```

#### 3. Positions Snapshot Table
```sql
CREATE TABLE position_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    tradingsymbol TEXT,
    exchange TEXT,
    product TEXT,
    quantity INTEGER,
    average_price REAL,
    last_price REAL,
    pnl REAL,
    m2m REAL,
    snapshot_time TIMESTAMP,
    created_at TIMESTAMP
);
CREATE INDEX idx_snapshots ON position_snapshots(user_id, snapshot_time);
```

#### 4. Orders Table
```sql
CREATE TABLE orders (
    order_id TEXT PRIMARY KEY,
    user_id INTEGER,
    exchange_order_id TEXT,
    tradingsymbol TEXT,
    exchange TEXT,
    transaction_type TEXT,
    order_type TEXT,
    product TEXT,
    quantity INTEGER,
    price REAL,
    trigger_price REAL,
    filled_quantity INTEGER,
    pending_quantity INTEGER,
    average_price REAL,
    status TEXT,
    status_message TEXT,
    order_timestamp TIMESTAMP,
    exchange_timestamp TIMESTAMP,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
CREATE INDEX idx_orders_user ON orders(user_id, order_timestamp);
CREATE INDEX idx_orders_status ON orders(status);
```

---

## 🔥 Key Insights from Zerodha SDK

### What's Available (The Good News)

1. **Complete Market Data Access**
   - Real-time quotes with market depth
   - Historical candles (1min to daily)
   - 100K+ instruments (stocks, F&O, commodities)
   - Open interest data for F&O

2. **Comprehensive Portfolio Tracking**
   - Holdings with cost basis
   - Positions with real-time P&L
   - Complete order history
   - Trade-level execution data

3. **Risk & Margin Calculations**
   - Pre-trade margin requirements
   - Basket margin (portfolio effect)
   - Charge breakdown (brokerage, taxes, etc.)

4. **Advanced Order Types**
   - Market, Limit, SL, SL-M
   - GTT (Good Till Triggered) - 365-day orders
   - Bracket orders, Cover orders (for intraday)
   - Order modifications and cancellations

### What's NOT Available (Limitations)

1. **No Live Streaming**
   - Kite Connect API doesn't provide WebSocket streaming
   - Need to poll for real-time data (rate-limited to 3 req/sec)
   - For true streaming, need Kite Connect WebSocket (separate subscription)

2. **Historical Data Limits**
   - Minute data: Max 60 days lookback
   - Daily data: Max 2000 days (~5.5 years)
   - No tick-by-tick data

3. **Rate Limits**
   - 3 requests per second per API key
   - Violating limits → temporary IP ban

4. **Order Placement**
   - No paper trading mode (all orders are real)
   - Must implement your own paper trading engine

---

## 📝 Next Steps Recommendations

### Immediate (This Week)

1. **✅ Fetch and Store Instruments**
   ```bash
   # Download all instruments
   curl "https://piyushdev.com/api/v1/data/zerodha/instruments?user_identifier=YOUR_ID" | python3 -m json.tool > instruments.json
   
   # Parse and load into database
   python scripts/load_instruments.py
   ```

2. **✅ Build Historical Data Pipeline**
   - Create script to fetch historical candles
   - Store in database
   - Schedule daily updates

3. **✅ Design Strategy Framework**
   - Base strategy class
   - Signal generation interface
   - Backtesting harness

### Short-term (Next 2 Weeks)

4. **✅ Paper Trading Engine**
   - Simulate order execution
   - Track virtual positions
   - Calculate virtual P&L
   - Test strategies risk-free

5. **✅ Real-time Data Pipeline**
   - Poll LTP/Quote endpoints
   - Update positions
   - Generate strategy signals

6. **✅ Risk Management Integration**
   - Position limits
   - Order value limits
   - Daily loss limits
   - Pre-trade margin checks

### Medium-term (Next Month)

7. **✅ Strategy Development**
   - Implement 2-3 simple strategies
   - Backtest thoroughly
   - Optimize parameters
   - Paper trade for validation

8. **✅ Dashboard Development**
   - Real-time positions view
   - P&L tracking
   - Order management UI
   - Strategy performance metrics

9. **✅ Live Trading (with caution!)**
   - Start with smallest quantities
   - One strategy at a time
   - Monitor closely
   - Iterate based on results

---

## 🛠️ Sample Code Snippets

### Fetch and Store Historical Data

```python
import requests
from datetime import datetime, timedelta
import sqlite3

USER_IDENTIFIER = "your_zerodha_identifier"
BASE_URL = "https://piyushdev.com/api/v1/data"

def fetch_historical_candles(instrument_token, from_date, to_date, interval="day"):
    """Fetch historical candles from Zerodha API"""
    url = f"{BASE_URL}/zerodha/historical/{instrument_token}"
    params = {
        "user_identifier": USER_IDENTIFIER,
        "from_date": from_date.strftime("%Y-%m-%d"),
        "to_date": to_date.strftime("%Y-%m-%d"),
        "interval": interval
    }
    response = requests.get(url, params=params)
    return response.json()

def store_candles(instrument_token, candles):
    """Store candles in database"""
    conn = sqlite3.connect("trading.db")
    cursor = conn.cursor()
    
    for candle in candles:
        cursor.execute("""
            INSERT OR IGNORE INTO candles 
            (instrument_token, interval, timestamp, open, high, low, close, volume)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            instrument_token,
            "day",
            candle["date"],
            candle["open"],
            candle["high"],
            candle["low"],
            candle["close"],
            candle["volume"]
        ))
    
    conn.commit()
    conn.close()

# Example: Fetch INFY daily candles for last 100 days
to_date = datetime.now()
from_date = to_date - timedelta(days=100)
result = fetch_historical_candles(408065, from_date, to_date)

if result["status"] == "success":
    store_candles(408065, result["data"])
    print(f"Stored {len(result['data'])} candles")
```

### Real-time Position Monitoring

```python
import requests
import time

def monitor_positions():
    """Monitor positions and P&L in real-time"""
    while True:
        response = requests.get(
            f"{BASE_URL}/zerodha/positions",
            params={"user_identifier": USER_IDENTIFIER}
        )
        
        if response.json()["status"] == "success":
            positions = response.json()["data"]
            
            total_pnl = 0
            for pos_type in ["day", "net"]:
                for pos in positions.get(pos_type, []):
                    if pos["quantity"] != 0:
                        print(f"{pos['tradingsymbol']}: Qty={pos['quantity']}, P&L={pos['pnl']}")
                        total_pnl += pos["pnl"]
            
            print(f"Total P&L: ₹{total_pnl}\n")
        
        time.sleep(5)  # Update every 5 seconds

# Run monitoring
monitor_positions()
```

---

## 📖 Additional Resources

1. **Kite Connect Documentation**
   - https://kite.trade/docs/connect/v3/

2. **Your Backend APIs**
   - Swagger UI: https://piyushdev.com/docs
   - Health Check: https://piyushdev.com/health
   - Capabilities: https://piyushdev.com/api/v1/data/zerodha/capabilities

3. **Project Files**
   - Full Guide: `/home/trade-desk/ZERODHA_API_EXPLORATION.md`
   - Test Script: `/home/trade-desk/test_zerodha_apis.sh`
   - Backend Code: `/home/trade-desk/backend/app/api/v1/zerodha_simple.py`

---

## ✅ Summary

**You now have:**
- ✅ Complete API coverage for ALL Zerodha data types
- ✅ Real-time market quotes and positions
- ✅ Historical data for backtesting (🔥 THIS IS HUGE!)
- ✅ Order management capabilities
- ✅ Portfolio tracking
- ✅ Comprehensive documentation
- ✅ Automated test suite
- ✅ Ready-to-use backend endpoints

**What you can build:**
- 🚀 Algo trading platform with backtesting
- 📊 Portfolio management dashboard
- 🎯 Strategy development framework
- 📈 Paper trading system
- 💹 Live trading bot (with caution!)

**Your Next Move:**
1. Explore the APIs using the test script
2. Understand what data is available
3. Design your application architecture
4. Build database schema
5. Create data ingestion pipelines
6. Develop your first strategy
7. Backtest thoroughly
8. Paper trade to validate
9. Go live (carefully!)

---

**Ready to build something amazing!** 🚀

Let me know which direction you want to go:
- Backtesting engine?
- Paper trading system?
- Real-time dashboard?
- Strategy development framework?

The foundation is solid. Time to build! 💪

