# JWT Migration Plan - Secure Zerodha API Access

**Date:** November 14, 2025  
**Objective:** Remove Nginx Basic Auth, implement JWT + user ownership validation

---

## 🎯 Overview

### Current Problem
- Nginx Basic Auth protects entire domain (single password: `piyushdeveshwar:Lead@102938`)
- Zerodha API endpoints only require `user_identifier` query parameter
- No validation that the caller owns the `user_identifier`
- Anyone with Basic Auth credentials can access any user's Zerodha data

### Solution
- Remove Nginx Basic Auth
- Require JWT Bearer token on all protected endpoints
- Validate user owns the `user_identifier` before accessing Zerodha APIs
- Keep public endpoints (login, health) without authentication

---

## 📋 Implementation Steps

### Phase 1: Database Schema Update ✅ (Already exists)

**What's needed:**
- Link between platform users (`users` table) and Zerodha sessions (`broker_sessions` table)

**Current schema:**
```sql
-- broker_sessions table
user_identifier TEXT  -- This is Zerodha's OAuth state (e.g., "RO0252")
broker TEXT           -- "zerodha"
status TEXT           -- "active", "expired"
```

**What we need:**
- Add `user_id` foreign key to `broker_sessions` table
- This links TradeDesk users to their Zerodha sessions

**Migration:**
```python
# Alembic migration to add user_id to broker_sessions
def upgrade():
    op.add_column('broker_sessions', sa.Column('user_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_broker_sessions_user_id', 'broker_sessions', 'users', ['user_id'], ['id'])
    op.create_index('ix_broker_sessions_user_id', 'broker_sessions', ['user_id'])
```

---

### Phase 2: Remove Nginx Basic Auth (Manual)

**Files to modify:** `/etc/nginx/sites-available/trade-desk`

**Instructions:**
1. Backup current config:
   ```bash
   sudo cp /etc/nginx/sites-available/trade-desk /etc/nginx/sites-available/trade-desk.backup.$(date +%Y%m%d)
   ```

2. Edit config:
   ```bash
   sudo nano /etc/nginx/sites-available/trade-desk
   ```

3. Remove these lines from ALL location blocks:
   ```nginx
   # DELETE THESE TWO LINES from each location {} block:
   auth_basic "TradeDesk Restricted";
   auth_basic_user_file /etc/nginx/.htpasswd;
   ```

   Affected locations (lines to remove):
   - Lines 52-54 (global server block)
   - Lines 58-59 (`location /api/`)
   - Lines 75-76 (`location /health`)
   - Lines 85-86 (`location /docs`)
   - Lines 92-93 (`location /redoc`)
   - Lines 100-101 (`location /`)

4. Test config:
   ```bash
   sudo nginx -t
   ```

5. If test passes, reload:
   ```bash
   sudo systemctl reload nginx
   ```

6. Verify Basic Auth is gone:
   ```bash
   curl -I https://piyushdev.com/health
   # Should return 200 OK without requiring -u credentials
   ```

---

### Phase 3: Update Database Schema (Backend)

**Task:** Add `user_id` to `broker_sessions` table

**Files to create:**
1. Alembic migration file
2. Update `BrokerSession` model

**Implementation:**

```python
# backend/alembic/versions/YYYYMMDD_add_user_id_to_broker_sessions.py
def upgrade():
    op.add_column('broker_sessions', sa.Column('user_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_broker_sessions_user_id',
        'broker_sessions', 'users',
        ['user_id'], ['id'],
        ondelete='CASCADE'
    )
    op.create_index('ix_broker_sessions_user_id', 'broker_sessions', ['user_id'])

def downgrade():
    op.drop_index('ix_broker_sessions_user_id', 'broker_sessions')
    op.drop_constraint('fk_broker_sessions_user_id', 'broker_sessions', type_='foreignkey')
    op.drop_column('broker_sessions', 'user_id')
```

```python
# backend/app/models/broker_session.py
# Add to BrokerSession model:
user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=True, index=True)
user = relationship("User", back_populates="broker_sessions")

# Add to User model:
broker_sessions = relationship("BrokerSession", back_populates="user", cascade="all, delete-orphan")
```

**Run migration:**
```bash
cd /home/trade-desk/backend
source venv/bin/activate
alembic revision --autogenerate -m "add user_id to broker_sessions"
alembic upgrade head
```

