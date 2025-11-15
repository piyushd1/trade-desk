# Zerodha API Exploration Guide

**Date:** November 13, 2025  
**Purpose:** Comprehensive guide to all available Zerodha Kite Connect APIs and data

---

## 🎯 Overview

This guide documents all available data and capabilities from the Zerodha Kite Connect API. Use this to understand what data you can fetch and how to model your trading application around it.

**New Endpoints:** `/api/v1/data/zerodha/*`

All data endpoints now take the Zerodha OAuth `user_identifier` (the `state` value used during login). Use this same identifier everywhere you need broker data, regardless of which TradeDesk user is calling the API.

---

## 📊 Data Categories Available

### 1. **Account & User Management**
Understand user profile, available funds, and account details.

```bash
# Get user profile
curl "https://piyushdev.com/api/v1/data/zerodha/account/profile?user_identifier=YOUR_ID" | python3 -m json.tool

# Get account margins
curl "https://piyushdev.com/api/v1/data/zerodha/account/margins?user_identifier=YOUR_ID" | python3 -m json.tool

# Get specific segment margins (equity/commodity)
curl "https://piyushdev.com/api/v1/data/zerodha/account/margins?user_identifier=YOUR_ID&segment=equity" | python3 -m json.tool
```

**What you get:**
- User ID, name, email
- Enabled exchanges (NSE, BSE, NFO, etc.)
- Available products (CNC, MIS, NRML)
- Supported order types (MARKET, LIMIT, SL, SL-M)
- Available cash, collateral, and margins
- Current utilization and exposure

**Use for:**
- User onboarding
- Displaying account info in UI
- Pre-trade checks (buying power)
- Risk management (margin monitoring)

---

### 2. **Portfolio Management**
Track holdings and positions with real-time P&L.

```bash
# Get long-term holdings (delivery)
curl "https://piyushdev.com/api/v1/data/zerodha/portfolio/holdings?user_identifier=YOUR_ID" | python3 -m json.tool

# Get current positions (intraday + overnight)
curl "https://piyushdev.com/api/v1/data/zerodha/portfolio/positions?user_identifier=YOUR_ID" | python3 -m json.tool

# Convert position (e.g., MIS to CNC)
curl -X POST "https://piyushdev.com/api/v1/data/zerodha/portfolio/convert?user_identifier=YOUR_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "exchange": "NSE",
    "tradingsymbol": "INFY",
    "transaction_type": "BUY",
    "position_type": "day",
    "quantity": 10,
    "old_product": "MIS",
    "new_product": "CNC"
  }' | python3 -m json.tool
```

**What you get:**
- **Holdings:** Long-term equity with average cost, current price, P&L
- **Positions:** Current trades with quantity, average price, realized/unrealized P&L
- Position types: Day (intraday) vs Net (overnight)
- Margin blocked per position

**Use for:**
- Portfolio valuation dashboard
- P&L tracking and reporting
- Position monitoring in real-time
- Risk exposure calculation
- Automated position management

---

### 3. **Order Management**
Complete order lifecycle from placement to execution.

```bash
# Get all orders for the day
curl "https://piyushdev.com/api/v1/data/zerodha/orders?user_identifier=YOUR_ID" | python3 -m json.tool

# Get executed trades
curl "https://piyushdev.com/api/v1/data/zerodha/trades?user_identifier=YOUR_ID" | python3 -m json.tool

# Preview order (risk checks + margin)
curl -X POST "https://piyushdev.com/api/v1/orders/preview" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "user_identifier": "YOUR_ID",
    "exchange": "NSE",
    "tradingsymbol": "INFY",
    "transaction_type": "BUY",
    "quantity": 1,
    "product": "CNC",
    "order_type": "LIMIT",
    "price": 1500.0,
    "price_for_risk": 1500.0
  }' | python3 -m json.tool

# Place order (CAREFUL - REAL MONEY!)
curl -X POST "https://piyushdev.com/api/v1/orders/place" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "user_identifier": "YOUR_ID",
    "exchange": "NSE",
    "tradingsymbol": "INFY",
    "transaction_type": "BUY",
    "quantity": 1,
    "product": "CNC",
    "order_type": "LIMIT",
    "price": 1500.0,
    "validity": "DAY",
    "tag": "test_order"
  }' | python3 -m json.tool

# Modify pending order
curl -X POST "https://piyushdev.com/api/v1/orders/modify" \
  -H "Content-Type: application/json" \
  -d '{
    "user_identifier": "YOUR_ID",
    "order_id": "ORDER_ID",
    "variety": "regular",
    "price": 1505.0,
    "quantity": 2
  }' | python3 -m json.tool

# Cancel order
curl -X POST "https://piyushdev.com/api/v1/orders/cancel" \
  -H "Content-Type: application/json" \
  -d '{
    "user_identifier": "YOUR_ID",
    "order_id": "ORDER_ID",
    "variety": "regular"
  }' | python3 -m json.tool
```

