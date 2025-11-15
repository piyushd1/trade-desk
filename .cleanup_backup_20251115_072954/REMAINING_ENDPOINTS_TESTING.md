# Remaining Endpoints Testing Guide

**Status:** ✅ Market Data APIs tested  
**Next:** Test remaining endpoint groups

---

## 📋 Test Scripts Created

All test scripts are ready to run. They automatically:
- Login if `ACCESS_TOKEN` is not set
- Save results to markdown files with timestamps
- Display output on screen and in files

### Available Test Scripts:

1. ✅ **Market Data APIs** - `./test_market_data_apis.sh` (Already tested)
2. 📦 **Data Management APIs** - `./test_data_management_apis.sh`
3. ⚠️ **Order Management APIs** - `./test_order_management_apis.sh` (Preview only - safe)
4. 🛡️ **Risk Management APIs** - `./test_risk_management_apis.sh`
5. 📡 **Streaming APIs** - `./test_streaming_apis.sh`

---

## 🚀 Quick Start

### Step 1: Set Access Token (if not already set)

```bash
# Login and get token
LOGIN_RESPONSE=$(curl -s -X POST https://piyushdev.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"piyushdev","password":"piyush123"}')

export ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
```

### Step 2: Run Test Scripts

```bash
cd /home/trade-desk

# Test Data Management (4 endpoints)
./test_data_management_apis.sh

# Test Order Preview (1 safe endpoint)
./test_order_management_apis.sh

# Test Risk Management (4 endpoints, all public)
./test_risk_management_apis.sh

# Test Streaming (7 endpoints)
./test_streaming_apis.sh
```

---

## 📦 Step 5: Data Management APIs

**Script:** `./test_data_management_apis.sh`

**Endpoints:**
1. ✅ **Sync Instruments** - `POST /api/v1/data/zerodha/data/instruments/sync`
   - Syncs NSE/BSE instruments to database
   - Requires JWT
   - ⏳ May take time (syncing all instruments)

2. ✅ **Search Instruments** - `GET /api/v1/data/zerodha/data/instruments/search`
   - Search instruments in database
   - Public endpoint (no JWT)

3. ✅ **Fetch Historical** - `POST /api/v1/data/zerodha/data/historical/fetch`
   - Fetches from Zerodha and stores in database
   - Requires JWT

4. ✅ **Query Historical** - `GET /api/v1/data/zerodha/data/historical`
   - Query stored historical data
   - Public endpoint (no JWT)

**Run:**
```bash
./test_data_management_apis.sh
```

**Expected Output:** `data_management_test_YYYYMMDD_HHMMSS.md`

---

## ⚠️ Step 6: Order Management APIs

**Script:** `./test_order_management_apis.sh`

**Endpoints:**
1. ✅ **Preview Order** - `POST /api/v1/orders/preview` (SAFE)
   - Preview order without placing
   - Shows margin requirements and risk checks
   - **This is the ONLY endpoint tested (safe)**

2. ❌ **Place Order** - `POST /api/v1/orders/place` ⚠️ REAL MONEY
   - **NOT TESTED** - Places actual orders

3. ❌ **Modify Order** - `POST /api/v1/orders/modify` ⚠️ REAL MONEY
   - **NOT TESTED** - Modifies existing orders

4. ❌ **Cancel Order** - `POST /api/v1/orders/cancel` ⚠️ REAL MONEY
   - **NOT TESTED** - Cancels existing orders

**Run:**
```bash
./test_order_management_apis.sh
```

**Expected Output:** `order_management_test_YYYYMMDD_HHMMSS.md`

**Note:** The script only tests the preview endpoint. Place/Modify/Cancel are intentionally not tested to avoid real trading.

---

## 🛡️ Step 7: Risk Management APIs

**Script:** `./test_risk_management_apis.sh`

**Endpoints (All Public - No JWT Required):**
1. ✅ **Get Risk Config** - `GET /api/v1/risk/config?user_id=2`
   - Get risk management configuration