**Backfill existing sessions:**
```python
# One-time script to link existing broker sessions to users
# For now, all sessions belong to user_id=1 (admin)
UPDATE broker_sessions SET user_id = 1 WHERE user_id IS NULL;
```

---

### Phase 4: Add User Ownership Validation Helper

**File:** `backend/app/api/v1/zerodha_common.py`

**Add new function:**

```python
async def validate_user_owns_session(
    current_user: User,
    user_identifier: str,
    db: AsyncSession
) -> BrokerSession:
    """
    Validate that the current user owns the Zerodha session.
    
    Raises:
        HTTPException: 404 if session not found, 403 if user doesn't own it
    
    Returns:
        BrokerSession: The validated session
    """
    session = await get_active_zerodha_session(db, user_identifier)
    
    # Check ownership
    if session.user_id != current_user.id:
        # Admin users can access any session (optional)
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"You do not have permission to access session {user_identifier}"
            )
    
    return session
```

---

### Phase 5: Update Zerodha Endpoints (Add JWT)

**Files to modify:**
1. `backend/app/api/v1/zerodha_simple.py` (12 endpoints)
2. `backend/app/api/v1/zerodha_data_management.py` (7 endpoints)
3. `backend/app/api/v1/zerodha_streaming.py` (7 endpoints)
4. `backend/app/api/v1/orders.py` (4 endpoints)

**Pattern for each endpoint:**

**BEFORE:**
```python
@router.get("/zerodha/profile")
async def get_profile(
    user_identifier: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    kite = await _get_kite_client_for_identifier(user_identifier, db)
    # ...
```

**AFTER:**
```python
@router.get("/zerodha/profile")
async def get_profile(
    current_user: User = Depends(get_current_user_dependency),  # ✅ Require JWT
    user_identifier: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    # ✅ Validate ownership
    session = await validate_user_owns_session(current_user, user_identifier, db)
    access_token = decrypt_access_token(session)
    kite = get_kite_client(access_token)
    # ...
```

**Count of changes needed:**
- `zerodha_simple.py`: 11 endpoints (skip `/capabilities`)
- `zerodha_data_management.py`: 4 endpoints (skip `/search`, `/instruments/{token}`, `/historical`, `/historical/stats`)
- `zerodha_streaming.py`: 6 endpoints (skip public ones if any)
- `orders.py`: 4 endpoints

**Total:** ~25 endpoint modifications

---

### Phase 6: Update OAuth Callback to Link User

**File:** `backend/app/api/v1/auth.py`

**Modify `/zerodha/callback` endpoint:**

**BEFORE:**
```python
@router.get("/zerodha/callback")
async def zerodha_oauth_callback(
    request_token: str,
    state: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    # Stores session with user_identifier = state
    # No link to platform user
```

**AFTER:**
```python
@router.get("/zerodha/callback")
async def zerodha_oauth_callback(
    request_token: str,
    state: Optional[str] = None,
    current_user: User = Depends(get_current_user_dependency),  # ✅ Require JWT
    db: AsyncSession = Depends(get_db)
):
    # Exchange token
    session_data = await zerodha_service.exchange_request_token(request_token)
    
    # Store with user_id link
    broker_session = await _store_broker_session(
        db=db,
        user_identifier=state or "default",
        user_id=current_user.id,  # ✅ Link to user
        broker="zerodha",
        session_data=session_data
    )
```

**Update `_store_broker_session` helper:**
```python
async def _store_broker_session(
    db: AsyncSession,
    user_identifier: str,
    user_id: int,  # ✅ New parameter
    broker: str,
    session_data: Dict
) -> BrokerSession:
    # ... existing code ...
    
    if broker_session:
        broker_session.user_id = user_id  # ✅ Update
    else:
        broker_session = BrokerSession(
            user_identifier=user_identifier,
            user_id=user_id,  # ✅ Set
            broker=broker,
            # ... rest
        )
```

---

### Phase 7: Update `/zerodha/connect` Endpoint

**Current flow:**
1. User calls `/zerodha/connect?state=RO0252`
2. Gets Zerodha OAuth URL
3. Completes OAuth in browser
4. Redirected to `/zerodha/callback`

**Problem:** User needs JWT to access `/zerodha/callback` now

**Solution:** Make `/zerodha/callback` accept JWT from query param OR header