**What you get:**
- Complete order book with status (OPEN, COMPLETE, CANCELLED, REJECTED)
- Order history with all modifications
- Executed trades with prices and timestamps
- Rejection reasons (if any)
- Average execution price
- Filled vs pending quantity

**Use for:**
- Order management dashboard
- Trade execution monitoring
- Order audit trail
- Debugging failed orders
- Execution quality analysis (slippage)

---

### 4. **Market Data & Quotes**
Real-time prices, market depth, and instrument discovery.

```bash
# Get all instruments (100K+ instruments)
curl "https://piyushdev.com/api/v1/data/zerodha/market/instruments?user_identifier=YOUR_ID" | python3 -m json.tool

# Filter by exchange
curl "https://piyushdev.com/api/v1/data/zerodha/market/instruments?user_identifier=YOUR_ID&exchange=NSE" | python3 -m json.tool

# Get full quote with market depth
curl -X POST "https://piyushdev.com/api/v1/data/zerodha/market/quote?user_identifier=YOUR_ID" \
  -H "Content-Type: application/json" \
  -d '["NSE:INFY", "NSE:RELIANCE"]' | python3 -m json.tool

# Get LTP only (lightweight)
curl -X POST "https://piyushdev.com/api/v1/data/zerodha/market/ltp?user_identifier=YOUR_ID" \
  -H "Content-Type: application/json" \
  -d '["NSE:INFY", "NSE:RELIANCE", "NSE:TCS"]' | python3 -m json.tool

# Get OHLC data
curl -X POST "https://piyushdev.com/api/v1/data/zerodha/market/ohlc?user_identifier=YOUR_ID" \
  -H "Content-Type: application/json" \
  -d '["NSE:INFY", "NSE:RELIANCE"]' | python3 -m json.tool

# Get trigger range for stop-loss orders
curl -X POST "https://piyushdev.com/api/v1/data/zerodha/market/trigger-range?user_identifier=YOUR_ID" \
  -H "Content-Type: application/json" \
  -d '["NSE:INFY"]' | python3 -m json.tool

# Get auction instruments
curl "https://piyushdev.com/api/v1/data/zerodha/market/auction?user_identifier=YOUR_ID" | python3 -m json.tool
```

**What you get:**
- **Instruments:** All stocks, F&O contracts, commodities with metadata
- **Quote:** Last price, OHLC, volume, 5-level market depth, OI
- **LTP:** Just last price (for quick checks)
- **OHLC:** Day's open, high, low, close + LTP
- **Trigger Range:** Allowed SL prices (circuit limits)
- **Auction:** Pre-open/closing auction instruments

**Use for:**
- Symbol search and autocomplete
- Watchlist with real-time prices
- Market depth visualization
- Order book analysis
- Liquidity assessment
- Building option chains
- Circuit limit validation

---

### 4.5 **Real-Time Streaming & Session Health**
Stream ticks via WebSocket bridge and monitor latency.

