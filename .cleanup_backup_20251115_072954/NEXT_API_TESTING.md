# Next API Testing Steps

**Current Status:** ✅ Zerodha Data APIs tested (Profile, Margins, Positions, Holdings, Orders, Trades)

---

## 📋 Testing Order

### ✅ COMPLETED
1. **Platform Authentication** - Login, profile, security checks
2. **Zerodha OAuth** - Connect, callback, session claim
3. **Zerodha Data APIs** - Profile, margins, positions, holdings, orders, trades

### 🔄 NEXT: Market Data APIs (Step 4)

**Test Script:** `./test_market_data_apis.sh`

**APIs to Test:**
1. **LTP (Last Traded Price)** - `POST /api/v1/data/zerodha/ltp`
   - Get last traded price for multiple instruments
   - Test with: `["NSE:INFY", "NSE:RELIANCE", "NSE:TCS"]`

2. **Quote** - `POST /api/v1/data/zerodha/quote`
   - Get full quote data (bid/ask, depth, etc.)
   - Test with: `["NSE:INFY"]`

3. **OHLC** - `POST /api/v1/data/zerodha/ohlc`
   - Get Open/High/Low/Close data
   - Test with: `["NSE:RELIANCE"]`

4. **Historical Data** - `GET /api/v1/data/zerodha/historical/{instrument_token}`
   - Get historical candle data
   - Test with: INFY (token: 408065), dates: 2025-11-01 to 2025-11-13

**Run:**
```bash
cd /home/trade-desk
./test_market_data_apis.sh
```

---

### 📦 STEP 5: Data Management APIs

**APIs to Test:**
1. **Sync Instruments** - `POST /api/v1/data/zerodha/data/instruments/sync`
   - Sync NSE/BSE instruments to database
   - Requires JWT

2. **Search Instruments** - `GET /api/v1/data/zerodha/data/instruments/search`
   - Search instruments in database
   - Public endpoint (no JWT)

3. **Fetch Historical** - `POST /api/v1/data/zerodha/data/historical/fetch`
   - Fetch and store historical data from Zerodha
   - Requires JWT

4. **Query Historical** - `GET /api/v1/data/zerodha/data/historical`
   - Query stored historical data from database
   - Public endpoint (no JWT)

**Manual Testing:**
```bash
# 1. Sync instruments
curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  -X POST "https://piyushdev.com/api/v1/data/zerodha/data/instruments/sync" \
  -H "Content-Type: application/json" \
  -d '{"user_identifier":"RO0252","exchange":"NSE"}' | python3 -m json.tool

# 2. Search (public)
curl -s "https://piyushdev.com/api/v1/data/zerodha/data/instruments/search?q=INFY&exchange=NSE&limit=5" | python3 -m json.tool

# 3. Fetch historical
curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  -X POST "https://piyushdev.com/api/v1/data/zerodha/data/historical/fetch" \
  -H "Content-Type: application/json" \
  -d '{
    "user_identifier": "RO0252",
    "instrument_token": 408065,
    "from_date": "2025-11-01T00:00:00",
    "to_date": "2025-11-13T23:59:59",
    "interval": "day",
    "oi": false
  }' | python3 -m json.tool

# 4. Query stored data (public)
curl -s "https://piyushdev.com/api/v1/data/zerodha/data/historical?instrument_token=408065&interval=day&limit=10" | python3 -m json.tool
```

---

### ⚠️ STEP 6: Order Management APIs (CAREFUL!)

**⚠️ WARNING:** These can place real orders with real money!

**APIs to Test:**
1. **Preview Order** - `POST /api/v1/orders/preview` ✅ SAFE
   - Preview order without placing
   - Shows margin requirements and risk checks

2. **Place Order** - `POST /api/v1/orders/place` ⚠️ REAL MONEY
   - Places actual order on exchange
   - **DO NOT TEST unless you want to trade!**

3. **Modify Order** - `POST /api/v1/orders/modify` ⚠️ REAL MONEY
   - Modifies existing order
   - **DO NOT TEST unless you want to trade!**

4. **Cancel Order** - `POST /api/v1/orders/cancel` ⚠️ REAL MONEY
   - Cancels existing order
   - **DO NOT TEST unless you want to trade!**

**Safe Testing (Preview Only):**
```bash
curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  -X POST "https://piyushdev.com/api/v1/orders/preview" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 2,
    "user_identifier": "RO0252",
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

### 🛡️ STEP 7: Risk Management APIs

**APIs to Test:**
1. **Get Risk Config** - `GET /api/v1/risk/config?user_id=2`
   - Get risk management configuration
   - Public endpoint

2. **Kill Switch Status** - `GET /api/v1/risk/kill-switch/status`
   - Check if kill switch is active
   - Public endpoint

3. **Risk Status** - `GET /api/v1/risk/status?user_id=2`
   - Get current risk status for user
   - Public endpoint

4. **Pre-trade Check** - `POST /api/v1/risk/pre-trade-check`
   - Run risk checks before placing order
   - Public endpoint

**Testing:**
```bash
# All are public endpoints, no JWT needed
curl -s "https://piyushdev.com/api/v1/risk/config?user_id=2" | python3 -m json.tool
curl -s "https://piyushdev.com/api/v1/risk/kill-switch/status" | python3 -m json.tool
curl -s "https://piyushdev.com/api/v1/risk/status?user_id=2" | python3 -m json.tool
curl -s -X POST "https://piyushdev.com/api/v1/risk/pre-trade-check" \
  -H "Content-Type: application/json" \
  -d '{"user_id": 2, "symbol": "INFY", "quantity": 1, "price": 1500.0}' | python3 -m json.tool
```

---

### 📡 STEP 8: Streaming APIs

**APIs to Test:**
1. **Start Stream** - `POST /api/v1/stream/start`
   - Start real-time data streaming
   - Requires JWT

2. **Stop Stream** - `POST /api/v1/stream/stop`
   - Stop streaming
   - Requires JWT

3. **Stream Status** - `GET /api/v1/stream/status`
   - Get streaming status
   - Requires JWT

4. **Get Ticks** - `GET /api/v1/stream/ticks`
   - Get latest tick data
   - Requires JWT

5. **Session Status** - `GET /api/v1/stream/session/status`
   - Get WebSocket session status
   - Requires JWT

6. **Validate Session** - `POST /api/v1/stream/session/validate`
   - Validate WebSocket session
   - Requires JWT

**Note:** Streaming requires WebSocket connection, may need special testing approach.

---

## 🎯 Quick Summary

**Next Immediate Step:**
```bash
cd /home/trade-desk
./test_market_data_apis.sh
```

**After Market Data:**
1. Test Data Management (sync, search, fetch, query)
2. Test Order Preview (safe)
3. Test Risk Management (all public)
4. Test Streaming (if needed)

**Total Remaining:**
- Market Data: 4 endpoints
- Data Management: 4 endpoints
- Order Management: 1 endpoint (preview only, safe)
- Risk Management: 4 endpoints
- Streaming: 6 endpoints
- **Total: ~19 endpoints remaining**

---

## 📝 Test Results Location

All test results are saved as markdown files:
- `zerodha_api_test_*.md` - Zerodha data APIs
- `market_data_test_*.md` - Market data APIs
- (Future test files will follow same pattern)

Review them in your IDE or any markdown viewer!