**Updated flow:**
1. User logs in → gets JWT
2. User calls `/zerodha/connect?state=RO0252` with JWT header
3. Gets Zerodha OAuth URL **with JWT embedded**
4. Completes OAuth in browser
5. Redirected to `/zerodha/callback?token=<JWT>&request_token=<ZERODHA>`
6. Callback validates JWT from query param

**Implementation:**

```python
@router.get("/zerodha/connect")
async def zerodha_oauth_initiate(
    current_user: User = Depends(get_current_user_dependency),  # ✅ Require JWT
    state: Optional[str] = Query(None),
    request: Request = None
):
    # Get user's access token from Authorization header
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "") if "Bearer " in auth_header else None
    
    # Generate OAuth URL
    oauth_url = zerodha_service.get_login_url(state=state or "default")
    
    # Append JWT to callback URL
    callback_url_with_token = f"{oauth_url}&jwt={token}"
    
    return {
        "status": "success",
        "login_url": callback_url_with_token,
        "user_identifier": state or "default"
    }

@router.get("/zerodha/callback")
async def zerodha_oauth_callback(
    request_token: str,
    state: Optional[str] = None,
    jwt: Optional[str] = Query(None),  # ✅ Accept from query param
    db: AsyncSession = Depends(get_db)
):
    # Validate JWT
    if not jwt:
        raise HTTPException(status_code=401, detail="JWT required")
    
    payload = auth_service.decode_token(jwt)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid JWT")
    
    user_id = payload.get("user_id")
    user = await auth_service.get_user_by_id(user_id, db)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    # Exchange token and link to user
    # ... rest of callback logic
```

---

### Phase 8: Restart Backend

```bash
# Stop current backend
pkill -f "uvicorn app.main:app"

# Restart with new code
cd /home/trade-desk/backend
source venv/bin/activate
nohup python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 > /tmp/backend.log 2>&1 &
echo $! > /tmp/backend.pid

# Tail logs to verify startup
tail -f /tmp/backend.log
```

---

## 🧪 Testing Plan

### Test 1: Public Endpoints (No JWT Required)

**Endpoints that should work WITHOUT JWT:**
- `GET /health` - Health check
- `GET /api/v1/health/ping` - Ping
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/refresh` - Token refresh

**Test commands:**
```bash
# Should work without JWT
curl https://piyushdev.com/health

# Should work without JWT
curl -X POST https://piyushdev.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

**Expected:** All return 200 OK

---

### Test 2: JWT Authentication Flow

**Step 1: Login**
```bash
# Login and save token
LOGIN_RESPONSE=$(curl -s -X POST https://piyushdev.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}')

# Extract access token
ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

echo "Access Token: $ACCESS_TOKEN"
```

**Expected:** Get valid JWT token

**Step 2: Access Protected Endpoint**
```bash
# Get current user profile
curl -H "Authorization: Bearer $ACCESS_TOKEN" \
  https://piyushdev.com/api/v1/auth/me | python3 -m json.tool
```

**Expected:** Returns user profile with status: success

**Step 3: Test Without JWT**
```bash
# Try without JWT - should fail
curl https://piyushdev.com/api/v1/auth/me
```

**Expected:** 401 Unauthorized with "Not authenticated" message

---

### Test 3: Zerodha OAuth with JWT

**Step 1: Get OAuth URL**
```bash
# Must provide JWT in header
curl -H "Authorization: Bearer $ACCESS_TOKEN" \
  "https://piyushdev.com/api/v1/auth/zerodha/connect?state=RO0252" | python3 -m json.tool
```

**Expected:** Returns login_url with embedded JWT

**Step 2: Complete OAuth**
1. Copy the `login_url` from response
2. Open in browser
3. Complete Zerodha login
4. Should redirect to callback with JWT in URL

**Expected:** Successfully stores session linked to your user

**Step 3: Verify Session**
```bash
curl -H "Authorization: Bearer $ACCESS_TOKEN" \
  "https://piyushdev.com/api/v1/auth/zerodha/session?user_identifier=RO0252" | python3 -m json.tool
```

**Expected:** Returns session details with your user_id

---

### Test 4: Zerodha Data APIs with JWT

**Test valid access (your own session):**
```bash
# Get profile - should work
curl -H "Authorization: Bearer $ACCESS_TOKEN" \
  "https://piyushdev.com/api/v1/data/zerodha/profile?user_identifier=RO0252" | python3 -m json.tool

# Get margins - should work
curl -H "Authorization: Bearer $ACCESS_TOKEN" \
  "https://piyushdev.com/api/v1/data/zerodha/margins?user_identifier=RO0252" | python3 -m json.tool

# Get positions - should work
curl -H "Authorization: Bearer $ACCESS_TOKEN" \
  "https://piyushdev.com/api/v1/data/zerodha/positions?user_identifier=RO0252" | python3 -m json.tool
```

