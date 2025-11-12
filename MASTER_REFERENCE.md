# TradeDesk - Master Reference Document

**Last Updated:** November 12, 2025  
**Repository:** https://github.com/piyushd1/trade-desk  
**Production URL:** https://piyushdev.com

---

## 📋 Table of Contents
1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Configuration](#configuration)
4. [API Endpoints](#api-endpoints)
5. [Database Schema](#database-schema)
6. [Deployment](#deployment)
7. [Testing](#testing)
8. [Troubleshooting](#troubleshooting)

---

## 🎯 Project Overview

TradeDesk is a SEBI-compliant algorithmic trading platform with:
- Multi-broker support (Zerodha implemented, Groww planned)
- Automated token management
- Comprehensive risk controls
- Complete audit logging
- Modern web interface

### Tech Stack
**Backend:**
- FastAPI (Python 3.12)
- SQLAlchemy (async)
- SQLite (dev) / PostgreSQL (prod ready)
- Alembic for migrations

**Frontend:**
- Next.js 14 (App Router)
- TypeScript
- Tailwind CSS
- shadcn/ui components
- React Query

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Nginx (443)                          │
│  ┌────────────────────┐          ┌────────────────────────┐ │
│  │   Frontend (3001)  │          │   Backend (8000)       │ │
│  │   Next.js 14       │          │   FastAPI              │ │
│  │   /                │          │   /api/*               │ │
│  └────────────────────┘          └────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
              ┌─────▼──────┐     ┌─────▼──────┐
              │  SQLite DB │     │  Services  │
              │  (dev)     │     │  - Token   │
              └────────────┘     │  - Risk    │
                                 │  - Audit   │
                                 └────────────┘
```

### Directory Structure
```
trade-desk/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # API endpoints
│   │   ├── models/          # Database models
│   │   ├── services/        # Business logic
│   │   ├── brokers/         # Broker integrations
│   │   ├── utils/           # Utilities
│   │   ├── config.py        # Configuration
│   │   ├── database.py      # DB setup
│   │   └── main.py          # FastAPI app
│   ├── alembic/             # DB migrations
│   └── venv/                # Python virtual env
├── frontend/
│   ├── app/                 # Next.js pages
│   ├── components/ui/       # UI components
│   ├── lib/                 # API client, hooks
│   └── public/              # Static assets
├── docs/                    # Planning documents
└── MASTER_REFERENCE.md      # This file
```

---

## ⚙️ Configuration

### Backend Environment Variables
**Location:** `/home/trade-desk/backend/.env`

**Critical Settings:**
```bash
# Application
APP_NAME=TradeDesk
APP_ENV=development
DEBUG=True
APP_DOMAIN=piyushdev.com
APP_URL=https://piyushdev.com

# Database
DATABASE_URL=sqlite+aiosqlite:///./tradedesk.db

# Security (MUST BE SECURE IN PRODUCTION)
SECRET_KEY=<your-secret-key>
ENCRYPTION_KEY=<32-byte-base64-fernet-key>
JWT_SECRET_KEY=<your-jwt-secret>

# Zerodha
ZERODHA_API_KEY=<your-api-key>
ZERODHA_API_SECRET=<your-api-secret>
ZERODHA_REDIRECT_URL=https://piyushdev.com/api/v1/auth/zerodha/callback

# Token Refresh
ZERODHA_AUTO_REFRESH_ENABLED=true
ZERODHA_REFRESH_INTERVAL_MINUTES=15
ZERODHA_REFRESH_EXPIRY_BUFFER_MINUTES=60

# Risk Management (Defaults)
MAX_POSITION_VALUE=50000
MAX_DAILY_LOSS=5000
MAX_POSITIONS=5
MAX_DRAWDOWN_PCT=15.0
DEFAULT_STOP_LOSS_PCT=2.0
DEFAULT_TARGET_PROFIT_PCT=4.0
```

### Frontend Environment Variables
**Location:** `/home/trade-desk/frontend/.env.local`

```bash
NEXT_PUBLIC_API_URL=https://piyushdev.com/api/v1
NEXT_PUBLIC_APP_NAME=TradeDesk
```

### Nginx Configuration
**Location:** `/etc/nginx/sites-enabled/trade-desk`

**Key Points:**
- Frontend served on `/` → proxied to `localhost:3001`
- Backend API on `/api/*` → proxied to `localhost:8000`
- SSL certificates from Let's Encrypt
- CORS headers configured

---

## 🔌 API Endpoints

### Authentication & OAuth
```
GET  /api/v1/auth/zerodha/connect?state=<user_id>
  → Returns Zerodha login URL

GET  /api/v1/auth/zerodha/callback?request_token=...&status=success&state=<user_id>
  → Exchanges token, stores session, redirects to dashboard

GET  /api/v1/auth/zerodha/session?user_identifier=<user_id>
  → Get stored session details

POST /api/v1/auth/zerodha/refresh?user_identifier=<user_id>
  → Manually refresh access token

GET  /api/v1/auth/zerodha/refresh/status
  → Get token refresh service status

GET  /api/v1/auth/brokers/status
  → Get all broker connection status
```

### Risk Management
```
GET  /api/v1/risk/config?user_id=<id>
  → Get risk configuration

PUT  /api/v1/risk/config?user_id=<id>
  → Update risk limits

POST /api/v1/risk/kill-switch?user_id=<id>
  → Toggle kill switch (enable/disable trading)

GET  /api/v1/risk/kill-switch/status?user_id=<id>
  → Get kill switch status

POST /api/v1/risk/pre-trade-check
  → Validate order against risk limits

GET  /api/v1/risk/metrics/daily?user_id=<id>
  → Get today's trading metrics

GET  /api/v1/risk/metrics/history?user_id=<id>&days=7
  → Get historical metrics

GET  /api/v1/risk/breaches?user_id=<id>&limit=100
  → Query risk breach logs

GET  /api/v1/risk/status?user_id=<id>
  → Get comprehensive risk status

GET  /api/v1/risk/limits/check?user_id=<id>
  → Check limit utilization
```

### Audit & Compliance
```
GET  /api/v1/audit/logs?action=<action>&limit=100&offset=0
  → Query audit logs

GET  /api/v1/audit/logs/<id>
  → Get specific audit log

GET  /api/v1/system/events?event_type=<type>&severity=<level>&limit=100
  → Query system events

GET  /api/v1/system/events/<id>
  → Get specific system event
```

### Health & Monitoring
```
GET  /health
  → Basic health check

GET  /api/v1/health/status
  → Detailed health status

GET  /api/v1/health/compliance
  → Compliance status
```

---

## 🗄️ Database Schema

### Tables

**broker_sessions** - Encrypted token storage
- user_identifier, broker, access_token_encrypted, refresh_token_encrypted
- public_token, status, meta, expires_at

**risk_configs** - Risk limit configuration
- user_id (null = system-wide), max_position_value, max_positions
- max_order_value, max_orders_per_day, ops_limit
- max_daily_loss, trading_enabled (kill switch)

**daily_risk_metrics** - Daily trading metrics
- user_id, trading_date, orders_placed, orders_executed
- realized_pnl, unrealized_pnl, total_pnl
- loss_limit_breached, risk_breaches

**audit_logs** - User action audit trail
- user_id, username, action, entity_type, entity_id
- details (JSON), ip_address, user_agent, created_at

**system_events** - System-level events
- event_type, severity, component, message
- details (JSON), stack_trace, created_at

**risk_breach_logs** - Risk violations
- user_id, breach_type, breach_details (JSON)
- action_taken, created_at

### Migrations
```bash
cd /home/trade-desk/backend
source venv/bin/activate
alembic upgrade head
```

Current revision: `20251112_064150`

---

## 🚀 Deployment

### Start Backend
```bash
cd /home/trade-desk/backend
source venv/bin/activate
nohup python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 > /tmp/backend.log 2>&1 &
echo $! > /tmp/backend.pid
```

### Start Frontend
```bash
cd /home/trade-desk/frontend
PORT=3001 nohup npm start > /tmp/frontend-prod.log 2>&1 &
echo $! > /tmp/frontend.pid
```

### Restart Services
```bash
# Backend
kill $(cat /tmp/backend.pid)
cd /home/trade-desk/backend && source venv/bin/activate
nohup python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 > /tmp/backend.log 2>&1 &
echo $! > /tmp/backend.pid

# Frontend
kill $(cat /tmp/frontend.pid)
cd /home/trade-desk/frontend
PORT=3001 nohup npm start > /tmp/frontend-prod.log 2>&1 &
echo $! > /tmp/frontend.pid

# Nginx
sudo systemctl reload nginx
```

### Check Status
```bash
# Health checks
curl https://piyushdev.com/health
curl https://piyushdev.com/api/v1/auth/brokers/status

# Process status
ps aux | grep uvicorn
ps aux | grep "npm start"

# Logs
tail -f /tmp/backend.log
tail -f /tmp/frontend-prod.log
```

---

## 🧪 Testing

### Run All Tests
```bash
cd /home/trade-desk

# Risk management unit tests
python test_risk_management.py

# Audit logging API tests
./test_audit_logging.sh

# Risk management API tests
./test_risk_api.sh

# OAuth flow test
./test_oauth_flow.sh
```

### Test Results
- ✅ 23 tests passing
- ✅ All API endpoints functional
- ✅ OAuth flow working
- ✅ Risk controls operational
- ✅ Audit logging verified

---

## 🔧 Troubleshooting

### Common Issues

**1. OAuth Callback Returns JSON Instead of Redirecting**
- **Cause:** Backend returns JSON response
- **Fix:** Backend now uses `RedirectResponse` to redirect to frontend
- **Verify:** Check `/backend/app/api/v1/auth.py` line ~324

**2. Encryption Key Error**
- **Cause:** Invalid Fernet key format
- **Fix:** Generate new key: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
- **Update:** Set in `.env` as `ENCRYPTION_KEY=<generated-key>`

**3. Datetime Serialization Error**
- **Cause:** SQLite can't serialize timezone-aware datetimes in JSON
- **Fix:** Convert to naive UTC and serialize datetime objects to ISO strings
- **Location:** `/backend/app/api/v1/auth.py` `_store_broker_session` function

**4. Frontend Not Loading**
- **Check:** `ps aux | grep "npm start"`
- **Restart:** Kill and restart frontend on port 3001
- **Logs:** `tail -f /tmp/frontend-prod.log`

**5. Backend 502 Error**
- **Check:** `curl http://127.0.0.1:8000/health`
- **Restart:** Kill and restart backend
- **Logs:** `tail -f /tmp/backend.log`

---

## 🔐 Security Checklist

### ✅ Implemented
- [x] SSL/HTTPS with Let's Encrypt
- [x] Encrypted token storage (Fernet)
- [x] Environment-based secrets
- [x] CORS properly configured
- [x] Security headers (HSTS, X-Frame-Options, etc.)
- [x] Audit logging for all operations
- [x] IP address tracking
- [x] Kill switch for emergency stop

### ⚠️ Production Recommendations
- [ ] Change DEBUG=False in production
- [ ] Use PostgreSQL instead of SQLite
- [ ] Rotate encryption keys periodically
- [ ] Set up Redis for caching
- [ ] Enable rate limiting
- [ ] Add 2FA for admin access
- [ ] Set up monitoring/alerts
- [ ] Regular security audits

---

## 📊 Current Status

### What's Working
- ✅ Backend APIs (20+ endpoints)
- ✅ Token auto-refresh (15-min intervals)
- ✅ Risk management (6-layer validation)
- ✅ Audit logging (SEBI compliant)
- ✅ Frontend UI (6 pages)
- ✅ OAuth authentication
- ✅ SSL/HTTPS
- ✅ Database migrations

### Known Issues
- ⚠️ OAuth redirect goes to root instead of dashboard (needs frontend fix)
- ⚠️ Frontend dashboard needs session loading logic
- ⚠️ Some hardcoded URLs need to use environment variables

### Not Yet Implemented
- [ ] Order placement
- [ ] Strategy management
- [ ] Paper trading
- [ ] Backtest engine
- [ ] Real-time WebSocket updates
- [ ] Groww integration

---

## 🎯 Quick Commands

### Development
```bash
# Backend dev mode
cd /home/trade-desk/backend && source venv/bin/activate
uvicorn app.main:app --reload

# Frontend dev mode
cd /home/trade-desk/frontend
npm run dev

# Run migrations
cd /home/trade-desk/backend && source venv/bin/activate
alembic upgrade head

# Generate new migration
alembic revision --autogenerate -m "description"
```

### Production
```bash
# Build frontend
cd /home/trade-desk/frontend
npm run build

# Start services (see Deployment section)
```

### Testing
```bash
# Quick health check
curl https://piyushdev.com/health

# Test OAuth URL generation
curl "https://piyushdev.com/api/v1/auth/zerodha/connect?state=test"

# Check risk status
curl "https://piyushdev.com/api/v1/risk/status?user_id=1"

# View audit logs
curl "https://piyushdev.com/api/v1/audit/logs?limit=10"
```

---

## 📝 Development History

### Day 1 (Nov 11, 2025)
- Infrastructure setup (GCP, SSL, Nginx)
- FastAPI backend foundation
- Zerodha OAuth integration
- Encrypted token storage
- Multi-user session support

### Day 2 (Nov 12, 2025)
- Git repository initialized
- Token auto-refresh system
- SEBI-compliant audit logging
- Comprehensive risk management
- Next.js frontend with OAuth
- Production deployment

### Commits
1. Initial import
2. Token auto-refresh & audit logging
3. Documentation cleanup
4. Risk management system
5. Frontend implementation
6. Bug fixes (encryption, datetime, redirects)

---

## 🎓 Key Learnings

1. **SQLite Limitations:** Doesn't handle timezone-aware datetimes in JSON fields
2. **Fernet Keys:** Must be exactly 32 bytes, base64-encoded
3. **OAuth Flow:** Backend should redirect to frontend, not return JSON
4. **CORS:** Must explicitly allow frontend domain
5. **Production:** Always test with production build, not just dev mode

---

## 📞 Support

For issues:
1. Check logs: `/tmp/backend.log` and `/tmp/frontend-prod.log`
2. Verify services are running
3. Check this reference document
4. Review git commit history for recent changes

---

**End of Master Reference**

