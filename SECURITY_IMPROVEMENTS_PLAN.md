# Security Improvements Plan

**Date:** January 31, 2025  
**Status:** 📋 Planning

---

## 🎯 Current Security Status

### ✅ What's Already Secure

1. **JWT Authentication**: Already implemented for most endpoints
2. **HTTP Basic Auth**: Nginx layer protection (if configured)
3. **Password Hashing**: Bcrypt for password storage
4. **Encrypted Token Storage**: Fernet encryption for broker tokens
5. **CORS Configuration**: Properly configured allowed origins
6. **HTTPS/SSL**: Let's Encrypt certificates in place
7. **Audit Logging**: Complete audit trail of all actions

### ⚠️ Current Security Gaps

1. **Some Public Endpoints**: Instrument search, session status, etc.
2. **No Rate Limiting**: APIs can be called unlimited times
3. **No IP Whitelisting**: Anyone can attempt to access
4. **Weak Session Management**: No session timeout tracking
5. **Documentation Always Public**: Swagger UI accessible to anyone
6. **No 2FA**: Single factor authentication only

---

## 🛡️ Recommended Security Improvements

### Priority 1: High Impact (Implement Immediately)

#### 1.1 Frontend Authentication Gateway ⭐⭐⭐⭐⭐

**Problem**: Currently no frontend, APIs are directly accessible  
**Solution**: Create a login-protected web interface

**Implementation:**
- Build Next.js frontend with protected routes
- Redirect all unauthenticated users to login page
- Store JWT token in httpOnly cookies (not localStorage)
- Auto-refresh tokens before expiry
- Logout on inactivity (15 min timeout)

**Files to Create:**
```
frontend/
├── app/
│   ├── login/page.tsx          # Login page
│   ├── (protected)/            # Protected routes group
│   │   ├── layout.tsx          # Auth wrapper
│   │   ├── dashboard/page.tsx  # Main dashboard
│   │   └── ...                 # Other pages
│   └── middleware.ts           # Route protection
```

#### 1.2 Protect All API Endpoints ⭐⭐⭐⭐⭐

**Problem**: Some endpoints don't require authentication  
**Solution**: Add JWT requirement to ALL sensitive endpoints

**Endpoints to Protect:**
- `GET /data/zerodha/data/instruments/search` - Currently public
- `GET /data/zerodha/session/status` - Should require auth
- `GET /technical-analysis/indicators/list` - Keep public (informational)
- All `/data/zerodha/*` endpoints - Require auth

**Implementation:**
```python
# Add to all sensitive endpoints
@router.get("/endpoint")
async def endpoint(
    current_user: User = Depends(get_current_user_dependency),  # Add this
    # ... other params
):
    pass
```

#### 1.3 Rate Limiting ⭐⭐⭐⭐

**Problem**: No protection against brute force or DDoS  
**Solution**: Implement rate limiting using slowapi

**Configuration:**
```python
# backend/requirements.txt
slowapi==0.1.9

# backend/app/main.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Apply to endpoints
@router.post("/login")
@limiter.limit("5/minute")  # 5 attempts per minute
async def login(request: Request, ...):
    pass

@router.post("/orders/place")
@limiter.limit("10/minute")  # 10 orders per minute
async def place_order(request: Request, ...):
    pass
```

#### 1.4 Secure Swagger/Docs ⭐⭐⭐⭐

**Problem**: Documentation is publicly accessible  
**Solution**: Add authentication to /docs endpoint

**Options:**

**Option A: HTTP Basic Auth on Nginx (Easiest)**
```nginx
location /docs {
    auth_basic "Restricted Documentation";
    auth_basic_user_file /etc/nginx/.htpasswd;
    proxy_pass http://localhost:8000;
}

location /redoc {
    auth_basic "Restricted Documentation";
    auth_basic_user_file /etc/nginx/.htpasswd;
    proxy_pass http://localhost:8000;
}

location /openapi.json {
    auth_basic "Restricted Documentation";
    auth_basic_user_file /etc/nginx/.htpasswd;
    proxy_pass http://localhost:8000;
}
```

**Option B: JWT Auth on Docs (More Secure)**
- Create custom docs route with JWT check
- Redirect to login if not authenticated

---

### Priority 2: Medium Impact (Implement Soon)

#### 2.1 IP Whitelisting ⭐⭐⭐

**Problem**: Anyone from anywhere can access  
**Solution**: Whitelist your IP addresses

**Implementation:**
```python
# backend/app/config.py
ALLOWED_IPS: list[str] = Field(
    default=["127.0.0.1"],
    description="Whitelisted IP addresses"
)

# backend/app/main.py
@app.middleware("http")
async def ip_whitelist(request: Request, call_next):
    # Skip for health check
    if request.url.path == "/health":
        return await call_next(request)
    
    # Get client IP
    client_ip = request.client.host
    if settings.ALLOWED_IPS and client_ip not in settings.ALLOWED_IPS:
        return JSONResponse(
            status_code=403,
            content={"detail": "Access forbidden from your IP"}
        )
    return await call_next(request)
```

**Note**: If using dynamic IP, consider:
- VPN with static IP
- Dynamic DNS service
- Skip IP check for /auth/login, add after login

#### 2.2 Session Management ⭐⭐⭐

