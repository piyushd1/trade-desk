# TradeDesk Backend

SEBI-compliant algorithmic trading platform backend built with FastAPI, PostgreSQL, and modern Python.

## 🏗️ Architecture

- **Framework**: FastAPI (async Python web framework)
- **Database**: PostgreSQL with TimescaleDB extension
- **ORM**: SQLAlchemy 2.0 with async support
- **Authentication**: JWT tokens with refresh mechanism
- **Task Queue**: Celery with Redis
- **API Documentation**: Automatic OpenAPI/Swagger

## 📁 Project Structure

```
backend/
├── app/                      # Main application code
│   ├── api/                  # API endpoints
│   │   └── v1/              # API version 1
│   │       ├── auth.py      # Authentication endpoints
│   │       ├── risk.py      # Risk management endpoints
│   │       ├── audit.py     # Audit log endpoints
│   │       └── ...
│   ├── models/              # Database models
│   │   ├── user.py          # User model
│   │   ├── order.py         # Order model
│   │   ├── position.py      # Position model
│   │   └── ...
│   ├── services/            # Business logic services
│   │   ├── auth_service.py  # Authentication service
│   │   ├── risk_manager.py  # Risk management service
│   │   └── ...
│   ├── config.py            # Configuration management
│   ├── database.py          # Database setup
│   └── main.py              # Application entry point
├── alembic/                 # Database migrations
├── tests/                   # Test suite
│   ├── unit/               # Unit tests
│   ├── integration/        # Integration tests
│   └── conftest.py         # Test configuration
├── scripts/                 # Utility scripts
├── requirements.txt         # Python dependencies
├── pyproject.toml          # Project configuration
└── .env.example            # Environment variables example
```

## 🚀 Setup

### Prerequisites

- Python 3.10+
- PostgreSQL 14+
- Redis 6+
- Virtual environment tool (venv, virtualenv, etc.)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd trade-desk/backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Initialize database**
   ```bash
   # Run migrations
   alembic upgrade head
   
   # Or initialize directly (development only)
   python scripts/init_db.py
   ```

6. **Run the application**
   ```bash
   # Development
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   
   # Production
   gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
   ```

## 🧪 Testing

### Run all tests
```bash
pytest
```

### Run with coverage
```bash
pytest --cov=app --cov-report=html
```

### Run specific test types
```bash
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m "not slow"    # Skip slow tests
```

## 🔧 Development

### Code Quality

We use several tools to maintain code quality:

- **Black**: Code formatting
  ```bash
  black app/ tests/
  ```

- **Ruff**: Fast linting
  ```bash
  ruff check app/ tests/
  ruff check --fix app/ tests/  # Auto-fix issues
  ```

- **MyPy**: Type checking
  ```bash
  mypy app/
  ```

### Pre-commit Hooks

Install pre-commit hooks to run checks automatically:
```bash
pre-commit install
pre-commit run --all-files  # Run on all files
```

### Database Migrations

Create a new migration:
```bash
alembic revision --autogenerate -m "Description of change"
```

Apply migrations:
```bash
alembic upgrade head
```

Rollback migration:
```bash
alembic downgrade -1
```

## 📡 API Documentation

When running in development mode, API documentation is available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

## 🔒 Security

- All sensitive data is encrypted using Fernet encryption
- JWT tokens for authentication with automatic refresh
- Rate limiting on API endpoints
- CORS configuration for frontend integration
- Request validation using Pydantic models
- SQL injection protection via SQLAlchemy ORM

## 📊 Monitoring

- Health check endpoint: `/health`
- Prometheus metrics: Port 9090 (when configured)
- Structured logging with correlation IDs
- Audit trail for all operations

## 🚦 Environment Variables

Key environment variables (see `.env.example` for full list):

```bash
# Application
APP_NAME=TradeDesk
APP_ENV=development
SECRET_KEY=your-secret-key

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/dbname

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
JWT_SECRET_KEY=your-jwt-secret
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Encryption
ENCRYPTION_KEY=your-fernet-key

# SEBI Compliance
STATIC_IP=your-static-ip
MAX_DAILY_TRADES=50
```

## 🤝 Contributing

1. Create a feature branch
2. Make your changes
3. Run tests and linting
4. Submit a pull request

## 📄 License

Proprietary - See LICENSE file for details