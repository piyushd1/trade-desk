# Final Testing Guide - JWT Migration Complete

**Status:** All code changes complete, ready for end-to-end testing  
**Date:** November 14, 2025

> **💡 Tip:** All curl commands in this guide are single-line for easy copy-paste. If you see a backslash `\` at the end of a line, it's for line continuation in scripts - you can either use it as-is in a script, or combine into a single line.

---

## 🎯 What to Test

All 65 API endpoints across these categories:
1. ✅ Platform Authentication (login, profile, refresh)
2. ⏳ Zerodha OAuth (connect, callback, claim session)
3. ⏳ Zerodha Data APIs (profile, margins, positions, holdings, orders, trades)
4. ⏳ Market Data (quote, ltp, ohlc, historical)
5. ⏳ Data Management (instrument sync, historical fetch)
6. ⏳ Order Management (preview, place, modify, cancel)
7. ⏳ Risk Management (config, kill-switch, pre-trade checks)
8. ⏳ Streaming APIs (start, stop, status, ticks)

---

## 📋 Step-by-Step Testing

### STEP 1: Test Platform Authentication ✅ Already Working

```bash
# 1.1 Login
curl -s -X POST https://piyushdev.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"piyushdev","password":"piyush123"}' | python3 -m json.tool

# Save the access_token from response
ACCESS_TOKEN="<paste_token_here>"

# 1.2 Get your profile
curl -s -H "Authorization: Bearer $ACCESS_TOKEN" https://piyushdev.com/api/v1/auth/me | python3 -m json.tool

# 1.3 Test security (should fail without JWT)
curl -s https://piyushdev.com/api/v1/auth/me | python3 -m json.tool
# Expected: {"error": {"code": 401, "message": "Not authenticated"}}
```

✅ **Expected:** All work, security enforced

---

### STEP 2: Re-authenticate with Zerodha

Your Zerodha session expired. Here's how to get a fresh one:

```bash
# 2.1 Get OAuth URL (public, no JWT needed)
curl -s "https://piyushdev.com/api/v1/auth/zerodha/connect?state=RO0252" | python3 -m json.tool

# 2.2 Copy the login_url from response

# 2.3 Open login_url in your browser

# 2.4 Complete Zerodha authentication

# 2.5 After successful auth, you'll see JSON response with session details

# 2.6 Claim the session (link it to your user account)
curl -s -H "Authorization: Bearer $ACCESS_TOKEN" -X POST "https://piyushdev.com/api/v1/auth/zerodha/session/claim?user_identifier=RO0252" | python3 -m json.tool
```

✅ **Expected:** Session claimed and linked to your account

---

### STEP 3: Test Zerodha Data APIs

Now that you have a valid Zerodha session linked to your account:

```bash
USER_ID="RO0252"

# 3.1 Get Zerodha Profile
curl -s -H "Authorization: Bearer $ACCESS_TOKEN" "https://piyushdev.com/api/v1/data/zerodha/profile?user_identifier=$USER_ID" | python3 -m json.tool

# 3.2 Get Margins
curl -s -H "Authorization: Bearer $ACCESS_TOKEN" "https://piyushdev.com/api/v1/data/zerodha/margins?user_identifier=$USER_ID" | python3 -m json.tool

# 3.3 Get Positions
curl -s -H "Authorization: Bearer $ACCESS_TOKEN" "https://piyushdev.com/api/v1/data/zerodha/positions?user_identifier=$USER_ID" | python3 -m json.tool

# 3.4 Get Holdings
curl -s -H "Authorization: Bearer $ACCESS_TOKEN" "https://piyushdev.com/api/v1/data/zerodha/holdings?user_identifier=$USER_ID" | python3 -m json.tool

# 3.5 Get Orders
curl -s -H "Authorization: Bearer $ACCESS_TOKEN" "https://piyushdev.com/api/v1/data/zerodha/orders?user_identifier=$USER_ID" | python3 -m json.tool

# 3.6 Get Trades
curl -s -H "Authorization: Bearer $ACCESS_TOKEN" "https://piyushdev.com/api/v1/data/zerodha/trades?user_identifier=$USER_ID" | python3 -m json.tool
```

✅ **Expected:** All return "status": "success" with data

---

### STEP 4: Test Market Data APIs

```bash
# 4.1 Get LTP (Last Traded Price)
curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  -X POST "https://piyushdev.com/api/v1/data/zerodha/ltp?user_identifier=$USER_ID" \
  -H "Content-Type: application/json" \
  -d '["NSE:INFY", "NSE:RELIANCE", "NSE:TCS"]' | python3 -m json.tool