**Expected:** All return 200 OK with data

**Test unauthorized access (someone else's session):**
```bash
# Try to access with different user_identifier (if it exists)
curl -H "Authorization: Bearer $ACCESS_TOKEN" \
  "https://piyushdev.com/api/v1/data/zerodha/profile?user_identifier=OTHER_ID" | python3 -m json.tool
```

**Expected:** 403 Forbidden - "You do not have permission"

**Test without JWT:**
```bash
# Try without JWT - should fail
curl "https://piyushdev.com/api/v1/data/zerodha/profile?user_identifier=RO0252"
```

**Expected:** 401 Unauthorized

---

### Test 5: Order APIs with JWT

**Test order preview:**
```bash
curl -H "Authorization: Bearer $ACCESS_TOKEN" \
  -X POST "https://piyushdev.com/api/v1/orders/preview" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
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

**Expected:** Returns margin calculation and risk checks

**Test without JWT:**
```bash
# Should fail
curl -X POST "https://piyushdev.com/api/v1/orders/preview" \
  -H "Content-Type: application/json" \
  -d '{...same payload...}'
```

**Expected:** 401 Unauthorized

---

### Test 6: Docs Access

**Test Swagger UI:**
```bash
curl -I https://piyushdev.com/docs
```

**Expected:** 200 OK (no authentication required now)

**Note:** Docs are public, but all API operations require JWT

---

## 📊 Summary of Changes

### Files to Modify (Backend Code)

| File | Changes | Count |
|------|---------|-------|
| `models/broker_session.py` | Add `user_id` field | 1 |
| `models/user.py` | Add `broker_sessions` relationship | 1 |
| `alembic/versions/YYYYMMDD_*.py` | New migration | 1 |
| `api/v1/zerodha_common.py` | Add `validate_user_owns_session()` | 1 |
| `api/v1/auth.py` | Update OAuth callback & connect | 2 |
| `api/v1/zerodha_simple.py` | Add JWT to 11 endpoints | 11 |
| `api/v1/zerodha_data_management.py` | Add JWT to 4 endpoints | 4 |
| `api/v1/zerodha_streaming.py` | Add JWT to 6 endpoints | 6 |
| `api/v1/orders.py` | Add JWT to 4 endpoints | 4 |
| **TOTAL** | | **31 changes** |

### Files to Modify (Server Config - Manual)

| File | Changes |
|------|---------|
| `/etc/nginx/sites-available/trade-desk` | Remove `auth_basic` lines |

---

## 🎯 Success Criteria

- [ ] Nginx Basic Auth removed
- [ ] All public endpoints work without JWT
- [ ] All protected endpoints require JWT
- [ ] User can complete Zerodha OAuth with JWT
- [ ] User can access own Zerodha data with JWT
- [ ] User CANNOT access other users' Zerodha data
- [ ] Order APIs require JWT and validate ownership
- [ ] Docs are accessible but all operations need JWT

---

## 🚨 Rollback Plan

If anything breaks:

1. **Restore Nginx Basic Auth:**
   ```bash
   sudo cp /etc/nginx/sites-available/trade-desk.backup.YYYYMMDD /etc/nginx/sites-available/trade-desk
   sudo nginx -t
   sudo systemctl reload nginx
   ```

2. **Revert Backend Code:**
   ```bash
   cd /home/trade-desk
   git log --oneline  # Find commit before changes
   git reset --hard <commit-hash>
   
   # Restart backend
   pkill -f "uvicorn app.main:app"
   cd backend && source venv/bin/activate
   nohup python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 > /tmp/backend.log 2>&1 &
   ```

3. **Revert Database Migration:**
   ```bash
   cd /home/trade-desk/backend
   source venv/bin/activate
   alembic downgrade -1
   ```

---

## 📝 Notes

- JWT tokens expire after 15 minutes (access) and 7 days (refresh)
- Admin users can access any user's sessions (optional feature)
- Keep `/health` and `/docs` public for monitoring
- Audit all actions with user_id for compliance

---

**Ready to implement?** Confirm and we'll proceed phase by phase.

