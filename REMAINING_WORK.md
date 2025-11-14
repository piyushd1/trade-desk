# Remaining Work - JWT Migration

**Status:** 14/25 endpoints complete (56%)  
**Last Update:** November 14, 2025

---

## ✅ Completed Files

### 1. zerodha_simple.py - ✅ COMPLETE
**11 endpoints updated** (1 left public):
- `/zerodha/profile` ✅
- `/zerodha/margins` ✅
- `/zerodha/holdings` ✅
- `/zerodha/positions` ✅
- `/zerodha/orders` ✅
- `/zerodha/trades` ✅
- `/zerodha/quote` ✅
- `/zerodha/ltp` ✅
- `/zerodha/ohlc` ✅
- `/zerodha/instruments` ✅
- `/zerodha/historical/{token}` ✅
- `/zerodha/capabilities` - PUBLIC (no JWT needed)

### 2. zerodha_data_management.py - ✅ COMPLETE  
**3 endpoints updated** (4 left public):
- `/instruments/sync` ✅ (requires JWT)
- `/instruments/search` - PUBLIC
- `/instruments/{token}` - PUBLIC
- `/historical/fetch` ✅ (requires JWT)
- `/historical` - PUBLIC (queries local DB)
- `/historical/stats` - PUBLIC (queries local DB)
- `/historical/cleanup` ✅ (requires JWT)

---

## ⏳ Remaining Files (11 endpoints)

### 3. zerodha_streaming.py - ⏳ TODO (7 endpoints)

**File:** `/home/trade-desk/backend/app/api/v1/zerodha_streaming.py`

**Pattern to apply:**
```python
# Add imports at top:
from app.api.v1.auth import get_current_user_dependency
from app.api.v1.zerodha_common import validate_user_owns_session
from app.models.user import User

# For each endpoint, add:
current_user: User = Depends(get_current_user_dependency),

# Replace session lookup with:
session = await validate_user_owns_session(current_user, user_identifier, db)
```

**Endpoints:**
1. `/stream/start` (POST) - Line ~143
2. `/stream/stop` (POST) - Line ~174
3. `/stream/update` (POST) - Line ~188
4. `/stream/status` (GET) - Line ~211
5. `/stream/ticks` (GET) - Line ~227
6. `/session/status` (GET) - Line ~242
7. `/session/validate` (POST) - Line ~266

---

### 4. orders.py - ⏳ TODO (4 endpoints)

**File:** `/home/trade-desk/backend/app/api/v1/orders.py`

**Pattern to apply:**
```python
# Add imports at top:
from app.api.v1.auth import get_current_user_dependency
from app.api.v1.zerodha_common import validate_user_owns_session
from app.models.user import User

# For each endpoint, add:
current_user: User = Depends(get_current_user_dependency),

# Replace session lookup with:
session = await validate_user_owns_session(current_user, request.user_identifier, db)
```

**Endpoints:**
1. `/orders/preview` (POST) - Line ~112
2. `/orders/place` (POST) - Line ~147
3. `/orders/modify` (POST) - Line ~195
4. `/orders/cancel` (POST) - Line ~216

---

### 5. auth.py - ⏳ TODO (OAuth endpoints)

**File:** `/home/trade-desk/backend/app/api/v1/auth.py`

**Changes needed:**

**A. Update `/zerodha/connect` (Line ~358):**
```python
@router.get("/zerodha/connect")
async def zerodha_oauth_initiate(
    current_user: User = Depends(get_current_user_dependency),  # ADD THIS
    request: Request,
    state: Optional[str] = Query(None),
):
    # Generate OAuth URL
    oauth_url = zerodha_service.get_login_url(state=state or "default")
    
    # Return URL (user will complete OAuth in browser)
    return {
        "status": "success",
        "login_url": oauth_url,
        "user_identifier": state or "default",
        "instructions": "Open login_url in browser to complete Zerodha authentication"
    }
```

**B. Update `/zerodha/callback` (Line ~406):**
```python
@router.get("/zerodha/callback")
async def zerodha_oauth_callback(
    request_token: str,
    state: Optional[str] = None,
    current_user: User = Depends(get_current_user_dependency),  # ADD THIS
    request: Request = None,
    db: AsyncSession = Depends(get_db)
):
    # ... existing code ...
    
    # When calling _store_broker_session, add user_id:
    broker_session = await _store_broker_session(
        db=db,
        user_identifier=user_identifier,
        user_id=current_user.id,  # ADD THIS
        broker="zerodha",
        session_data=session_data
    )
```

**C. Update `_store_broker_session` helper (Line ~53):**
```python
async def _store_broker_session(
    db: AsyncSession,
    user_identifier: str,
    user_id: int,  # ADD THIS PARAMETER
    broker: str,
    session_data: Dict
) -> BrokerSession:
    # ... existing code ...
    
    if broker_session:
        broker_session.user_id = user_id  # ADD THIS
        broker_session.access_token_encrypted = encrypted_token
        # ... rest of updates
    else:
        broker_session = BrokerSession(
            user_identifier=user_identifier,
            user_id=user_id,  # ADD THIS
            broker=broker,
            # ... rest of fields
        )
```

---

## 🔄 After Completing Updates

### 1. Restart Backend
```bash
pkill -f "uvicorn app.main:app"
cd /home/trade-desk/backend
source venv/bin/activate
nohup python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 > /tmp/backend.log 2>&1 &
echo $! > /tmp/backend.pid
tail -f /tmp/backend.log
```

### 2. Test Authentication Flow

See `TESTING_STEPS.md` for detailed testing instructions.

---

## 📊 Progress Tracker

- [x] Phase 1: Database schema (user_id in broker_sessions)
- [x] Phase 1: Reset admin password
- [x] Phase 2: Remove Nginx Basic Auth
- [x] Phase 2: Create ownership validation helper
- [x] zerodha_simple.py (11/11 endpoints)
- [x] zerodha_data_management.py (3/3 endpoints)
- [ ] zerodha_streaming.py (0/7 endpoints) - **REMAINING**
- [ ] orders.py (0/4 endpoints) - **REMAINING**
- [ ] auth.py OAuth updates (0/2 endpoints) - **REMAINING**
- [ ] Restart backend
- [ ] Test authentication flow
- [ ] Test Zerodha APIs with JWT

**Overall:** 14/25 endpoints (56% complete)

---

**Next:** Complete remaining 11 endpoints, restart backend, test.

