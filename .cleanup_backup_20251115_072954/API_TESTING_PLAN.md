# API Testing & Hardening Plan - TradeDesk Platform

**Date:** November 14, 2025  
**Objective:** Test and make all APIs robust and production-ready

---

## 🎯 Current API Inventory (65 Total Endpoints)

### 1. Authentication & User Management (13 endpoints)
**Module:** `auth.py`

#### Internal Platform Authentication
| Endpoint | Method | Status | Auth Required | Notes |
|----------|--------|--------|---------------|-------|
| `/auth/register` | POST | ✅ Implemented | No | User registration |
| `/auth/login` | POST | ✅ Implemented | No | JWT login |
| `/auth/logout` | POST | ⚠️ TODO | Yes | Not implemented yet |
| `/auth/refresh` | POST | ⚠️ TODO | Yes | JWT refresh not implemented |
| `/auth/me` | GET | ⚠️ TODO | Yes | Get current user not implemented |

#### Zerodha OAuth & Session Management
| Endpoint | Method | Status | Auth Required | Notes |
|----------|--------|--------|---------------|-------|
| `/auth/zerodha/config` | POST | ✅ Implemented | No | Update Zerodha credentials |
| `/auth/zerodha/connect` | GET | ✅ Implemented | No | Initiate OAuth |
| `/auth/zerodha/callback` | GET | ✅ Implemented | No | OAuth callback |
| `/auth/zerodha/session` | GET | ✅ Implemented | No | Get session details |
| `/auth/zerodha/refresh` | POST | ✅ Implemented | No | Manual token refresh |
| `/auth/zerodha/refresh/status` | GET | ✅ Implemented | No | Refresh service status |

#### Broker Status
| Endpoint | Method | Status | Auth Required | Notes |
|----------|--------|--------|---------------|-------|
| `/auth/brokers/status` | GET | ✅ Implemented | No | All broker status |
| `/auth/brokers/groww/connect` | POST | ⚠️ Stub | No | Groww placeholder |

---

### 2. Zerodha Data APIs (12 endpoints)
**Module:** `zerodha_simple.py`

| Endpoint | Method | Status | Auth Required | Notes |
|----------|--------|--------|---------------|-------|
| `/data/zerodha/profile` | GET | ✅ Implemented | user_identifier | User profile |
| `/data/zerodha/margins` | GET | ✅ Implemented | user_identifier | Account margins |
| `/data/zerodha/holdings` | GET | ✅ Implemented | user_identifier | Long-term holdings |
| `/data/zerodha/positions` | GET | ✅ Implemented | user_identifier | Current positions |
| `/data/zerodha/orders` | GET | ✅ Implemented | user_identifier | Order book |
| `/data/zerodha/trades` | GET | ✅ Implemented | user_identifier | Executed trades |
| `/data/zerodha/quote` | POST | ✅ Implemented | user_identifier | Market quotes |
| `/data/zerodha/ltp` | POST | ✅ Implemented | user_identifier | Last traded price |
| `/data/zerodha/ohlc` | POST | ✅ Implemented | user_identifier | OHLC data |
| `/data/zerodha/instruments` | GET | ✅ Implemented | user_identifier | All instruments |
| `/data/zerodha/historical/{token}` | GET | ✅ Implemented | user_identifier | Historical candles |
| `/data/zerodha/capabilities` | GET | ✅ Implemented | No | API capabilities |

---

### 3. Zerodha Data Management (7 endpoints)
**Module:** `zerodha_data_management.py`

| Endpoint | Method | Status | Auth Required | Notes |
|----------|--------|--------|---------------|-------|
| `/data/instruments/sync` | POST | ✅ Implemented | user_identifier | Sync instruments to DB |
| `/data/instruments/search` | GET | ✅ Implemented | No | Search instruments |
| `/data/instruments/{token}` | GET | ✅ Implemented | No | Get instrument detail |
| `/data/historical/fetch` | POST | ✅ Implemented | user_identifier | Fetch & store historical |
| `/data/historical` | GET | ✅ Implemented | No | Query stored historical |
| `/data/historical/stats` | GET | ✅ Implemented | No | Historical statistics |
| `/data/historical/cleanup` | DELETE | ✅ Implemented | No | Cleanup old data |

---

### 4. Zerodha Streaming (7 endpoints)
**Module:** `zerodha_streaming.py`