```bash
# Check Zerodha session status (expiry, refresh token availability)
curl "https://piyushdev.com/api/v1/data/zerodha/session/status?user_identifier=YOUR_ID" | python3 -m json.tool

# Validate access token by fetching profile
curl -X POST "https://piyushdev.com/api/v1/data/zerodha/session/validate?user_identifier=YOUR_ID" | python3 -m json.tool

# Start real-time stream (FULL mode) for instruments
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

# Get stream status & latency metrics
curl "https://piyushdev.com/api/v1/data/zerodha/stream/status?user_identifier=YOUR_ID" | python3 -m json.tool

# Fetch last 20 ticks captured by the streaming manager
curl "https://piyushdev.com/api/v1/data/zerodha/stream/ticks?user_identifier=YOUR_ID&limit=20" | python3 -m json.tool

# Stop streaming
curl -X POST "https://piyushdev.com/api/v1/data/zerodha/stream/stop" \
  -H "Content-Type: application/json" \
  -d '{"user_identifier": "YOUR_ID"}' | python3 -m json.tool
```

**What you get:**
- Connection metrics (uptime, tick rate, latency stats)
- Rolling buffer of ticks with receipt timestamps
- Latency between exchange timestamp and server receipt
- Session validation utilities (status + profile check)

**Use for:**
- Measuring data arrival speed before strategy design
- Building latency dashboards
- Verifying streaming stability and reconnection behaviour

---

### 5. **Historical Data**
Time series OHLCV candles for backtesting and charting.

```bash
# Get historical data (instrument_token from instruments list)
curl "https://piyushdev.com/api/v1/data/zerodha/historical/408065?user_identifier=YOUR_ID&from_date=2025-10-01&to_date=2025-11-13&interval=day" | python3 -m json.tool

# Intraday 5-minute candles
curl "https://piyushdev.com/api/v1/data/zerodha/historical/408065?user_identifier=YOUR_ID&from_date=2025-11-01&to_date=2025-11-13&interval=5minute" | python3 -m json.tool

# F&O with open interest
curl "https://piyushdev.com/api/v1/data/zerodha/historical/408065?user_identifier=YOUR_ID&from_date=2025-11-01&to_date=2025-11-13&interval=day&oi=true" | python3 -m json.tool
```

**What you get:**
- OHLC candles at various intervals
- Volume data
- Open interest (for F&O)
- Timestamps

**Intervals available:**
- Intraday: minute, 3minute, 5minute, 10minute, 15minute, 30minute, 60minute
- Daily: day

**Limits:**
- Minute data: Max 60 days
- Day data: Max 2000 days (~5.5 years)

**Use for:**
- Backtesting trading strategies
- Technical indicator calculation
- Chart plotting
- Pattern recognition
- Strategy optimization

**🔥 This is GOLD for algo trading!**

---

### 5.5 **Historical Data Storage & Instrument Sync**
Persist Zerodha data locally (TimescaleDB / PostgreSQL) for faster analytics.

```bash
# Sync entire instrument master (exchange optional)
curl -X POST "https://piyushdev.com/api/v1/data/zerodha/data/instruments/sync" \
  -H "Content-Type: application/json" \
  -d '{
    "user_identifier": "YOUR_ID",
    "exchange": "NSE"
  }' | python3 -m json.tool

# Search locally stored instruments
curl "https://piyushdev.com/api/v1/data/zerodha/data/instruments/search?q=INFY&limit=5" | python3 -m json.tool

# Fetch and store historical candles in the database
curl -X POST "https://piyushdev.com/api/v1/data/zerodha/data/historical/fetch" \
  -H "Content-Type: application/json" \
  -d '{
    "user_identifier": "YOUR_ID",
    "instrument_token": 408065,
    "from_date": "2025-10-01T00:00:00+05:30",
    "to_date": "2025-11-13T00:00:00+05:30",
    "interval": "day",
    "oi": true
  }' | python3 -m json.tool

# Query stored candles (fast, no external API call)
curl "https://piyushdev.com/api/v1/data/zerodha/data/historical?instrument_token=408065&interval=day&limit=20" | python3 -m json.tool

# View storage stats
curl "https://piyushdev.com/api/v1/data/zerodha/data/historical/stats?instrument_token=408065&interval=day" | python3 -m json.tool
```

**What you get:**
- Local instrument master with metadata
- Historical candle store ready for backtests
- Fast SQL queries without hitting Zerodha rate limits
- Storage statistics & cleanup helpers