2. ✅ **Kill Switch Status** - `GET /api/v1/risk/kill-switch/status`
   - Check if kill switch is active

3. ✅ **Risk Status** - `GET /api/v1/risk/status?user_id=2`
   - Get current risk status for user

4. ✅ **Pre-trade Check** - `POST /api/v1/risk/pre-trade-check`
   - Run risk checks before placing order

**Run:**
```bash
./test_risk_management_apis.sh
```

**Expected Output:** `risk_management_test_YYYYMMDD_HHMMSS.md`

**Note:** All endpoints are public (no JWT needed), but the script will still work if `ACCESS_TOKEN` is set.

---

## 📡 Step 8: Streaming APIs

**Script:** `./test_streaming_apis.sh`

**Endpoints:**
1. ✅ **Session Status** - `GET /api/v1/data/zerodha/session/status`
   - Get Zerodha session information

2. ✅ **Validate Session** - `POST /api/v1/data/zerodha/session/validate`
   - Validate access token by fetching profile

3. ✅ **Stream Status** - `GET /api/v1/data/zerodha/stream/status`
   - Get streaming status and metrics

4. ✅ **Start Stream** - `POST /api/v1/data/zerodha/stream/start`
   - Start real-time data streaming
   - Requires WebSocket connection

5. ✅ **Get Ticks** - `GET /api/v1/data/zerodha/stream/ticks`
   - Get recent tick data from stream

6. ✅ **Update Subscription** - `POST /api/v1/data/zerodha/stream/update`
   - Update instrument subscriptions

7. ✅ **Stop Stream** - `POST /api/v1/data/zerodha/stream/stop`
   - Stop streaming

**Run:**
```bash
./test_streaming_apis.sh
```

**Expected Output:** `streaming_test_YYYYMMDD_HHMMSS.md`

**Note:** Streaming requires active WebSocket connections. Some endpoints may return empty results if no stream is active.

---

## 📊 Testing Summary

### Completed ✅
- Platform Authentication (Login, Profile, Security)
- Zerodha OAuth (Connect, Callback, Claim)
- Zerodha Data APIs (Profile, Margins, Positions, Holdings, Orders, Trades)
- Market Data APIs (LTP, Quote, OHLC, Historical)

### Remaining ⏳
- Data Management APIs (4 endpoints)
- Order Management APIs (1 safe endpoint - preview)
- Risk Management APIs (4 endpoints)
- Streaming APIs (7 endpoints)

**Total Remaining:** ~16 endpoints

---

## 🎯 Recommended Testing Order

1. **Data Management** (Step 5) - Foundation for other tests
2. **Risk Management** (Step 7) - Quick, all public
3. **Order Preview** (Step 6) - Safe order testing
4. **Streaming** (Step 8) - Most complex, requires WebSocket

---

## 📝 Test Results Location

All test results are saved as markdown files in `/home/trade-desk/`:
- `zerodha_api_test_*.md` - Zerodha data APIs
- `market_data_test_*.md` - Market data APIs
- `data_management_test_*.md` - Data management APIs
- `order_management_test_*.md` - Order management APIs
- `risk_management_test_*.md` - Risk management APIs
- `streaming_test_*.md` - Streaming APIs

Review them in your IDE or any markdown viewer!

---

## 🔧 Troubleshooting

### Access Token Expired
```bash
# Re-authenticate Zerodha session
./zerodha_reauth.sh
```

### JWT Token Expired
```bash
# Re-login to platform
LOGIN_RESPONSE=$(curl -s -X POST https://piyushdev.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"piyushdev","password":"piyush123"}')

export ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
```

### Streaming Not Working
- Ensure Zerodha session is valid (test with `/session/validate`)
- Check if WebSocket service is running
- Verify instrument tokens are correct

---

## ✅ Next Steps After Testing

Once all endpoints are tested:
1. Review all test result markdown files
2. Document any issues or errors
3. Fix any bugs found
4. Create final API documentation
5. Set up automated testing (optional)

