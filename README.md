# TradeDesk - Personal Algo Trading Platform

**SEBI-Compliant Algorithmic Trading Platform**

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-Private-red.svg)]()

---

## 🎯 Overview

TradeDesk is a personal algorithmic trading platform designed for SEBI compliance. It runs on a **Raspberry Pi 4B at home** with **Tailscale-only remote access** — no public ports forwarded, no public internet exposure.

- **Multi-broker support** — Zerodha Kite Connect (live) + IndStocks/IndMoney (in progress)
- **Encrypted token storage** with automatic refresh where supported
- **SEBI-compliant audit logging** with 7-year retention and immutable records
- **Risk management** — position limits, daily loss tracking, kill switch
- **Portfolio data pipeline** — 15-min snapshots into SQLite, aggregated metrics (Sharpe/Sortino/VaR/alpha/beta)
- **Backup / restore drills** using native SQLite `.backup` command
- **Strategy SDK + paper trading engine** (planned, Phase 2)

### Stack

- **Backend**: FastAPI + SQLAlchemy (async, aiosqlite) + Alembic migrations + APScheduler
- **Frontend**: Next.js 15 (standalone output) + React Query + Tailwind CSS
- **Database**: SQLite with WAL mode (Postgres/TimescaleDB in a later phase)
- **Broker SDKs**: `kiteconnect` (Zerodha), IndStocks REST (in progress)
- **Deployment**: Docker Compose + systemd + Tailscale Serve on Raspberry Pi OS Bookworm (arm64)

---

## 🚀 Running TradeDesk

Two supported paths: **local dev** (bare-metal Python, for working on the code) and **Pi production** (Docker + systemd + Tailscale, for the always-on deployment).

### Local development

```bash
git clone git@github.com:piyushd1/trade-desk.git
cd trade-desk

# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env                      # edit with your local values
alembic upgrade head
python scripts/create_default_user.py     # seed admin
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Frontend (separate terminal)
cd ../frontend
cp .env.local.example .env.local          # NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
npm install
npm run dev                                # http://localhost:3000
```

### Raspberry Pi production deployment

**→ Read [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md)** — the authoritative runbook.

It covers the full end-to-end: first-time Pi setup, Tailscale + Docker install, env file configuration, systemd unit installation, Docker image build, Alembic migrations, admin user seeding, Zerodha OAuth handshake, the `td-sudo` scoped-sudo toggle system, smoke tests, reboot verification, daily operations (log watching, re-auth, backup), and a full troubleshooting reference for every gotcha discovered during the 2026-04-15 deploy.

---

## 📚 Documentation

### How to run this
- **[Deployment Guide](docs/DEPLOYMENT.md)** — authoritative runbook for Pi production deployment
- **[Pi Deployment Handoff State](docs/plans/HANDOFF-2026-04-15.md)** — current state, discovered gotchas, commits
- **[Active plan](docs/plans/2026-04-15-pi-deployment-plan.md)** — original phased deployment plan (Phase 1)

### Core documentation
- **[Setup Instructions](SETUP_INSTRUCTIONS.md)** — legacy bare-metal setup guide
- **[Quick Start Guide](QUICK_START.md)** — legacy quick start
- **[Security Guide](SECURITY.md)** — security best practices
- **[Testing Guide](TESTING.md)** — testing documentation
- **[Master Reference](MASTER_REFERENCE.md)** — complete reference guide

### Planning & architecture
- **[Master PRD](docs/MASTER_PRD.md)** — product requirements
- **[Executive Summary](docs/01_EXECUTIVE_SUMMARY.md)** — project overview
- **[Compliance Requirements](docs/02_COMPLIANCE_REQUIREMENTS.md)** — SEBI compliance
- **[Technical Architecture](docs/03_TECHNICAL_ARCHITECTURE.md)** — system design
- **[Feature Specifications](docs/04_FEATURE_SPECIFICATIONS.md)** — detailed features
- **[Data Management](docs/05_DATA_MANAGEMENT.md)** — data handling
- **[Risk Management](docs/06_RISK_MANAGEMENT.md)** — risk controls
- **[Technical Analysis](docs/09_TECHNICAL_ANALYSIS.md)** — technical indicators guide
- **[Fundamentals](docs/10_FUNDAMENTALS.md)** — fundamental data guide
- **[Implementation Plan](docs/07_IMPLEMENTATION_PLAN.md)** — development roadmap
- **[Testing Strategy](docs/08_TESTING_STRATEGY.md)** — QA approach

