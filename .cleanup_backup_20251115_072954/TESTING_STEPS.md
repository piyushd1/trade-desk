# JWT Migration - Testing Steps

**Prerequisites:**
- All 25 endpoints updated with JWT authentication
- Backend restarted
- Nginx Basic Auth removed

---

## Test Credentials

**Username:** `piyushdev`  
**Password:** `piyush123`  
**Zerodha Session:** `RO0252` (linked to piyushdev, user_id=2)

---

## Step 1: Test Login (Get JWT Token)

```bash
# Login and get JWT tokens
LOGIN_RESPONSE=$(curl -s -X POST https://piyushdev.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"piyushdev","password":"piyush123"}')

echo "$LOGIN_RESPONSE" | python3 -m json.tool

# Extract access token
ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

echo "Access Token: ${ACCESS_TOKEN:0:50}..."
```

**Expected Result:**
```json
{
    "status": "success",
    "access_token": "eyJhbGc...",
    "refresh_token": "eyJhbGc...",
    "token_type": "bearer",
    "user": {
        "id": 2,
        "username": "piyushdev",
        "email": "piyush.dev@gmail.com",
        "full_name": "Piyush Deveshwar",
        "role": "trader"
    }
}
```

✅ **Pass:** Got access_token  
❌ **Fail:** 401 error or no token

---

## Step 2: Test `/auth/me` Endpoint

```bash
# Get current user profile with JWT
curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  https://piyushdev.com/api/v1/auth/me | python3 -m json.tool
```

**Expected Result:**
```json
{
    "status": "success",
    "user": {
        "id": 2,
        "username": "piyushdev",
        ...
    }
}
```

✅ **Pass:** Returns user profile  
❌ **Fail:** 401 "Not authenticated"

---

## Step 3: Test Without JWT (Should Fail)

```bash
# Try to access protected endpoint without JWT
curl -s https://piyushdev.com/api/v1/data/zerodha/profile?user_identifier=RO0252 | python3 -m json.tool
```

**Expected Result:**
```json
{
    "error": {
        "code": 401,
        "message": "Not authenticated"
    }
}
```

✅ **Pass:** 401 error  
❌ **Fail:** Returns data (security breach!)

---

## Step 4: Test Zerodha Profile (With JWT)

```bash
# Get Zerodha profile with JWT
curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  "https://piyushdev.com/api/v1/data/zerodha/profile?user_identifier=RO0252" | python3 -m json.tool
```

**Expected Result:**
```json
{
    "status": "success",
    "data": {
        "user_id": "YOUR_ZERODHA_ID",
        "user_name": "Your Name",
        "email": "your@email.com",
        ...
    }
}
```

✅ **Pass:** Returns Zerodha profile  
❌ **Fail:** 401, 403, or 404 error

---

## Step 5: Test Ownership Validation (Try Another User's Session)

**Setup:** Login as admin and try to access piyushdev's Zerodha session

```bash
# Login as admin
ADMIN_LOGIN=$(curl -s -X POST https://piyushdev.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}')

ADMIN_TOKEN=$(echo "$ADMIN_LOGIN" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

# Try to access piyushdev's session (RO0252) as admin
curl -s -H "Authorization: Bearer $ADMIN_TOKEN" \
  "https://piyushdev.com/api/v1/data/zerodha/profile?user_identifier=RO0252" | python3 -m json.tool
```

**Expected Result:**
```json
{
    "error": {
        "code": 403,
        "message": "You do not have permission to access session 'RO0252'. This session belongs to another user."
    }
}
```

✅ **Pass:** 403 Forbidden (correct - admin can't access piyushdev's session)  
❌ **Fail:** Returns data (security breach!)

---

## Step 6: Test Multiple Zerodha Endpoints

```bash
# Set user identifier
USER_ID="RO0252"

# Test margins
echo "Testing /margins..."
curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  "https://piyushdev.com/api/v1/data/zerodha/margins?user_identifier=$USER_ID" | python3 -m json.tool

# Test positions
echo "Testing /positions..."
curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  "https://piyushdev.com/api/v1/data/zerodha/positions?user_identifier=$USER_ID" | python3 -m json.tool

# Test holdings
echo "Testing /holdings..."
curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  "https://piyushdev.com/api/v1/data/zerodha/holdings?user_identifier=$USER_ID" | python3 -m json.tool

# Test orders
echo "Testing /orders..."
curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  "https://piyushdev.com/api/v1/data/zerodha/orders?user_identifier=$USER_ID" | python3 -m json.tool

# Test LTP
echo "Testing /ltp..."
curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  -X POST "https://piyushdev.com/api/v1/data/zerodha/ltp?user_identifier=$USER_ID" \
  -H "Content-Type: application/json" \
  -d '["NSE:INFY", "NSE:RELIANCE"]' | python3 -m json.tool
```