**Problem**: Tokens don't track active sessions  
**Solution**: Add session tracking table

**Implementation:**
```sql
CREATE TABLE user_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    session_id UUID NOT NULL,
    access_token_hash VARCHAR(255),  -- Hash of JWT
    ip_address VARCHAR(45),
    user_agent TEXT,
    last_activity TIMESTAMP,
    expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Features:**
- Track all active sessions
- Auto-expire on inactivity (15 min)
- Force logout from all devices
- View active sessions in UI

#### 2.3 Enhanced Audit Logging ⭐⭐⭐

**Already implemented but can enhance:**
- Log all failed login attempts
- Log API access patterns
- Alert on suspicious activity
- Weekly security reports

---

### Priority 3: Nice to Have (Future)

#### 3.1 Two-Factor Authentication (2FA) ⭐⭐

**Options:**
- TOTP (Google Authenticator, Authy)
- Email OTP
- SMS OTP (expensive)

**Libraries:**
- `pyotp` for TOTP generation
- `qrcode` for QR code generation

#### 3.2 API Key Authentication ⭐⭐

**For programmatic access:**
- Generate API keys for scripts
- Separate from user passwords
- Can be rotated without password change

#### 3.3 Security Headers ⭐⭐

**Add security headers:**
```python
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response
```

#### 3.4 Request Signature Validation ⭐

**For critical operations:**
- Sign requests with HMAC
- Prevent replay attacks with nonce
- Useful for order placement

---

## 🎯 Recommended Implementation Order

### Week 1: Immediate Security Hardening
1. ✅ Fix duplicate API documentation (today)
2. 🔒 Protect all API endpoints with JWT (today)
3. 🚫 Add rate limiting to login and critical endpoints (tomorrow)
4. 🔐 Secure /docs with HTTP Basic Auth (tomorrow)

### Week 2: Access Control
5. 🌐 Add IP whitelisting (optional if you have static IP)
6. 📊 Review and test all endpoints
7. 📝 Update documentation with security requirements

### Week 3: Session Management
8. 🗄️ Implement session tracking
9. ⏰ Auto-logout on inactivity
10. 🖥️ Build frontend login page

### Future (Optional)
11. 🔐 2FA implementation
12. 🔑 API key system
13. 📧 Email alerts for security events

---

## 🚀 Quick Wins (Implement Today)

### 1. Protect Sensitive Endpoints
Add `current_user: User = Depends(get_current_user_dependency)` to:
- All `/data/zerodha/*` endpoints
- All `/risk/*` endpoints
- All `/orders/*` endpoints
- All `/technical-analysis/*` endpoints (except `/indicators/list`)

### 2. Secure Documentation
Add to Nginx config:
```nginx
location ~ ^/(docs|redoc|openapi.json) {
    auth_basic "TradeDesk Documentation";
    auth_basic_user_file /etc/nginx/.htpasswd_docs;
    proxy_pass http://localhost:8000;
}
```

Create password file:
```bash
sudo htpasswd -c /etc/nginx/.htpasswd_docs piyushdev
sudo systemctl reload nginx
```

### 3. Add Rate Limiting to Login
Protect against brute force attacks

---

## 📋 Security Checklist

- [x] JWT authentication implemented
- [x] Password hashing (bcrypt)
- [x] HTTPS/SSL enabled
- [x] CORS configured
- [x] Audit logging active
- [ ] All endpoints require auth
- [ ] Rate limiting enabled
- [ ] Documentation secured
- [ ] IP whitelisting (optional)
- [ ] Session management
- [ ] Frontend with login
- [ ] 2FA (optional)
- [ ] Security monitoring

---

## 💡 Best Practices

1. **Never commit secrets**: Use .env files (already doing)
2. **Rotate credentials**: Change passwords regularly
3. **Monitor logs**: Review audit logs weekly
4. **Update dependencies**: Keep packages up to date
5. **Backup database**: Regular backups with encryption
6. **Test security**: Regular penetration testing

---

## 🎯 Your Specific Needs

Based on your requirement: **"I want to be the only person who can login"**

### Recommended Approach:

**Option 1: Single User + IP Whitelist (Most Secure)**
```python
# In .env
ALLOWED_IPS=["YOUR_HOME_IP", "YOUR_OFFICE_IP"]
SINGLE_USER_MODE=true
ALLOWED_USER_ID=2  # Your user ID

# Middleware check
if settings.SINGLE_USER_MODE:
    if current_user.id != settings.ALLOWED_USER_ID:
        raise HTTPException(403, "Access denied")
```

**Option 2: Disable User Registration**
```python
# Remove or disable /auth/register endpoint
# Only you can create users via database
```

**Option 3: Frontend with Login Gate**
- Build simple login page
- All routes protected by middleware
- Auto-logout on inactivity
- No public access to any page

**Recommended: Combine all three for maximum security!**

---

## 📝 Next Steps

1. **Choose your approach** from the options above
2. **Let me implement** the quick wins today
3. **Plan frontend** development for next week
4. **Schedule security review** monthly

---

**Questions to Decide:**
1. Do you have a static IP for whitelisting?
2. Do you want a frontend, or just secure the APIs?
3. How important is 2FA for you?
4. Do you want to disable docs in production?

Let me know your preferences and I'll implement the changes!

