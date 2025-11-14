# Phase 2 Progress - JWT Migration

**Date:** November 14, 2025  
**Status:** In Progress

---

## ✅ Completed

### 1. Nginx Basic Auth Removed
- Successfully removed HTTP Basic Auth from all endpoints
- Verified: `curl https://piyushdev.com/api/v1/health/ping` works without credentials
- ✅ Domain is now public but APIs will require JWT

### 2. User Ownership Validation Helper Created
- Added `validate_user_owns_session()` to `zerodha_common.py`
- Function validates:
  1. Session exists
  2. Current user owns the session (user_id match)
  3. Raises 403 Forbidden if user doesn't own session

### 3. Started Updating Zerodha Endpoints
- Updated imports in `zerodha_simple.py`
- Updated 2 endpoints so far:
  - `/zerodha/profile` - ✅ Requires JWT + validates ownership
  - `/zerodha/margins` - ✅ Requires JWT + validates ownership

---

## ⏳ Remaining Work

### Endpoints Still Need JWT (23 endpoints)

**File: `zerodha_simple.py` (9 more endpoints)**
- `/zerodha/holdings`
- `/zerodha/positions`
- `/zerodha/orders`
- `/zerodha/trades`
- `/zerodha/quote` (POST)
- `/zerodha/ltp` (POST)
- `/zerodha/ohlc` (POST)
- `/zerodha/instruments`
- `/zerodha/historical/{token}`
- `/zerodha/capabilities` - ⚠️ Should this be public?

**File: `zerodha_data_management.py` (7 endpoints)**
- `/instruments/sync` - Requires JWT
- `/instruments/search` - PUBLIC (no JWT needed, queries local DB)
- `/instruments/{token}` - PUBLIC (no JWT needed, queries local DB)
- `/historical/fetch` - Requires JWT
- `/historical` - PUBLIC (no JWT needed, queries local DB)
- `/historical/stats` - PUBLIC (no JWT needed, queries local DB)
- `/historical/cleanup` - Requires JWT

**File: `zerodha_streaming.py` (6 endpoints)**
- `/stream/start` - Requires JWT
- `/stream/stop` - Requires JWT
- `/stream/update` - Requires JWT
- `/stream/status` - Requires JWT
- `/stream/ticks` - Requires JWT
- `/session/status` - Requires JWT
- `/session/validate` - Requires JWT

**File: `orders.py` (4 endpoints)**
- `/orders/preview` - Requires JWT
- `/orders/place` - Requires JWT
- `/orders/modify` - Requires JWT
- `/orders/cancel` - Requires JWT

---

## 📋 Pattern for Each Update

**BEFORE:**
```python
@router.get("/zerodha/profile")
async def get_profile(
    user_identifier: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    kite = await _get_kite_client_for_identifier(user_identifier, db)
    # ... use kite
```

**AFTER:**
```python
@router.get("/zerodha/profile")
async def get_profile(
    current_user: User = Depends(get_current_user_dependency),  # ✅ Add JWT
    user_identifier: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    # ✅ Validate ownership
    session = await validate_user_owns_session(current_user, user_identifier, db)
    access_token = decrypt_access_token(session)
    kite = get_kite_client(access_token)
    # ... use kite
```

---

## 🎯 Next Steps

1. **Continue updating endpoints:**
   - Complete remaining 9 in `zerodha_simple.py`
   - Update 4 in `zerodha_data_management.py` (skip public ones)
   - Update 7 in `zerodha_streaming.py`
   - Update 4 in `orders.py`

2. **Update OAuth endpoints in `auth.py`:**
   - `/zerodha/connect` - Require JWT, embed token in URL
   - `/zerodha/callback` - Accept JWT from query param
   - `_store_broker_session` - Link session to current_user.id

3. **Restart backend and test:**
   - Test login flow
   - Test Zerodha OAuth with JWT
   - Test data APIs with JWT
   - Test ownership validation (try accessing another user's session)

---

## 🔐 Security Status

**Current State:**
- ✅ Database schema ready (user_id in broker_sessions)
- ✅ Nginx Basic Auth removed
- ✅ Ownership validation helper created
- ⏳ Endpoints being updated (2/25 done)

**When Complete:**
- ✅ All Zerodha APIs require JWT
- ✅ Users can only access their own sessions
- ✅ Per-user access control enforced
- ✅ Audit trail per user

---

## Admin Credentials (After Phase 1)

```
Username: admin
Password: admin123
```

Use these to login and get JWT tokens for testing.

---

**Status:** 8% complete (2/25 endpoints updated)  
**Next:** Continue updating remaining endpoints

