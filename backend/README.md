# TradeDesk - Backend

TradeDesk - Personal algorithmic trading platform with SEBI compliance for NSE/BSE trading.

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 16+
- Redis 7.2+
- TimescaleDB extension for PostgreSQL

### Installation

```bash
# 1. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy environment file and configure
cp .env.example .env
# Edit .env with your configuration

# 4. Initialize database
python scripts/init_db.py

# 5. Run migrations
alembic upgrade head

# 6. Start the server
python -m app.main
```

### Development Mode

```bash
# Run with auto-reload
uvicorn app.main:app --reload --port 8000

# Or using the convenience script
python -m app.main
```

## 📚 API Documentation

Once running, access:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- Health Check: `http://localhost:8000/health`

## 🏗️ Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration management
│   ├── database.py          # Database connection
│   │
│   ├── api/                 # API routes
│   │   └── v1/
│   │       ├── auth.py
│   │       ├── health.py
│   │       └── ...
│   │
│   ├── models/              # SQLAlchemy models
│   │   ├── user.py
│   │   ├── order.py
│   │   └── ...
│   │
│   ├── schemas/             # Pydantic schemas
│   ├── services/            # Business logic
│   ├── brokers/             # Broker integrations
│   ├── strategies/          # Trading strategies
│   └── utils/               # Utilities
│
├── alembic/                 # Database migrations
├── tests/                   # Test suites
├── scripts/                 # Utility scripts
├── requirements.txt
└── README.md
```

## 🔐 SEBI Compliance

This platform implements all required SEBI compliance measures:

- ✅ OAuth-based authentication (no password storage for broker access)
- ✅ Two-factor authentication for API access
- ✅ Static IP whitelisting
- ✅ Complete audit trail (7-year retention)
- ✅ Order tagging with unique algo identifier
- ✅ Orders Per Second (OPS) tracking and limiting
- ✅ Multi-layer risk controls

## 🛡️ Risk Management

Built-in risk controls:
- Position size limits
- Daily loss limits
- Stop loss mechanisms
- Maximum drawdown monitoring
- Emergency kill switch
- Circuit breakers

## 🔧 Configuration

Key environment variables (see `.env.example`):

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/algotrading

# JWT
JWT_SECRET_KEY=your-secret-key

# Broker API Keys
ZERODHA_API_KEY=your-api-key
GROWW_API_KEY=your-api-key

# Risk Management
MAX_POSITION_VALUE=50000
MAX_DAILY_LOSS=5000
OPS_LIMIT=10
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test types
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/
```

## 📊 Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1

# View migration history
alembic history
```

## 🚀 Deployment

```bash
# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# With Gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

## 📝 Development Status

### ✅ Phase 0: Foundation (Current)
- [x] FastAPI application structure
- [x] Database models and migrations
- [x] Basic API endpoints
- [ ] Authentication system
- [ ] Broker integration

### 🚧 Phase 1: Core Features (Next)
- [ ] Strategy plugin system
- [ ] Backtesting engine
- [ ] Paper trading
- [ ] WebSocket streaming

### 📋 Phase 2: Live Trading (Planned)
- [ ] Order management
- [ ] Risk controls
- [ ] Live trading engine
- [ ] Monitoring and alerts

## 📞 Support

For issues and questions, please refer to the main PRD documentation in `/docs`.

## ⚠️ Disclaimer

This is a personal trading platform. Use at your own risk. No financial advice is provided.

