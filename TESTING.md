# Testing Documentation

## Overview

This document explains how to set up and run tests for the TradeDesk application.

## Prerequisites

1. Backend server running (locally or remote)
2. Test user account created
3. Environment variables configured

## Environment Setup

### Option 1: Using TEST_ENV File

```bash
# 1. Copy the example file
cp TEST_ENV.example TEST_ENV

# 2. Edit TEST_ENV with your credentials
nano TEST_ENV

# 3. Source the file
source TEST_ENV
```

### Option 2: Export Manually

```bash
export TEST_USERNAME=testuser
export TEST_PASSWORD=testpass123
export USER_IDENTIFIER=your_user_identifier
export API_BASE_URL=http://localhost:8000
```

## Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `TEST_USERNAME` | Platform username | `testuser` |
| `TEST_PASSWORD` | Platform password | `testpass123` |
| `USER_IDENTIFIER` | Zerodha user identifier | `your_user_id` |
| `API_BASE_URL` | API base URL | `http://localhost:8000` |

## Running Tests

### Individual Test Scripts

```bash
# Test fundamentals API
./tests/scripts/test_fundamentals_apis.sh

# Test technical analysis API
./tests/scripts/test_technical_analysis_apis.sh

# Test internal authentication
./tests/scripts/test_internal_auth.sh

# Test market data APIs
./tests/scripts/test_market_data_apis.sh

# Test data management APIs
./tests/scripts/test_data_management_apis.sh

# Test risk management APIs
./tests/scripts/test_risk_management_apis.sh

# Test streaming APIs
./tests/scripts/test_streaming_apis.sh
```

### Quick Test Suite

```bash
# Run quick test suite (requires USER_IDENTIFIER)
export USER_IDENTIFIER=your_user_id
./tests/scripts/QUICK_TEST.sh
```

## Test Output

Test scripts generate markdown files with timestamps:
- `fundamentals_test_YYYYMMDD_HHMMSS.md`
- `technical_analysis_test_YYYYMMDD_HHMMSS.md`
- etc.

These files are automatically gitignored.

## Python Scripts

### Fetch Nifty 50 Data

```bash
# Using environment variables
export TEST_USERNAME=testuser
export TEST_PASSWORD=testpass123
export USER_IDENTIFIER=your_user_id
export API_BASE_URL=http://localhost:8000

python scripts/fetch_nifty50_data.py --days 200

# Or with command-line arguments
python scripts/fetch_nifty50_data.py \
  --user-identifier YOUR_ID \
  --username testuser \
  --password testpass123 \
  --days 200
```

## Creating Test Users

```bash
# Make sure API_BASE_URL is set
export API_BASE_URL=http://localhost:8000

# Run the script
./scripts/utilities/create_test_users.sh
```

This creates:
- Admin user: `admin` / `admin123`
- Test user: `testuser` / `testpass123`

## Zerodha Re-authentication

```bash
# Set required environment variables
export TEST_USERNAME=testuser
export TEST_PASSWORD=testpass123
export USER_IDENTIFIER=your_user_id
export API_BASE_URL=http://localhost:8000

# Run the helper script
./scripts/utilities/zerodha_reauth.sh
```

## Troubleshooting

### "Environment variable not set" Error

Ensure all required environment variables are exported:

```bash
source TEST_ENV
# Or
export TEST_USERNAME=testuser
export TEST_PASSWORD=testpass123
export USER_IDENTIFIER=your_user_id
```

### "401 Unauthorized" Error

Your credentials may be incorrect or the user doesn't exist. Create a test user:

```bash
./scripts/utilities/create_test_users.sh
```

### "Connection refused" Error

The backend server may not be running. Start it:

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### "No active Zerodha session" Error

You need to authenticate with Zerodha first:

1. Visit: `http://localhost:8000/api/v1/auth/zerodha/connect?state=your_user_id`
2. Log in to Zerodha and authorize
3. Run your test script again

## Best Practices

1. **Never commit test credentials** to git
2. **Use placeholders** in documentation
3. **Use environment variables** for all secrets
4. **Run tests locally** before pushing
5. **Review test output** for sensitive data before sharing

## Python Unit Tests (pytest)

The backend has pytest-based unit tests in `backend/tests/`.

### Required environment variables

The backend needs a minimum set of environment variables to start. Use the provided template:

```bash
cd backend
cp .env.test.example .env.test
```

### Running unit tests

```bash
cd backend

# Using the .env.test file (export vars then run)
env $(grep -v '^#' .env.test | xargs) python -m pytest tests/unit/ -v --no-cov

# Or export the minimum required vars inline:
SECRET_KEY=test-secret \
  JWT_SECRET_KEY=test-jwt-secret \
  DATABASE_URL=sqlite+aiosqlite:///:memory: \
  ENCRYPTION_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())") \
  python -m pytest tests/unit/ -v --no-cov
```

### What the unit tests cover

| Test file | Coverage |
|-----------|----------|
| `tests/unit/test_config.py` | Settings loading, validation, environment detection |
| `tests/unit/test_database.py` | Database engine, connection check, Base metadata |

### Known test requirements

- **REDIS_URL, CELERY_BROKER_URL, CELERY_RESULT_BACKEND**: These now have defaults and do not need to be set for tests.
- **STATIC_IP**: Defaults to `0.0.0.0` for SEBI compliance display; does not need to be set for tests.
- **SECRET_KEY, JWT_SECRET_KEY, ENCRYPTION_KEY, DATABASE_URL**: These are still required (they are security-critical and must be set explicitly).

## Additional Resources

- [Security Best Practices](SECURITY.md)
- [Quick Start Guide](QUICK_START.md)
- [Setup Instructions](SETUP_INSTRUCTIONS.md)