---

## 🔧 Features Implemented

### ✅ Phase 1 - Foundation (Complete)
- [x] FastAPI backend with async support
- [x] PostgreSQL/SQLite database
- [x] Zerodha OAuth integration
- [x] Encrypted token storage
- [x] Multi-user session management
- [x] SSL/HTTPS setup
- [x] Health monitoring endpoints

### ✅ Phase 2 - Token Management & Audit (Complete)
- [x] Automatic token refresh (15-min intervals)
- [x] Background scheduler service
- [x] Comprehensive audit logging
- [x] System event tracking
- [x] SEBI-compliant audit trail
- [x] Audit log query APIs

### ✅ Phase 3 - Risk Controls (Complete)
- [x] Position limits enforcement
- [x] Daily loss tracking
- [x] Kill switch mechanism
- [x] Pre-trade risk checks
- [x] Risk metrics and monitoring
- [x] Risk breach logging

### ✅ Phase 4 - Technical Analysis (Complete)
- [x] 60+ technical indicators (RSI, MACD, Bollinger Bands, etc.)
- [x] Momentum indicators (14 types)
- [x] Volume indicators (9 types)
- [x] Volatility indicators (5 types)
- [x] Trend indicators (15 types)
- [x] Runtime computation API
- [x] Customizable parameters

### ✅ Phase 5 - Fundamental Data (Complete)
- [x] Yahoo Finance integration
- [x] Fundamental ratios and metrics
- [x] Analyst recommendations and estimates
- [x] Symbol mapping (Zerodha ↔ Yahoo Finance)
- [x] Caching and rate limiting
- [x] Bulk data fetching