**Expected:** All return `"status": "success"` with data  
✅ **Pass:** All work  
❌ **Fail:** Any return 401/403/404

---

## Step 7: Test Historical Data

```bash
# Get historical data for INFY
curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  "https://piyushdev.com/api/v1/data/zerodha/historical/408065?user_identifier=$USER_ID&from_date=2025-11-01&to_date=2025-11-13&interval=day" | python3 -m json.tool | head -50
```

**Expected:** Returns array of candles  
✅ **Pass:** Got candle data  
❌ **Fail:** 401/403/404 error

---

## Step 8: Test Token Refresh

```bash
# Extract refresh token from login response
REFRESH_TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['refresh_token'])")

# Refresh access token
REFRESH_RESPONSE=$(curl -s -X POST https://piyushdev.com/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d "{\"refresh_token\":\"$REFRESH_TOKEN\"}")

echo "$REFRESH_RESPONSE" | python3 -m json.tool

# Extract new access token
NEW_ACCESS_TOKEN=$(echo "$REFRESH_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

# Test with new token
curl -s -H "Authorization: Bearer $NEW_ACCESS_TOKEN" \
  https://piyushdev.com/api/v1/auth/me | python3 -m json.tool
```

**Expected:** New token works  
✅ **Pass:** Token refreshed and works  
❌ **Fail:** 401 error

---

## Step 9: Test Public Endpoints (No JWT Needed)

```bash
# These should work WITHOUT JWT

# Search instruments (public, queries local DB)
curl -s "https://piyushdev.com/api/v1/data/zerodha/data/instruments/search?q=INFY&limit=5" | python3 -m json.tool

# Get instrument detail (public)
curl -s "https://piyushdev.com/api/v1/data/zerodha/data/instruments/408065" | python3 -m json.tool

# Historical stats (public)
curl -s "https://piyushdev.com/api/v1/data/zerodha/data/historical/stats" | python3 -m json.tool

# Capabilities (public)
curl -s "https://piyushdev.com/api/v1/data/zerodha/capabilities" | python3 -m json.tool
```

**Expected:** All work without JWT  
✅ **Pass:** All return data  
❌ **Fail:** 401 error (shouldn't require JWT)

---

## Step 10: Test Order Preview (Careful - Risk Check)

```bash
# Preview an order (doesn't place it)
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

**Expected:** Returns margin requirements and risk checks  
✅ **Pass:** Got margin calculation  
❌ **Fail:** 401/403/500 error

---

## Summary Checklist

- [ ] Step 1: Login works, got JWT token
- [ ] Step 2: `/auth/me` works with JWT
- [ ] Step 3: Protected endpoints reject requests without JWT
- [ ] Step 4: Zerodha profile works with JWT
- [ ] Step 5: Ownership validation works (403 for other user's session)
- [ ] Step 6: All Zerodha data endpoints work
- [ ] Step 7: Historical data works
- [ ] Step 8: Token refresh works
- [ ] Step 9: Public endpoints work without JWT
- [ ] Step 10: Order preview works

---

## If Tests Fail

### 401 "Not authenticated" on protected endpoints
- Check JWT token is valid: `echo $ACCESS_TOKEN`
- Verify `Authorization: Bearer` header is included
- Check backend logs: `tail -f /tmp/backend.log`

### 403 "You do not have permission"
- Verify you're using the correct `user_identifier` for your account
- Check database: Session `RO0252` should belong to user_id=2 (piyushdev)
- Verify you're logged in as the right user

### 404 "No active Zerodha session found"
- Verify Zerodha OAuth was completed
- Check session in database
- Session might be expired (re-do OAuth)

### 500 Internal Server Error
- Check backend logs for Python errors
- Verify all imports are correct
- Check database connection

---

**All tests passing? JWT migration is complete! 🎉**