| Endpoint | Method | Status | Auth Required | Notes |
|----------|--------|--------|---------------|-------|
| `/data/stream/start` | POST | ✅ Implemented | user_identifier | Start WebSocket stream |
| `/data/stream/stop` | POST | ✅ Implemented | user_identifier | Stop stream |
| `/data/stream/update` | POST | ✅ Implemented | user_identifier | Update subscription |
| `/data/stream/status` | GET | ✅ Implemented | user_identifier | Stream status |
| `/data/stream/ticks` | GET | ✅ Implemented | user_identifier | Recent ticks |
| `/data/session/status` | GET | ✅ Implemented | user_identifier | Session status |
| `/data/session/validate` | POST | ✅ Implemented | user_identifier | Validate token |

---

### 5. Order Management (4 endpoints)
**Module:** `orders.py`

| Endpoint | Method | Status | Auth Required | Notes |
|----------|--------|--------|---------------|-------|
| `/orders/preview` | POST | ✅ Implemented | user_id + user_identifier | Preview with risk checks |
| `/orders/place` | POST | ✅ Implemented | user_id + user_identifier | Place order |
| `/orders/modify` | POST | ✅ Implemented | user_id + user_identifier | Modify order |
| `/orders/cancel` | POST | ✅ Implemented | user_id + user_identifier | Cancel order |

---

### 6. Risk Management (11 endpoints)
**Module:** `risk.py`

| Endpoint | Method | Status | Auth Required | Notes |
|----------|--------|--------|---------------|-------|
| `/risk/config` | GET | ✅ Implemented | user_id | Get risk config |
| `/risk/config` | PUT | ✅ Implemented | user_id | Update risk limits |
| `/risk/kill-switch` | POST | ✅ Implemented | No | Toggle kill switch |
| `/risk/kill-switch/status` | GET | ✅ Implemented | No | Check kill switch |
| `/risk/pre-trade-check` | POST | ✅ Implemented | user_id | Pre-trade validation |
| `/risk/metrics/daily` | GET | ✅ Implemented | user_id | Daily metrics |
| `/risk/metrics/history` | GET | ✅ Implemented | user_id | Historical metrics |
| `/risk/breaches` | GET | ✅ Implemented | user_id | Query breaches |
| `/risk/breaches/{id}` | GET | ✅ Implemented | No | Get specific breach |
| `/risk/status` | GET | ✅ Implemented | user_id | Comprehensive status |
| `/risk/limits/check` | GET | ✅ Implemented | user_id | Check limits |

---

### 7. Audit & Compliance (4 endpoints)
**Module:** `audit.py`

| Endpoint | Method | Status | Auth Required | Notes |
|----------|--------|--------|---------------|-------|
| `/audit/logs` | GET | ✅ Implemented | No | Query audit logs |
| `/audit/logs/{id}` | GET | ✅ Implemented | No | Get specific log |
| `/system/events` | GET | ✅ Implemented | No | Query system events |
| `/system/events/{id}` | GET | ✅ Implemented | No | Get specific event |

---

### 8. Health & Monitoring (3 endpoints)
**Module:** `health.py`

| Endpoint | Method | Status | Auth Required | Notes |
|----------|--------|--------|---------------|-------|
| `/health/ping` | GET | ✅ Implemented | No | Simple ping |
| `/health/status` | GET | ✅ Implemented | No | System status |
| `/health/compliance` | GET | ✅ Implemented | No | Compliance status |

---

### 9. Broker Testing (4 endpoints)
**Module:** `broker.py`

| Endpoint | Method | Status | Auth Required | Notes |
|----------|--------|--------|---------------|-------|
| `/broker/test/zerodha/profile` | GET | ✅ Implemented | access_token | Direct token test |
| `/broker/test/zerodha/margins` | GET | ✅ Implemented | access_token | Direct token test |
| `/broker/test/zerodha/positions` | GET | ✅ Implemented | access_token | Direct token test |
| `/broker/test/zerodha/holdings` | GET | ✅ Implemented | access_token | Direct token test |

---

## 🔴 Critical Issues to Fix

### Issue 1: JWT Authentication Not Working
**Problem:** 401 "Not authenticated" errors on protected endpoints

**Affected Endpoints:**
- `/auth/me`
- `/auth/refresh`
- `/auth/logout`
- Any endpoint using `oauth2_scheme = OAuth2PasswordBearer`

**Root Cause:**
1. JWT token validation logic not implemented
2. `oauth2_scheme` dependency returns token but doesn't validate it
3. No middleware to verify JWT signatures

**Fix Required:**
- Implement JWT validation dependency
- Create `get_current_user` dependency
- Add proper error handling for expired/invalid tokens

---

### Issue 2: Mixed Authentication Patterns
**Problem:** Three different auth patterns used inconsistently

**Pattern 1:** JWT Bearer Token (not working)
```python
token: str = Depends(oauth2_scheme)
```

**Pattern 2:** Query Parameter `user_identifier` (working)
```python
user_identifier: str = Query(...)
```

