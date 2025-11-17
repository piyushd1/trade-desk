# TradeDesk - Personal Algo Trading Platform

**SEBI-Compliant Algorithmic Trading Platform**

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-Private-red.svg)]()

---

## 🎯 Overview

TradeDesk is a personal algorithmic trading platform designed for SEBI compliance, featuring:

- **Multi-broker support** (Zerodha, Groww)
- **Automated token management** with refresh
- **SEBI-compliant audit logging** (7-year retention)
- **Risk management** controls
- **Strategy SDK** for custom algorithms
- **Paper trading** engine
- **Real-time monitoring** and alerts

---

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- PostgreSQL/SQLite
- Zerodha Kite Connect API credentials
- SSL certificate (Let's Encrypt)

### Installation

```bash
# Clone repository
git clone https://github.com/piyushd1/trade-desk.git
cd trade-desk

# Setup backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Production Deployment

```bash
# Start backend (production)
cd /home/trade-desk/backend
source venv/bin/activate
nohup python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 > /tmp/backend.log 2>&1 &
echo $! > /tmp/backend.pid
```

---

## 📚 Documentation

### Core Documentation
- **[Setup Instructions](SETUP_INSTRUCTIONS.md)** - Complete setup guide
- **[Quick Start Guide](QUICK_START.md)** - Quick start guide
- **[Security Guide](SECURITY.md)** - Security best practices
- **[Testing Guide](TESTING.md)** - Testing documentation
- **[Master Reference](MASTER_REFERENCE.md)** - Complete reference guide

### Planning & Architecture
- **[Master PRD](docs/MASTER_PRD.md)** - Product requirements
- **[Executive Summary](docs/01_EXECUTIVE_SUMMARY.md)** - Project overview
- **[Compliance Requirements](docs/02_COMPLIANCE_REQUIREMENTS.md)** - SEBI compliance
- **[Technical Architecture](docs/03_TECHNICAL_ARCHITECTURE.md)** - System design
- **[Feature Specifications](docs/04_FEATURE_SPECIFICATIONS.md)** - Detailed features
- **[Data Management](docs/05_DATA_MANAGEMENT.md)** - Data handling
- **[Risk Management](docs/06_RISK_MANAGEMENT.md)** - Risk controls
- **[Technical Analysis](docs/09_TECHNICAL_ANALYSIS.md)** - Technical indicators guide
- **[Fundamentals](docs/10_FUNDAMENTALS.md)** - Fundamental data guide
- **[Implementation Plan](docs/07_IMPLEMENTATION_PLAN.md)** - Development roadmap
- **[Testing Strategy](docs/08_TESTING_STRATEGY.md)** - QA approach

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

### 📋 Phase 6 - Trading Engine (Planned)
- [ ] Paper trading engine
- [ ] Strategy SDK
- [ ] Order placement APIs
- [ ] Backtest engine

### 🎨 Phase 7 - Frontend (Planned)
- [ ] Dashboard UI
- [ ] Strategy management
- [ ] Real-time monitoring
- [ ] Audit log viewer

---

## 🏗️ Architecture

```
trade-desk/
├── backend/               # FastAPI backend
│   ├── app/
│   │   ├── api/          # API endpoints
│   │   ├── models/       # Database models
│   │   ├── services/     # Business logic
│   │   ├── brokers/      # Broker integrations
│   │   └── utils/        # Utilities
│   ├── alembic/          # Database migrations
│   └── tests/            # Test suite
├── docs/                 # Documentation
├── scripts/              # Utility scripts
└── tests/                # Integration tests
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
- [x] Token auto-refresh
- [x] Audit logging
- [x] Risk controls
- [x] Technical Analysis (60+ indicators)
- [x] Fundamental Data (Yahoo Finance integration)

### Q1 2026 (In Progress)
- [ ] Paper trading engine
- [ ] Strategy SDK
- [ ] Order placement APIs
- [ ] Backtest engine
- [ ] Frontend dashboard

### Q2 2026 (Planned)
- [ ] Groww integration
- [ ] Advanced risk management
- [ ] Real-time alerts
- [ ] Mobile app

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

---

**Built with ❤️ for algorithmic trading**