**Use for:**
- Building a research database
- Running backtests without repeatedly calling the broker
- Enabling advanced analytics and dashboards

---

### 6. **Mutual Funds**
MF portfolio, instruments, orders, and SIPs.

```bash
# Get MF holdings
curl "https://piyushdev.com/api/v1/data/zerodha/mf/holdings?user_identifier=YOUR_ID" | python3 -m json.tool

# Get all MF instruments (5000+ schemes)
curl "https://piyushdev.com/api/v1/data/zerodha/mf/instruments?user_identifier=YOUR_ID" | python3 -m json.tool

# Get MF orders
curl "https://piyushdev.com/api/v1/data/zerodha/mf/orders?user_identifier=YOUR_ID" | python3 -m json.tool

# Get SIPs
curl "https://piyushdev.com/api/v1/data/zerodha/mf/sips?user_identifier=YOUR_ID" | python3 -m json.tool
```

**What you get:**
- MF portfolio with folio numbers
- Units held, NAV, average cost, P&L
- All available MF schemes
- Purchase/redemption orders
- Active SIPs with schedules

**Use for:**
- MF portfolio tracking
- Asset allocation
- SIP management
- Fund discovery and screening

---

### 7. **GTT Orders (Good Till Triggered)**
Long-term trigger-based orders.

```bash
# Get all active GTTs
curl "https://piyushdev.com/api/v1/data/zerodha/gtt/list?user_identifier=YOUR_ID" | python3 -m json.tool

# Get specific GTT
curl "https://piyushdev.com/api/v1/data/zerodha/gtt/GTT_ID?user_identifier=YOUR_ID" | python3 -m json.tool

# Cancel GTT
curl -X DELETE "https://piyushdev.com/api/v1/data/zerodha/gtt/GTT_ID?user_identifier=YOUR_ID"
```

**What you get:**
- Active GTT orders
- Trigger conditions (target/stop-loss)
- Order details to execute on trigger
- Status and expiry

**GTT Features:**
- Valid for 365 days
- OCO (One Cancels Other) support
- Can have multiple legs

**Use for:**
- Long-term automated trading
- Risk management (trailing stops)
- Portfolio rebalancing triggers
- Set-and-forget strategies

---

### 8. **Margin Calculations & Risk**
Pre-trade margin checks and cost estimation.

```bash
# Calculate order margins
curl -X POST "https://piyushdev.com/api/v1/data/zerodha/margins/order-check?user_identifier=YOUR_ID" \
  -H "Content-Type: application/json" \
  -d '[{
    "exchange": "NSE",
    "tradingsymbol": "INFY",
    "transaction_type": "BUY",
    "quantity": 10,
    "price": 1500.0,
    "product": "CNC",
    "order_type": "LIMIT"
  }]' | python3 -m json.tool

# Calculate basket margins (portfolio effect)
curl -X POST "https://piyushdev.com/api/v1/data/zerodha/margins/basket-check?user_identifier=YOUR_ID" \
  -H "Content-Type: application/json" \
  -d '[{
    "exchange": "NSE",
    "tradingsymbol": "INFY",
    "transaction_type": "BUY",
    "quantity": 10,
    "price": 1500.0,
    "product": "MIS",
    "order_type": "LIMIT"
  }, {
    "exchange": "NSE",
    "tradingsymbol": "RELIANCE",
    "transaction_type": "BUY",
    "quantity": 5,
    "price": 2500.0,
    "product": "MIS",
    "order_type": "LIMIT"
  }]' | python3 -m json.tool
```

**What you get:**
- Total margin required
- Available margin
- Utilized margin
- Estimated charges (brokerage, STT, taxes, stamp duty)
- Breakdown per order
- Span margin benefit (for baskets)

**Use for:**
- Pre-trade risk checks
- Preventing margin shortage rejections
- Cost estimation before order placement
- Position sizing calculations
- Capital allocation optimization

---

### 9. **Utilities**
Contract notes and trade summaries.