**Pattern 3:** Request Body `user_id` + `user_identifier` (working)
```python
class OrderRequest(BaseModel):
    user_id: int
    user_identifier: str
```

**Fix Required:**
- Standardize on JWT for internal platform auth
- Keep `user_identifier` for Zerodha session lookup
- Document which endpoints need which auth

---

### Issue 3: Zerodha Session vs Platform Session Confusion
**Problem:** Two separate auth systems not clearly separated

**Platform Users:**
- Username/password login
- JWT tokens for session
- Internal user_id (1, 2, 3...)

**Zerodha Sessions:**
- OAuth flow
- user_identifier (e.g., "RO0252")
- Stored in broker_sessions table

**Fix Required:**
- Clear documentation of auth flows
- Endpoints should require platform JWT first, then look up Zerodha session
- Add proper error messages

---

## 📋 Testing Plan

### Phase 1: Fix Internal Authentication (Priority P0)

**Tasks:**
1. ✅ Create JWT validation dependency in `auth.py`
2. ✅ Implement `get_current_user` function
3. ✅ Fix `/auth/me` endpoint
4. ✅ Implement `/auth/refresh` endpoint
5. ✅ Implement `/auth/logout` endpoint
6. ✅ Update all protected endpoints to use JWT auth
7. ✅ Test login → get profile → refresh → logout flow

**Success Criteria:**
- User can login and receive JWT
- JWT can be used to access protected endpoints
- Token refresh works without re-login
- Logout invalidates token

---

### Phase 2: Test Zerodha OAuth & Data APIs (Priority P0)

**Tasks:**
1. ✅ Test complete OAuth flow (connect → callback → session storage)
2. ✅ Verify token encryption/decryption
3. ✅ Test all 12 data endpoints with valid session
4. ✅ Test auto-refresh mechanism
5. ✅ Test error handling (expired token, invalid session)
6. ✅ Verify historical data storage
7. ✅ Test instrument sync

**Success Criteria:**
- OAuth flow completes successfully
- All data APIs return valid responses
- Tokens auto-refresh before expiry
- Database stores instruments and historical data

---

### Phase 3: Test Data Management & Storage (Priority P1)

**Tasks:**
1. ✅ Sync instruments for NSE, BSE, NFO
2. ✅ Verify multi-exchange support (removed unique constraint)
3. ✅ Fetch and store historical data for multiple symbols
4. ✅ Test historical query API
5. ✅ Verify OI (open interest) storage
6. ✅ Test cleanup endpoints

**Success Criteria:**
- All instruments synced without errors
- Historical data stored correctly with OI
- Query API returns accurate data
- Cleanup works without breaking references

---

### Phase 4: Test Streaming APIs (Priority P1)

**Tasks:**
1. ✅ Start stream for multiple instruments
2. ✅ Verify tick data reception
3. ✅ Test stream status endpoint
4. ✅ Test update subscription
5. ✅ Test stop stream
6. ✅ Verify session validation

**Success Criteria:**
- Stream starts without errors
- Ticks received in real-time
- Subscription updates work
- Clean shutdown on stop

---

### Phase 5: Test Order Management (Priority P0 - Money at Risk!)

**Tasks:**
1. ✅ Test order preview with margin calculation
2. ✅ Verify all risk checks fire correctly
3. ✅ Test kill switch blocks orders
4. ✅ Test position/order limits
5. ✅ Test daily loss limit
6. ✅ Test OPS (orders per second) limit
7. ✅ Place REAL orders in paper trading mode first
8. ✅ Test modify order
9. ✅ Test cancel order

**Success Criteria:**
- Preview shows accurate margins
- Risk checks prevent invalid orders
- Kill switch works
- Orders placed successfully
- Modify/cancel work

---

### Phase 6: Test Risk Management (Priority P0)

**Tasks:**
1. ✅ Get risk config for user
2. ✅ Update risk limits
3. ✅ Toggle kill switch on/off
4. ✅ Run pre-trade checks
5. ✅ Verify daily metrics tracking
6. ✅ Test breach logging
7. ✅ Query breach history
8. ✅ Check risk status

**Success Criteria:**
- All risk APIs return valid data
- Limits enforced correctly
- Breaches logged properly
- Kill switch effective

---

### Phase 7: Test Audit & Compliance (Priority P1)

**Tasks:**
1. ✅ Query audit logs
2. ✅ Filter by action, user, date
3. ✅ Query system events
4. ✅ Verify all actions logged
5. ✅ Test pagination

**Success Criteria:**
- All user actions logged
- Queries work with filters
- Pagination functional
- 7-year retention ready

---

## 🛠️ Implementation Checklist

### Step 1: Fix JWT Authentication (MUST DO FIRST)