# 4.2 Get Quote
curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  -X POST "https://piyushdev.com/api/v1/data/zerodha/quote?user_identifier=$USER_ID" \
  -H "Content-Type: application/json" \
  -d '["NSE:INFY"]' | python3 -m json.tool

# 4.3 Get OHLC
curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  -X POST "https://piyushdev.com/api/v1/data/zerodha/ohlc?user_identifier=$USER_ID" \
  -H "Content-Type: application/json" \
  -d '["NSE:RELIANCE"]' | python3 -m json.tool

# 4.4 Get Historical Data (INFY, instrument_token: 408065)
curl -s -H "Authorization: Bearer $ACCESS_TOKEN" "https://piyushdev.com/api/v1/data/zerodha/historical/408065?user_identifier=$USER_ID&from_date=2025-11-01&to_date=2025-11-13&interval=day" | python3 -m json.tool | head -50
```

✅ **Expected:** All return market data

---

### STEP 5: Test Data Management (Sync & Store)

```bash
# 5.1 Sync NSE instruments to database
curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  -X POST "https://piyushdev.com/api/v1/data/zerodha/data/instruments/sync" \
  -H "Content-Type: application/json" \
  -d '{"user_identifier":"RO0252","exchange":"NSE"}' | python3 -m json.tool

# 5.2 Search instruments (public, no JWT needed)
curl -s "https://piyushdev.com/api/v1/data/zerodha/data/instruments/search?q=INFY&exchange=NSE&limit=5" | python3 -m json.tool

# 5.3 Fetch and store historical data
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

# 5.4 Query stored historical data (public, no JWT)
curl -s "https://piyushdev.com/api/v1/data/zerodha/data/historical?instrument_token=408065&interval=day&limit=10" | python3 -m json.tool
```

✅ **Expected:** Instruments synced, historical data stored and queryable

---

### STEP 6: Test Order Management (⚠️ CAREFUL - Real Money!)

```bash
# 6.1 Preview Order (safe, doesn't place)
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

# STOP HERE - DO NOT RUN place/modify/cancel UNLESS YOU WANT TO TRADE!
```

✅ **Expected:** Returns margin requirements and risk checks
⚠️ **DO NOT** proceed to `/orders/place` unless you want to place real orders!

---

### STEP 7: Test Risk Management

```bash
# 7.1 Get risk config
curl -s "https://piyushdev.com/api/v1/risk/config?user_id=2" | python3 -m json.tool

# 7.2 Check kill switch
curl -s https://piyushdev.com/api/v1/risk/kill-switch/status | python3 -m json.tool

# 7.3 Get risk status
curl -s "https://piyushdev.com/api/v1/risk/status?user_id=2" | python3 -m json.tool

# 7.4 Run pre-trade check
curl -s -X POST https://piyushdev.com/api/v1/risk/pre-trade-check \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 2,
    "symbol": "INFY",
    "quantity": 1,
    "price": 1500.0
  }' | python3 -m json.tool