```bash
# Get contract note (trade summary with charges)
curl "https://piyushdev.com/api/v1/data/zerodha/utilities/contract-note?user_identifier=YOUR_ID&from_date=2025-11-01&to_date=2025-11-13" | python3 -m json.tool

# Filter by order IDs
curl "https://piyushdev.com/api/v1/data/zerodha/utilities/contract-note?user_identifier=YOUR_ID&order_ids=ORDER1&order_ids=ORDER2" | python3 -m json.tool
```

**What you get:**
- Detailed trade summary
- Turnover calculation
- All charges breakdown:
  - Brokerage
  - STT (Securities Transaction Tax)
  - GST on brokerage
  - Exchange charges
  - SEBI turnover charges
  - Stamp duty
- Net P&L after all charges

**Use for:**
- Trade reconciliation
- Accurate P&L calculation
- Tax reporting
- Cost analysis
- Audit compliance

---

## 🚀 Complete API Capabilities Summary

Get a JSON overview of all capabilities:

```bash
curl "https://piyushdev.com/api/v1/data/zerodha/capabilities" | python3 -m json.tool
```

This returns:
- All endpoint categories
- Endpoints within each category
- Data available for modeling
- Recommended usage patterns

---

## 💡 Application Modeling Recommendations

### For Algo Trading Platform

1. **Backtesting Engine**
   - Use `/historical/*` to fetch OHLCV data
   - Support multiple timeframes (1min to daily)
   - Store locally for faster backtests

2. **Strategy Execution**
   - Use `/market/quote` or `/market/ltp` for real-time signals
   - Use `/margins/order-check` before placing orders
   - Use `/orders/place` with risk checks
   - Track using `/orders/list` and `/orders/trades`

3. **Risk Management**
   - Monitor positions using `/portfolio/positions`
   - Check margins using `/account/margins`
   - Calculate exposure using position value
   - Implement kill switch based on P&L

4. **Portfolio Dashboard**
   - Display holdings from `/portfolio/holdings`
   - Show positions with P&L from `/portfolio/positions`
   - Calculate total portfolio value
   - Track margin utilization

### For Portfolio Management

1. **Holdings Tracking**
   - Fetch holdings and positions daily
   - Store historical snapshots
   - Calculate returns and XIRR
   - Monitor asset allocation

2. **Rebalancing**
   - Use margins to check rebalancing capacity
   - Calculate required trades
   - Use basket margins for optimal execution
   - Track rebalancing P&L

3. **Reporting**
   - Use contract notes for tax reporting
   - Generate P&L statements
   - Track charges and costs
   - SEBI compliance reports

### For Paper Trading

1. **Data Pipeline**
   - Fetch instruments once daily
   - Get LTP for watchlist symbols
   - Store historical data locally
   - Update positions in your DB

2. **Virtual Order Management**
   - Simulate orders in your database
   - Use real prices for execution simulation
   - Calculate virtual P&L
   - Track paper portfolio performance

3. **Strategy Testing**
   - Test strategies risk-free
   - Validate before live trading
   - Optimize parameters
   - Build confidence in system

---

## 🎯 Key Data Points Summary

| Category | Key Data | Update Frequency | Primary Use |
|----------|----------|------------------|-------------|
| **Profile** | User details, exchanges, products | Once per session | Account info, onboarding |
| **Margins** | Available funds, utilization | Real-time | Pre-trade checks, risk mgmt |
| **Holdings** | Long-term equity, cost basis, P&L | End of day | Portfolio valuation |
| **Positions** | Current trades, realized/unrealized P&L | Real-time | Active trade monitoring |
| **Orders** | Order status, fills, rejections | Real-time | Order management |
| **Trades** | Execution prices, timestamps | Real-time | Slippage analysis |
| **Instruments** | All tradable symbols | Daily | Symbol search, discovery |
| **Quote** | Price, depth, volume, OI | Real-time | Strategy signals, monitoring |
| **LTP** | Last price only | Real-time | Quick price checks |
| **OHLC** | Day's range | Real-time | Charts, volatility |
| **Historical** | OHLCV candles | Historical | Backtesting, analysis |
| **MF Holdings** | Mutual fund portfolio | Daily | Asset allocation |
| **GTT** | Long-term triggers | Real-time | Automated trading |
| **Margins Calc** | Pre-trade requirements | On-demand | Position sizing |
| **Contract Note** | Charges breakdown | End of day | P&L, tax reporting |