**Files to Modify:**
1. `backend/app/api/v1/auth.py`
   - ✅ Implement `get_current_user` dependency
   - ✅ Fix `/auth/me` endpoint
   - ✅ Implement `/auth/refresh` endpoint
   - ✅ Implement `/auth/logout` endpoint

2. `backend/app/services/auth_service.py`
   - ✅ Add JWT validation method
   - ✅ Add token revocation (blacklist or DB flag)

3. `backend/app/models/user.py`
   - ✅ Add `last_login` field
   - ✅ Add `is_active` field

**Test Script:** `test_internal_auth.sh`

---

### Step 2: Create Comprehensive Test Scripts

**Scripts to Create:**
1. ✅ `test_internal_auth.sh` - Test platform login/logout
2. ✅ `test_zerodha_oauth.sh` - Test OAuth flow
3. ✅ `test_zerodha_data.sh` - Test all data endpoints
4. ✅ `test_data_management.sh` - Test sync/storage
5. ✅ `test_streaming.sh` - Test WebSocket streams
6. ✅ `test_orders.sh` - Test order APIs (CAREFUL!)
7. ✅ `test_risk.sh` - Test risk management
8. ✅ `test_audit.sh` - Test audit logs
9. ✅ `test_all_apis.sh` - Run all tests

---

### Step 3: Add HTTP Basic Auth Bypass for Testing

**Problem:** Current Nginx basic auth blocks API testing

**Solutions:**
1. Create separate test endpoints without basic auth
2. Add API key authentication
3. Use curl with `-u username:password`

**For Now:** Use curl with basic auth:
```bash
curl -u piyushdeveshwar:Lead@102938 https://piyushdev.com/api/v1/...
```

---

### Step 4: Document Authentication Flows

**Create:** `AUTHENTICATION_GUIDE.md`

**Content:**
1. Platform authentication (JWT)
2. Zerodha OAuth flow
3. Session management
4. Token refresh strategy
5. Error handling
6. Security best practices

---

## 🚀 Quick Start Testing

### 1. Setup Test Environment
```bash
cd /home/trade-desk

# Set credentials
export BASIC_AUTH_USER="piyushdeveshwar"
export BASIC_AUTH_PASS="Lead@102938"
export API_BASE="https://piyushdev.com/api/v1"

# Helper function
api_call() {
    curl -u "$BASIC_AUTH_USER:$BASIC_AUTH_PASS" "$@"
}
```

### 2. Test Platform Login
```bash
# Login
RESPONSE=$(api_call -X POST "$API_BASE/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}')

# Extract token
TOKEN=$(echo $RESPONSE | jq -r '.access_token')

# Test protected endpoint
api_call -H "Authorization: Bearer $TOKEN" "$API_BASE/auth/me"
```

### 3. Test Zerodha Session
```bash
USER_ID="RO0252"

# Get session
api_call "$API_BASE/auth/zerodha/session?user_identifier=$USER_ID" | jq

# Get profile
api_call "$API_BASE/data/zerodha/profile?user_identifier=$USER_ID" | jq
```

---

## 📊 Success Metrics

| Category | Total Endpoints | Implemented | Working | Tests | Target |
|----------|----------------|-------------|---------|-------|--------|
| Auth | 13 | 10 | 7 | 0 | 100% |
| Zerodha Data | 12 | 12 | 12 | 0 | 100% |
| Data Management | 7 | 7 | 7 | 0 | 100% |
| Streaming | 7 | 7 | ? | 0 | 100% |
| Orders | 4 | 4 | ? | 0 | 100% |
| Risk | 11 | 11 | 11 | 23 | 100% |
| Audit | 4 | 4 | 4 | 14 | 100% |
| Health | 3 | 3 | 3 | 0 | 100% |
| Broker Test | 4 | 4 | 4 | 0 | 100% |
| **TOTAL** | **65** | **62** | **~55** | **37** | **100%** |

**Current Status:** 95% implemented, ~85% working, 57% tested

**Target:** 100% implemented, 100% working, 100% tested

---

## 🎯 Priority Order

1. **P0 - Critical (Do First)**
   - Fix JWT authentication
   - Test order APIs (money at risk!)
   - Verify risk management works

2. **P1 - High (Do Next)**
   - Test all Zerodha data APIs
   - Test data management/storage
   - Test streaming APIs
   - Create test scripts

3. **P2 - Medium (Do After)**
   - Audit/compliance testing
   - Performance testing
   - Load testing
   - Documentation

4. **P3 - Nice to Have**
   - Groww integration
   - Strategy engine
   - Paper trading
   - Advanced analytics

---

**Next Steps:**
1. Review this plan
2. Confirm priorities
3. Start with JWT authentication fix
4. Then test Zerodha APIs
5. Then orders/risk management

