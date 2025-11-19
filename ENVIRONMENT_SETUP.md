# TradeDesk Environment Configuration Guide

This guide explains how to configure environment variables for TradeDesk to ensure secure deployment and protect sensitive credentials.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Environment Variables Reference](#environment-variables-reference)
3. [Security Best Practices](#security-best-practices)
4. [Configuration for Different Environments](#configuration-for-different-environments)
5. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Automated Setup (Recommended)

The easiest way to set up your environment is using the automated setup script:

```bash
# Run the setup script
python scripts/setup_env.py
```

This script will:
- Copy `.env.example` to `.env` files
- Generate secure cryptographic keys automatically
- Prompt you for essential configuration values
- Validate your inputs

### Manual Setup

If you prefer manual configuration:

1. **Backend Configuration**:
   ```bash
   cd backend
   cp .env.example .env
   # Edit .env with your favorite editor
   nano .env  # or vim, code, etc.
   ```

2. **Frontend Configuration**:
   ```bash
   cd frontend
   cp .env.local.example .env.local
   # Edit .env.local with your favorite editor
   nano .env.local
   ```

3. **Generate Required Keys**:
   ```bash
   # Generate SECRET_KEY and JWT_SECRET_KEY
   python -c "import secrets; print(secrets.token_urlsafe(64))"

   # Generate ENCRYPTION_KEY (Fernet key)
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```

---

## Environment Variables Reference

### Backend Configuration (`backend/.env`)

#### Required Variables

These variables **must** be set for the application to run:

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | Application secret for session management | Generated 64-char string |
| `JWT_SECRET_KEY` | Secret key for signing JWT tokens | Generated 64-char string |
| `ENCRYPTION_KEY` | Fernet key for encrypting sensitive data | Generated Fernet key |
| `DATABASE_URL` | Database connection string | `sqlite+aiosqlite:///./tradedesk.db` |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379/0` |
| `CELERY_BROKER_URL` | Celery message broker URL | `redis://localhost:6379/1` |
| `CELERY_RESULT_BACKEND` | Celery result backend URL | `redis://localhost:6379/2` |
| `STATIC_IP` | Your static IP for SEBI compliance | `123.45.67.89` |

#### Application Settings

| Variable | Description | Default | Production Example |
|----------|-------------|---------|-------------------|
| `APP_NAME` | Application name | `TradeDesk` | `TradeDesk` |
| `APP_ENV` | Environment type | `development` | `production` |
| `DEBUG` | Enable debug mode | `True` | `False` |
| `APP_DOMAIN` | Your domain name | `example.com` | `yourdomain.com` |
| `APP_URL` | Full application URL | `http://localhost:8000` | `https://yourdomain.com` |
| `API_BASE_URL` | Backend API URL | `http://localhost:8000` | `https://yourdomain.com/api` |
| `FRONTEND_URL` | Frontend URL | `http://localhost:3000` | `https://yourdomain.com` |

#### Broker Integration

| Variable | Description | Required | Example |
|----------|-------------|----------|---------|
| `ZERODHA_API_KEY` | Zerodha API key | Optional | `your_api_key` |
| `ZERODHA_API_SECRET` | Zerodha API secret | Optional | `your_api_secret` |
| `ZERODHA_REDIRECT_URL` | OAuth redirect URL | Optional | `https://yourdomain.com/api/v1/auth/zerodha/callback` |
| `ZERODHA_USER_IDENTIFIER` | Default Zerodha user ID | Optional | `YOUR_USER_ID` |
| `GROWW_API_KEY` | Groww API key | Optional | `your_api_key` |
| `GROWW_API_SECRET` | Groww API secret | Optional | `your_api_secret` |
| `GROWW_TOTP_SECRET` | Groww TOTP secret | Optional | `your_totp_secret` |

#### Admin User Configuration

Used during initial setup with `create_default_user.py`:

| Variable | Description | Required |
|----------|-------------|----------|
| `ADMIN_USERNAME` | Default admin username | No (prompts if not set) |
| `ADMIN_EMAIL` | Default admin email | No (prompts if not set) |
| `ADMIN_PASSWORD` | Default admin password | No (prompts if not set) |

#### Test Configuration

Used for testing only:

| Variable | Description | Default |
|----------|-------------|---------|
| `TEST_DATABASE_URL` | Test database URL | `sqlite+aiosqlite:///:memory:` |
| `TEST_USER_USERNAME` | Test user username | `testuser` |
| `TEST_USER_PASSWORD` | Test user password | `testpass123` |
| `TEST_ADMIN_USERNAME` | Test admin username | `admin` |
| `TEST_ADMIN_PASSWORD` | Test admin password | `admin123` |

### Frontend Configuration (`frontend/.env.local`)

| Variable | Description | Example |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API URL (must be public) | `/api/v1` (dev) or `https://yourdomain.com/api/v1` (prod) |

---

## Security Best Practices

### 1. Never Commit Secrets to Git

- ✅ `.env.example` files are safe to commit (contain placeholders)
- ❌ `.env` and `.env.local` files should **never** be committed
- The `.gitignore` file is configured to exclude all `.env` files

### 2. Use Strong, Unique Keys

```bash
# Generate strong keys
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

- **Never** reuse keys across environments
- **Never** use default or example keys in production
- **Never** share keys via email, Slack, or other insecure channels

### 3. Rotate Keys Regularly

- Rotate `SECRET_KEY` and `JWT_SECRET_KEY` every 90 days
- Rotate `ENCRYPTION_KEY` carefully (requires data re-encryption)
- Update broker API keys when they expire

### 4. Use Different Credentials Per Environment

| Environment | Database | Keys | Broker Credentials |
|-------------|----------|------|-------------------|
| **Development** | Local SQLite | Development keys | Test/sandbox keys |
| **Staging** | Staging DB | Staging keys | Test/sandbox keys |
| **Production** | Production DB | Production keys | Live credentials |

### 5. Secure Storage

**For Local Development:**
- Store `.env` files in the project directory (gitignored)
- Use restrictive file permissions: `chmod 600 .env`

**For Production:**
Consider using a secrets management service:
- **AWS Secrets Manager**
- **HashiCorp Vault**
- **Azure Key Vault**
- **Google Cloud Secret Manager**

### 6. SEBI Compliance

For SEBI compliance, ensure:
- `STATIC_IP` is set to your actual static IP address
- All API calls originate from this IP
- Audit logs are enabled and retained for 7 years

---

## Configuration for Different Environments

### Development Environment

```bash
# backend/.env (development)
APP_ENV=development
DEBUG=True
APP_DOMAIN=localhost
APP_URL=http://localhost:8000
API_BASE_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000

DATABASE_URL=sqlite+aiosqlite:///./tradedesk.db
REDIS_URL=redis://localhost:6379/0

# Use test/sandbox broker credentials
ZERODHA_API_KEY=your_test_api_key
ZERODHA_API_SECRET=your_test_api_secret
```

### Staging Environment

```bash
# backend/.env (staging)
APP_ENV=staging
DEBUG=False
APP_DOMAIN=staging.yourdomain.com
APP_URL=https://staging.yourdomain.com
API_BASE_URL=https://staging.yourdomain.com/api
FRONTEND_URL=https://staging.yourdomain.com

DATABASE_URL=postgresql+asyncpg://user:pass@staging-db:5432/tradedesk
REDIS_URL=redis://staging-redis:6379/0

# Use test/sandbox broker credentials
ZERODHA_API_KEY=your_test_api_key
ZERODHA_API_SECRET=your_test_api_secret
```

### Production Environment

```bash
# backend/.env (production)
APP_ENV=production
DEBUG=False
APP_DOMAIN=yourdomain.com
APP_URL=https://yourdomain.com
API_BASE_URL=https://yourdomain.com/api
FRONTEND_URL=https://yourdomain.com

DATABASE_URL=postgresql+asyncpg://user:pass@prod-db:5432/tradedesk
REDIS_URL=redis://prod-redis:6379/0

STATIC_IP=123.45.67.89  # Your actual static IP

# Use live broker credentials
ZERODHA_API_KEY=your_live_api_key
ZERODHA_API_SECRET=your_live_api_secret
ZERODHA_USER_IDENTIFIER=YOUR_USER_ID
```

---

## Database Configuration

### SQLite (Development)

```bash
DATABASE_URL=sqlite+aiosqlite:///./tradedesk.db
```

**Pros:**
- No setup required
- Easy to use for development
- Data stored in local file

**Cons:**
- Not suitable for production
- Limited concurrency support

### PostgreSQL (Production)

```bash
DATABASE_URL=postgresql+asyncpg://username:password@host:5432/database
```

**Example:**
```bash
DATABASE_URL=postgresql+asyncpg://tradedesk:SecurePass123!@localhost:5432/tradedesk_prod
```

**Setup PostgreSQL:**
```sql
-- Create database and user
CREATE USER tradedesk WITH PASSWORD 'SecurePass123!';
CREATE DATABASE tradedesk_prod OWNER tradedesk;
GRANT ALL PRIVILEGES ON DATABASE tradedesk_prod TO tradedesk;
```

---

## Nginx Configuration

The nginx configuration uses environment variables via a template system.

### Generate Nginx Config

```bash
# Set APP_DOMAIN in .env first, then run:
./scripts/deploy_nginx.sh
```

This will:
1. Read `APP_DOMAIN` from `backend/.env`
2. Generate `nginx.conf` from `nginx.conf.template`
3. Optionally install to `/etc/nginx/sites-available/`

### Manual Nginx Setup

If you prefer manual configuration:

```bash
# Replace ${APP_DOMAIN} with your domain
sed 's/${APP_DOMAIN}/yourdomain.com/g' nginx.conf.template > nginx.conf

# Install
sudo cp nginx.conf /etc/nginx/sites-available/trade-desk
sudo ln -s /etc/nginx/sites-available/trade-desk /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## First-Time Setup

After configuring environment variables:

### 1. Create Admin User

```bash
cd backend
python scripts/create_default_user.py
```

This will:
- Check for admin credentials in environment variables
- If not found, prompt you interactively
- Validate password strength
- Create the admin user in the database

### 2. Run Database Migrations

```bash
cd backend
alembic upgrade head
```

### 3. Start the Application

```bash
# Backend
cd backend
uvicorn app.main:app --reload

# Frontend (in another terminal)
cd frontend
npm run dev
```

---

## Troubleshooting

### "Config validation error" on startup

**Cause:** Required environment variables are missing

**Solution:**
1. Check that `.env` file exists in `backend/` directory
2. Ensure all required variables are set (see Required Variables section)
3. Run `python scripts/setup_env.py` to regenerate configuration

### "Invalid Fernet key" error

**Cause:** `ENCRYPTION_KEY` is not a valid Fernet key

**Solution:**
```bash
# Generate a new Fernet key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# Update ENCRYPTION_KEY in .env
```

### Database connection errors

**SQLite:**
```bash
# Ensure path is correct and writable
DATABASE_URL=sqlite+aiosqlite:///./tradedesk.db
```

**PostgreSQL:**
```bash
# Test connection
psql -h localhost -U tradedesk -d tradedesk_prod

# Check DATABASE_URL format
DATABASE_URL=postgresql+asyncpg://user:pass@host:port/database
```

### "Zerodha API authentication failed"

**Solution:**
1. Verify `ZERODHA_API_KEY` and `ZERODHA_API_SECRET` are correct
2. Check that `ZERODHA_REDIRECT_URL` matches your registered URL
3. Ensure you're using the correct credentials (test vs live)

### Nginx configuration not working

**Solution:**
```bash
# Test nginx configuration
sudo nginx -t

# Check logs
sudo tail -f /var/log/nginx/error.log

# Verify APP_DOMAIN is set
grep APP_DOMAIN backend/.env

# Regenerate configuration
./scripts/deploy_nginx.sh
```

---

## Additional Resources

- [SETUP_INSTRUCTIONS.md](./SETUP_INSTRUCTIONS.md) - Complete setup guide
- [MASTER_REFERENCE.md](./MASTER_REFERENCE.md) - Complete API reference
- [README.md](./README.md) - Project overview
- [Zerodha API Documentation](https://kite.trade/docs/connect/v3/)

---

## Need Help?

If you encounter issues not covered in this guide:

1. Check the [GitHub Issues](https://github.com/piyushd1/trade-desk/issues)
2. Review application logs: `tail -f backend/logs/app.log`
3. Enable debug mode: `DEBUG=True` in `.env`
4. Open a new issue with:
   - Error message
   - Environment (dev/staging/prod)
   - Steps to reproduce

---

**Last Updated:** 2025-01-18