---

## 🔥 Most Valuable APIs for Your Use Case

### For Building Algo Trading Platform:

**🏆 Top Priority:**
1. `/historical/*` - Backtesting (MUST HAVE)
2. `/market/quote` or `/market/ltp` - Real-time signals
3. `/orders/place` - Execution
4. `/portfolio/positions` - Position tracking
5. `/margins/order-check` - Risk checks

**🥈 Secondary:**
6. `/account/margins` - Buying power
7. `/orders/list` - Order monitoring
8. `/orders/trades` - Execution analysis
9. `/market/instruments` - Symbol discovery
10. `/utilities/contract-note` - P&L reconciliation

**🥉 Nice to Have:**
11. `/gtt/*` - Long-term automation
12. `/portfolio/holdings` - Long-term tracking
13. `/market/trigger-range` - SL validation
14. `/margins/basket-check` - Multi-leg strategies

---

## 📝 Next Steps

1. **✅ Restart backend** to load new APIs
2. **✅ Test with your Zerodha session** using `user_identifier`
3. **✅ Explore each endpoint** to see actual data structure
4. **✅ Decide which data to store** in your database
5. **✅ Design your application** around available data
6. **✅ Build data models** (SQLAlchemy models for instruments, candles, etc.)
7. **✅ Create data ingestion** pipelines
8. **✅ Implement caching** strategy (Redis for quotes, DB for historical)
9. **✅ Build WebSocket layer** for real-time data (if needed)
10. **✅ Design strategy execution** engine

---

## 🛠️ Testing Commands

### Quick Health Check

```bash
# Check if backend is running
curl https://piyushdev.com/health

# Access Swagger UI (interactive docs)
open https://piyushdev.com/docs
```

### Get Your User Identifier

Your `user_identifier` is what you used as `state` during Zerodha OAuth flow.

```bash
# List all sessions
curl "https://piyushdev.com/api/v1/auth/zerodha/session" | python3 -m json.tool

# Get specific session
curl "https://piyushdev.com/api/v1/auth/zerodha/session?user_identifier=YOUR_ID" | python3 -m json.tool
```

### Test Flow

```bash
# 1. Get profile (verify auth works)
curl "https://piyushdev.com/api/v1/data/zerodha/account/profile?user_identifier=YOUR_ID" | python3 -m json.tool

# 2. Get LTP for a stock
curl -X POST "https://piyushdev.com/api/v1/data/zerodha/market/ltp?user_identifier=YOUR_ID" \
  -H "Content-Type: application/json" \
  -d '["NSE:INFY"]' | python3 -m json.tool

# 3. Get historical data
curl "https://piyushdev.com/api/v1/data/zerodha/historical/408065?user_identifier=YOUR_ID&from_date=2025-11-01&to_date=2025-11-13&interval=day" | python3 -m json.tool

# 4. Check margins
curl "https://piyushdev.com/api/v1/data/zerodha/account/margins?user_identifier=YOUR_ID" | python3 -m json.tool

# 5. Get current positions
curl "https://piyushdev.com/api/v1/data/zerodha/portfolio/positions?user_identifier=YOUR_ID" | python3 -m json.tool
```

---

## 📚 Additional Resources

- **Kite Connect Docs:** https://kite.trade/docs/connect/v3/
- **Swagger UI:** https://piyushdev.com/docs
- **Your Backend Logs:** `/tmp/backend.log`
- **Day 2 Work Summary:** `day_2_work.md`

---

**Happy Exploring! 🚀**

The Zerodha API is incredibly comprehensive. You now have access to:
- ✅ Real-time market data
- ✅ Historical candles (1min to daily)
- ✅ Order management (place, modify, cancel)
- ✅ Portfolio tracking (holdings, positions, P&L)
- ✅ Risk calculations (margins, charges)
- ✅ Mutual funds
- ✅ GTT orders
- ✅ And much more!

**Your job now:** Decide how to model your application around this treasure trove of data! 💎