### ✅ Phase 6 - Pi Deployment (Complete as of 2026-04-15)
- [x] `docker-compose.prod.yml` — backend + frontend, arm64 pinned, log rotation, named volumes for SQLite data + logs
- [x] Three systemd units — migrate oneshot, main stack, tailscale-serve oneshot
- [x] Idempotent `setup-pi.sh` installer with template substitution
- [x] `td-sudo` scoped-NOPASSWD toggle system
- [x] Zerodha OAuth handshake end-to-end (including session-claim fix)
- [x] HTTPS via Tailscale Serve (Let's Encrypt on `*.ts.net`)
- [x] SQLite WAL mode + pragmas enforced at engine level

### 🚧 Phase 7 - Multi-broker data plumbing (In Progress)
- [ ] IndStocks/IndMoney broker adapter (BaseBroker impl + auth flow)
- [ ] Multi-broker `portfolio_snapshots` pipeline with APScheduler
- [ ] NSE market calendar (`config/nse_holidays.yaml`)
- [ ] Broker-agnostic `/portfolio/{holdings,positions,margins}` aggregated endpoints
- [ ] `/portfolio/history` + `/portfolio/metrics` (alpha/beta/Sharpe/Sortino/VaR/drawdown) + `/portfolio/sectors`
- [ ] SQLite backup/restore drill cron (Stage 5)
- [ ] Backend API surface audit doc

### 📋 Phase 8 - Trading Engine (Planned)
- [ ] Paper trading engine
- [ ] Strategy SDK
- [ ] Order placement APIs
- [ ] Backtest engine

### 🎨 Phase 9 - Frontend rebuild (Planned)
- [ ] Tailwind design system port from `tradedesk-designs/` (The Financial Atelier)
- [ ] New navigation shell (top / side / mobile bottom nav)
- [ ] Portfolio Insights bento-grid page (replaces current dashboard + portfolio)
- [ ] Analysis Lab page (Monte Carlo / Mean Variance / Black-Litterman — Phase 10+)
- [ ] Paper Trading page
- [ ] Settings + Risk rework with edit mutations

---

## 🏗️ Repo layout

```
trade-desk/
├── backend/                       # FastAPI backend
│   ├── app/
│   │   ├── api/v1/                # HTTP routes (auth, portfolio, risk, audit, ...)
│   │   ├── brokers/               # BaseBroker + per-broker adapters (zerodha, indstocks)
│   │   ├── models/                # SQLAlchemy ORM models
│   │   ├── services/              # Long-lived singletons (zerodha, indstocks, audit, token-refresh, snapshot-scheduler)
│   │   ├── utils/                 # Pure helpers (crypto, market_calendar, portfolio_metrics, sector_map)
│   │   └── config.py              # Pydantic settings loader
│   ├── alembic/versions/          # DB migrations
│   ├── config/                    # nse_holidays.yaml, sector_map.yaml
│   ├── scripts/                   # create_default_user.py, one-off admin scripts
│   └── tests/                     # pytest suite
├── frontend/                      # Next.js 15 (standalone output for Docker)
│   ├── app/                       # App Router pages
│   ├── components/                # UI primitives + layouts
│   ├── lib/                       # api.ts axios client, hooks
│   └── public/                    # static assets
├── deployment/
│   ├── docker/
│   │   ├── docker-compose.prod.yml           # Pi production stack
│   │   ├── Dockerfile.backend                # arm64, uvicorn --workers 1
│   │   └── Dockerfile.frontend               # Next.js standalone
│   ├── systemd/*.service.template            # trade-desk-migrate, trade-desk, trade-desk-tailscale-serve
│   ├── scripts/
│   │   ├── setup-pi.sh                       # idempotent unit installer
│   │   ├── td-sudo-on, td-sudo-off           # scoped NOPASSWD toggle
│   │   └── td-sudo-install.sh                # installs the above to /usr/local/bin + /etc/trade-desk/sudoers
│   └── sudoers/trade-desk                    # sudoers template (not live until td-sudo-on)
├── tradedesk-designs/             # Future-frontend design mockups + design system spec
├── docs/
│   ├── DEPLOYMENT.md              # authoritative Pi runbook
│   ├── plans/                     # phased plans + handoff state
│   └── 0[1-9]_*.md                # PRD, architecture, compliance, features, ...
└── tests/                         # integration tests
```

---

## 🔐 Security

- **Encrypted token storage** using Fernet encryption
- **SSL/HTTPS** for all communications
- **Environment-based secrets** management
- **IP whitelisting** for API access
- **Audit logging** for all operations
- **2FA support** (planned)

---

## 📊 API Endpoints

### Authentication
- `GET /api/v1/auth/zerodha/connect` - Initiate OAuth
- `GET /api/v1/auth/zerodha/callback` - OAuth callback
- `GET /api/v1/auth/zerodha/session` - Get session details
- `POST /api/v1/auth/zerodha/refresh` - Manual token refresh
- `GET /api/v1/auth/zerodha/refresh/status` - Refresh service status

### Audit & Compliance
- `GET /api/v1/audit/logs` - Query audit logs
- `GET /api/v1/audit/logs/{id}` - Get specific audit log
- `GET /api/v1/system/events` - Query system events
- `GET /api/v1/system/events/{id}` - Get specific system event

### Health & Monitoring
- `GET /health` - Health check
- `GET /api/v1/health/status` - Detailed health status
- `GET /api/v1/health/compliance` - Compliance status

### Technical Analysis
- `GET /api/v1/technical-analysis/indicators/list` - List all available indicators
- `POST /api/v1/technical-analysis/compute` - Compute technical indicators

### Fundamentals
- `GET /api/v1/fundamentals/{instrument_token}` - Get fundamental ratios
- `GET /api/v1/fundamentals/{instrument_token}/analyst` - Get analyst data
- `POST /api/v1/fundamentals/fetch` - Force fetch fresh data
- `POST /api/v1/fundamentals/mapping/sync` - Sync symbol mappings

### Risk Management
- `GET /api/v1/risk/config` - Get risk configuration
- `PUT /api/v1/risk/config` - Update risk limits
- `POST /api/v1/risk/kill-switch` - Toggle kill switch
- `GET /api/v1/risk/status` - Get comprehensive risk status
- `POST /api/v1/risk/pre-trade-check` - Validate order against risk limits

### Data Management
- `GET /api/v1/data/zerodha/profile` - Get Zerodha profile
- `GET /api/v1/data/zerodha/margins` - Get account margins
- `GET /api/v1/data/zerodha/positions` - Get current positions
- `POST /api/v1/data/zerodha/data/historical/fetch` - Fetch and store historical data

---

## 🧪 Testing

### Environment Setup
All test scripts require environment variables. See [TESTING.md](TESTING.md) for complete guide.

```bash
# Set up test environment
export TEST_USERNAME=testuser
export TEST_PASSWORD=testpass123
export USER_IDENTIFIER=your_user_id
export API_BASE_URL=http://localhost:8000

# Or use TEST_ENV file
cp TEST_ENV.example TEST_ENV
# Edit TEST_ENV with your credentials
source TEST_ENV
```

### Manual Testing
- See [TESTING.md](TESTING.md) for complete testing documentation
- Use Swagger UI at `/docs` for interactive API testing
- All endpoints require JWT authentication (except public endpoints)

---

## 🔄 Token Auto-Refresh

The platform automatically refreshes Zerodha access tokens before expiry:

- **Interval:** Every 15 minutes
- **Buffer:** Refreshes tokens expiring within 60 minutes
- **Zerodha expiry:** Daily at 6 AM IST
- **Status:** Check via `/api/v1/auth/zerodha/refresh/status`

---

## 📝 Audit Logging

All critical operations are logged for SEBI compliance:

- **OAuth operations** (initiate, success, failure)
- **Token refresh** (manual and automatic)
- **System events** (startup, shutdown, errors)
- **User actions** (with IP and user agent)
- **7-year retention** ready
- **Immutable records** (insert-only)

---

## 🛠️ Configuration

Key environment variables:

```bash
# Application
APP_NAME=TradeDesk
APP_ENV=production
DEBUG=false

# Database
DATABASE_URL=sqlite+aiosqlite:///./tradedesk.db

# Zerodha
ZERODHA_API_KEY=your_api_key
ZERODHA_API_SECRET=your_api_secret
ZERODHA_REDIRECT_URL=https://yourdomain.com/api/v1/auth/zerodha/callback
ZERODHA_AUTO_REFRESH_ENABLED=true
ZERODHA_REFRESH_INTERVAL_MINUTES=15
ZERODHA_REFRESH_EXPIRY_BUFFER_MINUTES=60

# Security
SECRET_KEY=your_secret_key
ENCRYPTION_KEY=your_encryption_key
JWT_SECRET_KEY=your_jwt_secret
```

---

## 📈 Roadmap

### Q4 2025 ✅ (Complete)
- [x] Foundation & OAuth integration
- [x] Token management + audit logging (SEBI-compliant, 7-year retention ready)
- [x] Risk controls (position/loss limits, kill switch)
- [x] Technical Analysis (60+ indicators)
- [x] Fundamental Data (Yahoo Finance integration)

### Q1 2026 ✅ (Complete)
- [x] Raspberry Pi 4B deployment (Docker + systemd + Tailscale)
- [x] Zerodha OAuth end-to-end (including session-claim flow)
- [x] Scoped `td-sudo` toggle system for safe systemctl access
- [x] Tailscale Serve TLS + path routing

### Q2 2026 (In Progress — Phase B)
- [ ] IndStocks/IndMoney broker adapter + auth flow
- [ ] Multi-broker portfolio snapshot pipeline (15-min cron, market-calendar-aware)
- [ ] Portfolio history + metrics + sectors APIs (aggregated across brokers)
- [ ] SQLite backup/restore drill
- [ ] Backend API surface doc

### Q3 2026 (Planned — Phase F)
- [ ] Frontend rebuild against "The Financial Atelier" design system (`tradedesk-designs/`)
- [ ] New IA: Portfolio Insights / Analysis Lab / Paper Trading
- [ ] Mobile-responsive layouts

### Later
- [ ] Paper trading engine + Strategy SDK
- [ ] Analysis Lab algorithmic backends (Monte Carlo, Mean Variance, Black-Litterman)
- [ ] Order placement APIs (live trading)
- [ ] Prometheus + Grafana metrics

---

## 🤝 Contributing

This is a personal project. For collaboration inquiries, please contact the repository owner.

---

## 📄 License

Private - All Rights Reserved

---

## 📞 Support

For issues or questions:
- Check [Documentation](docs/)
- Review [Testing Guide](TESTING.md)
- See [Setup Instructions](SETUP_INSTRUCTIONS.md)
- Review [Security Guide](SECURITY.md) for best practices

---

## 🙏 Acknowledgments

- **Zerodha Kite Connect** - Broker API
- **FastAPI** - Web framework
- **SQLAlchemy** - ORM
- **Alembic** - Database migrations
- **yfinance** - Fundamental data source
- **ta** - Technical analysis library
- **pandas** - Data manipulation