```

✅ **Expected:** Risk management data and validations

---

### STEP 8: Test Security - Ownership Validation

```bash
# Login as admin
ADMIN_LOGIN=$(curl -s -X POST https://piyushdev.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}')

ADMIN_TOKEN=$(echo "$ADMIN_LOGIN" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

# Try to access piyushdev's Zerodha session (should fail)
curl -s -H "Authorization: Bearer $ADMIN_TOKEN" "https://piyushdev.com/api/v1/data/zerodha/profile?user_identifier=RO0252" | python3 -m json.tool
```

✅ **Expected:** 403 Forbidden - "You do not have permission to access session 'RO0252'"

---

## 🚀 Quick Test Script

Run the automated test:
```bash
cd /home/trade-desk
./QUICK_TEST.sh
```

This tests:
- Login
- JWT validation
- Security (401 without JWT)
- Ownership (403 for other user's session)

---

## 📝 Complete Re-authentication Process

**Here's the exact sequence:**

```bash
# Step 1: Get OAuth URL (no JWT needed)
echo "Step 1: Getting OAuth URL..."
OAUTH=$(curl -s "https://piyushdev.com/api/v1/auth/zerodha/connect?state=RO0252")
echo "$OAUTH" | python3 -m json.tool
LOGIN_URL=$(echo "$OAUTH" | python3 -c "import sys, json; print(json.load(sys.stdin)['login_url'])")

echo ""
echo "Step 2: Open this URL in browser:"
echo "$LOGIN_URL"
echo ""
echo "Step 3: Complete Zerodha authentication"
echo ""
echo "Step 4: After successful auth, login to TradeDesk and claim session:"
echo ""
echo "# Login"
echo "LOGIN=\$(curl -s -X POST https://piyushdev.com/api/v1/auth/login \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -d '{\"username\":\"piyushdev\",\"password\":\"piyush123\"}')"
echo ""
echo "ACCESS_TOKEN=\$(echo \"\$LOGIN\" | python3 -c \"import sys, json; print(json.load(sys.stdin)['access_token'])\")"
echo ""
echo "# Claim session"
echo "curl -s -H \"Authorization: Bearer \$ACCESS_TOKEN\" \\"
echo "  -X POST \"https://piyushdev.com/api/v1/auth/zerodha/session/claim?user_identifier=RO0252\" | python3 -m json.tool"
echo ""
echo "# Now test Zerodha APIs"
echo "curl -s -H \"Authorization: Bearer \$ACCESS_TOKEN\" \\"
echo "  \"https://piyushdev.com/api/v1/data/zerodha/profile?user_identifier=RO0252\" | python3 -m json.tool"
```

---

## ✅ Success Checklist

After completing all steps above:

- [ ] Platform login working (got JWT tokens)
- [ ] /auth/me returns profile
- [ ] Security working (401 without JWT)
- [ ] Ownership working (403 for other user's session)
- [ ] Zerodha OAuth completed successfully
- [ ] Session claimed and linked to user
- [ ] Zerodha profile API working
- [ ] All Zerodha data APIs returning data
- [ ] Historical data fetch/store working
- [ ] Order preview working (don't place!)
- [ ] Risk management checks working

---

## 🔐 Security Verification

**Test these to confirm security:**

1. **Without JWT - Should FAIL:**
   ```bash
   curl https://piyushdev.com/api/v1/data/zerodha/profile?user_identifier=RO0252
   # Expected: 401 Unauthorized
   ```

2. **Wrong User - Should FAIL:**
   ```bash
   # Login as admin
   ADMIN_TOKEN=$(curl -s -X POST https://piyushdev.com/api/v1/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username":"admin","password":"admin123"}' | \
     python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
   
   # Try to access piyushdev's session
   curl -H "Authorization: Bearer $ADMIN_TOKEN" \
     "https://piyushdev.com/api/v1/data/zerodha/profile?user_identifier=RO0252"
   # Expected: 403 Forbidden
   ```

3. **Correct User - Should WORK:**
   ```bash
   # Login as piyushdev
   ACCESS_TOKEN=$(curl -s -X POST https://piyushdev.com/api/v1/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username":"piyushdev","password":"piyush123"}' | \
     python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
   
   # Access your own session
   curl -H "Authorization: Bearer $ACCESS_TOKEN" \
     "https://piyushdev.com/api/v1/data/zerodha/profile?user_identifier=RO0252"
   # Expected: 200 OK with profile data
   ```

---

## 🎯 Current Credentials

**Platform Login:**
- Username: `piyushdev`
- Password: `piyush123`
- User ID: 2

**Zerodha Session:**
- Identifier: `RO0252`
- Status: Expired (needs re-auth)
- Owner: piyushdev (user_id=2)

**Admin Account:**
- Username: `admin`
- Password: `admin123`
- User ID: 1
- Cannot access RO0252 (ownership validation)

---

## 📊 What Changed

### Before JWT Migration
- Nginx Basic Auth (single password)
- No per-user access control
- Anyone with password could access any Zerodha session

### After JWT Migration ✅
- JWT Bearer tokens (15min expiry)
- Per-user authentication
- Users can only access their own Zerodha sessions
- 403 Forbidden if trying to access another user's session
- All actions audited per user_id

---

## 🚀 Ready to Test!

1. Run `./QUICK_TEST.sh` to verify platform auth
2. Follow Step 2 above to re-authenticate with Zerodha
3. Follow Steps 3-8 to test all APIs systematically
4. Refer to `TESTING_STEPS.md` for detailed expected results

**All code is complete. Time to test! 🎉**

