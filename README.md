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
- **[Zerodha Testing Guide](ZERODHA_TESTING_GUIDE.md)** - OAuth flow and API testing
- **[Day 1 Work Summary](day_1_work.md)** - Initial implementation details
- **[Testing Results](TESTING_RESULTS.md)** - Latest test results

### Planning & Architecture
- **[Master PRD](docs/MASTER_PRD.md)** - Product requirements
- **[Executive Summary](docs/01_EXECUTIVE_SUMMARY.md)** - Project overview
- **[Compliance Requirements](docs/02_COMPLIANCE_REQUIREMENTS.md)** - SEBI compliance
- **[Technical Architecture](docs/03_TECHNICAL_ARCHITECTURE.md)** - System design
- **[Feature Specifications](docs/04_FEATURE_SPECIFICATIONS.md)** - Detailed features
- **[Data Management](docs/05_DATA_MANAGEMENT.md)** - Data handling
- **[Risk Management](docs/06_RISK_MANAGEMENT.md)** - Risk controls
- **[Implementation Plan](docs/07_IMPLEMENTATION_PLAN.md)** - Development roadmap
- **[Testing Strategy](docs/08_TESTING_STRATEGY.md)** - QA approach

### Infrastructure
- **[GCP Firewall Setup](GCP_FIREWALL_SETUP.md)** - Network configuration
- **[SSL Setup](SSL_SETUP_COMPLETE.md)** - HTTPS configuration

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

### 🚧 Phase 3 - Risk Controls (In Progress)
- [ ] Position limits enforcement
- [ ] Daily loss tracking
- [ ] Kill switch mechanism
- [ ] Pre-trade risk checks

### 📋 Phase 4 - Trading Engine (Planned)
- [ ] Paper trading engine
- [ ] Strategy SDK
- [ ] Order placement APIs
- [ ] Backtest engine

### 🎨 Phase 5 - Frontend (Planned)
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

### Testing (Dev Only)
- `GET /api/v1/test/zerodha/profile` - Test profile fetch
- `GET /api/v1/test/zerodha/margins` - Test margins fetch
- `GET /api/v1/test/zerodha/positions` - Test positions fetch
- `GET /api/v1/test/zerodha/holdings` - Test holdings fetch

---

## 🧪 Testing

### Automated Tests
```bash
# Run audit logging tests
./test_audit_logging.sh

# Run OAuth flow tests
./test_oauth_flow.sh
```

### Manual Testing
See [Zerodha Testing Guide](ZERODHA_TESTING_GUIDE.md) for detailed testing procedures.

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

### Q4 2025
- [x] Foundation & OAuth integration
- [x] Token auto-refresh
- [x] Audit logging
- [ ] Risk controls
- [ ] Paper trading engine

### Q1 2026
- [ ] Strategy SDK
- [ ] Order placement
- [ ] Frontend dashboard
- [ ] Backtest engine

### Q2 2026
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
- Review [Testing Guide](ZERODHA_TESTING_GUIDE.md)
- See [Setup Instructions](SETUP_INSTRUCTIONS.md)

---

## 🙏 Acknowledgments

- **Zerodha Kite Connect** - Broker API
- **FastAPI** - Web framework
- **SQLAlchemy** - ORM
- **Alembic** - Database migrations

---

**Built with ❤️ for algorithmic trading**

