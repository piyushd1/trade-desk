# TradeDesk Setup Scripts & Documentation Guide

This document provides a complete overview of all setup scripts, configuration files, and documentation created for secure TradeDesk deployment.

---

## 📋 Table of Contents

1. [Setup Scripts Overview](#setup-scripts-overview)
2. [Environment Configuration Files](#environment-configuration-files)
3. [Infrastructure Templates](#infrastructure-templates)
4. [Documentation Files](#documentation-files)
5. [Quick Start Guide](#quick-start-guide)
6. [File Locations Reference](#file-locations-reference)

---

## 1. Setup Scripts Overview

### 📄 `scripts/setup_env.py`

**Purpose:** Automated environment configuration setup script

**What it does:**
- Copies `.env.example` to `.env` files for backend and frontend
- Generates secure cryptographic keys automatically (SECRET_KEY, JWT_SECRET_KEY, ENCRYPTION_KEY)
- Prompts for essential configuration values (domain, database, Zerodha credentials)
- Validates inputs and creates production-ready configuration

**Usage:**
```bash
# Run the interactive setup
python scripts/setup_env.py

# Or from project root
python3 scripts/setup_env.py
```

**Key Features:**
- ✅ Automatic Fernet key generation for encryption
- ✅ Secure token generation (64-character secrets)
- ✅ Interactive prompts with validation
- ✅ Support for SQLite (dev) and PostgreSQL (prod)
- ✅ Optional Zerodha broker configuration
- ✅ Colored terminal output for better UX

**When to use:** First-time setup or when resetting environment configuration

---

### 📄 `scripts/deploy_nginx.sh`

**Purpose:** Nginx configuration deployment script

**What it does:**
- Reads `APP_DOMAIN` from `backend/.env`
- Generates `nginx.conf` from `nginx.conf.template` using environment variable substitution
- Optionally installs configuration to `/etc/nginx/sites-available/`
- Tests nginx configuration validity
- Reloads nginx service

**Usage:**
```bash
# Generate nginx.conf (requires APP_DOMAIN in backend/.env)
./scripts/deploy_nginx.sh

# Or with sudo to install directly
sudo ./scripts/deploy_nginx.sh
```

**Key Features:**
- ✅ Template-based configuration (no hardcoded domains)
- ✅ Environment variable substitution using `envsubst`
- ✅ Automatic nginx syntax validation
- ✅ Safe deployment with rollback capability
- ✅ Colored output with status messages

**When to use:** Deploying to production or updating domain configuration

---

### 📄 `backend/scripts/create_default_user.py`

**Purpose:** Interactive admin user creation with security validation

**What it does:**
- Checks for admin credentials in environment variables (`ADMIN_USERNAME`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`)
- If not found, prompts interactively with secure input (password masking)
- Validates email format
- Validates password strength (8+ chars, uppercase, lowercase, number, special char)
- Creates admin user in database with hashed password

**Usage:**
```bash
# From backend directory
cd backend
python scripts/create_default_user.py

# With environment variables set
ADMIN_USERNAME=admin ADMIN_EMAIL=admin@example.com ADMIN_PASSWORD='SecurePass123!' python scripts/create_default_user.py
```

**Key Features:**
- ✅ Interactive prompts with `getpass` (password masking)
- ✅ Strong password validation
- ✅ Email format validation
- ✅ Password confirmation
- ✅ Checks for existing users
- ✅ No password display in console

**When to use:** First-time setup to create initial admin account

---

## 2. Environment Configuration Files

### 📄 `backend/.env.example`

**Purpose:** Template for backend environment configuration

**Contains:**
- Application settings (APP_NAME, APP_ENV, DEBUG, SECRET_KEY)
- URLs (APP_DOMAIN, APP_URL, API_BASE_URL, FRONTEND_URL)
- Database configuration (DATABASE_URL, connection pool settings)
- Redis and Celery configuration
- JWT authentication settings (JWT_SECRET_KEY, token expiration)
- Encryption key (ENCRYPTION_KEY)
- SEBI compliance settings (STATIC_IP, trade limits)
- Broker integration (Zerodha, Groww credentials)
- Risk management parameters
- Admin user configuration (ADMIN_USERNAME, ADMIN_EMAIL, ADMIN_PASSWORD)
- Test environment configuration

**Size:** 3.3 KB (fully documented with comments)

**Key sections:**
```bash
# Required for application startup
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key
ENCRYPTION_KEY=your-fernet-key
DATABASE_URL=sqlite+aiosqlite:///./tradedesk.db
REDIS_URL=redis://localhost:6379/0

# Your domain configuration
APP_DOMAIN=example.com
API_BASE_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000

# SEBI compliance
STATIC_IP=your-static-ip

# Broker integration (optional)
ZERODHA_API_KEY=your-api-key
ZERODHA_API_SECRET=your-api-secret
ZERODHA_USER_IDENTIFIER=YOUR_USER_ID
```

**Usage:**
```bash
# Copy to create your .env file
cp backend/.env.example backend/.env

# Edit with your values
nano backend/.env
```

---

### 📄 `frontend/.env.local.example`

**Purpose:** Template for frontend environment configuration

**Contains:**
- API URL configuration (NEXT_PUBLIC_API_URL)
- Optional analytics configuration
- Optional Sentry DSN for error tracking

**Size:** 731 bytes

**Key sections:**
```bash
# Backend API URL (must be prefixed with NEXT_PUBLIC_)
NEXT_PUBLIC_API_URL=/api/v1

# Optional configuration
# NEXT_PUBLIC_APP_NAME=TradeDesk
# NEXT_PUBLIC_GA_ID=your-google-analytics-id
```

**Usage:**
```bash
# Copy to create your .env.local file
cp frontend/.env.local.example frontend/.env.local

# Edit if needed (defaults usually work)
nano frontend/.env.local
```

---

## 3. Infrastructure Templates

### 📄 `nginx.conf.template`

**Purpose:** Template-based nginx configuration with environment variable substitution

**Contains:**
- HTTP to HTTPS redirect configuration
- SSL/TLS security settings
- Security headers (HSTS, X-Frame-Options, CSP)
- Proxy configuration for FastAPI backend
- API documentation protection (password-protected /docs)
- Health check endpoint
- Logging configuration

**Size:** 3.2 KB

**Key features:**
- Uses `${APP_DOMAIN}` placeholder for domain name
- SSL certificate paths use domain variable
- Supports Let's Encrypt ACME challenges
- Reverse proxy to backend (127.0.0.1:8000)

**Template variables:**
```nginx
# These get replaced by deploy_nginx.sh
server_name ${APP_DOMAIN} www.${APP_DOMAIN};
ssl_certificate /etc/letsencrypt/live/${APP_DOMAIN}/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/${APP_DOMAIN}/privkey.pem;
```

**Generated output:** `nginx.conf` (excluded from git)

---

## 4. Documentation Files

### 📄 `ENVIRONMENT_SETUP.md`

**Purpose:** Comprehensive environment configuration guide

**Size:** 12 KB

**Sections:**
1. **Quick Start** - Automated and manual setup instructions
2. **Environment Variables Reference** - Complete table of all variables
3. **Security Best Practices** - Key rotation, secrets management, SEBI compliance
4. **Configuration for Different Environments** - Dev, staging, production examples
5. **Database Configuration** - SQLite vs PostgreSQL setup
6. **Nginx Configuration** - Deployment and troubleshooting
7. **First-Time Setup** - Step-by-step initial configuration
8. **Troubleshooting** - Common issues and solutions

**Key sections covered:**

#### Quick Start
- Automated setup with `setup_env.py`
- Manual setup steps
- Key generation commands

#### Environment Variables Reference
- Complete table of all 50+ environment variables
- Required vs optional distinction
- Default values and production examples
- Security considerations for each

#### Security Best Practices
- Never commit secrets to git
- Use strong, unique keys
- Key rotation strategies
- Different credentials per environment
- Secrets management services (AWS, Vault, Azure, GCP)
- SEBI compliance requirements

#### Configuration Examples
- Development environment setup
- Staging environment setup
- Production environment setup
- Database configuration (SQLite vs PostgreSQL)

#### Troubleshooting
- Config validation errors
- Invalid Fernet key errors
- Database connection issues
- Zerodha API authentication failures
- Nginx configuration problems

---

## 5. Quick Start Guide

### Complete First-Time Setup

```bash
# 1. Clone the repository
git clone https://github.com/piyushd1/trade-desk.git
cd trade-desk

# 2. Run automated environment setup
python scripts/setup_env.py

# This will:
# - Copy .env.example to .env files
# - Generate secure keys
# - Prompt for essential config (domain, database, etc.)
# - Configure Zerodha integration (optional)

# 3. Create admin user
cd backend
python scripts/create_default_user.py

# This will prompt for:
# - Username (default: admin)
# - Email address
# - Full name
# - Password (with strength validation)

# 4. Install dependencies
# Backend
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install

# 5. Run database migrations
cd ../backend
alembic upgrade head

# 6. Start the application
# Terminal 1 - Backend
cd backend
uvicorn app.main:app --reload

# Terminal 2 - Frontend
cd frontend
npm run dev
```

### Deployment to Production

```bash
# 1. Ensure .env is configured for production
nano backend/.env
# Set:
# - APP_ENV=production
# - DEBUG=False
# - Production DATABASE_URL
# - Production REDIS_URL
# - Your domain and static IP

# 2. Generate and deploy nginx configuration
./scripts/deploy_nginx.sh

# With sudo for automatic installation:
sudo ./scripts/deploy_nginx.sh

# 3. Set up SSL certificates (if not already done)
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# 4. Start services
# Using systemd (recommended)
sudo systemctl start tradedesk-backend
sudo systemctl start tradedesk-frontend

# Or using Docker
docker-compose up -d
```

---

## 6. File Locations Reference

### Complete File Tree

```
trade-desk/
│
├── 📁 scripts/
│   ├── setup_env.py              # ✨ NEW: Automated environment setup
│   ├── deploy_nginx.sh           # ✨ NEW: Nginx deployment script
│   └── fetch_nifty50_data.py     # Existing: Data fetching script
│
├── 📁 backend/
│   ├── .env.example              # ✨ NEW: Backend environment template
│   ├── .env                      # ⚠️  GITIGNORED: Your actual config
│   │
│   ├── 📁 scripts/
│   │   └── create_default_user.py  # ✨ ENHANCED: Interactive admin setup
│   │
│   ├── 📁 app/
│   │   ├── config.py             # ✨ UPDATED: New environment variables
│   │   ├── main.py               # ✨ UPDATED: Removed hardcoded credentials
│   │   │
│   │   └── 📁 api/v1/
│   │       └── auth.py           # ✨ UPDATED: Generic examples
│   │
│   └── 📁 tests/
│       └── conftest.py           # ✨ UPDATED: Uses env vars for tests
│
├── 📁 frontend/
│   ├── .env.local.example        # ✨ NEW: Frontend environment template
│   └── .env.local                # ⚠️  GITIGNORED: Your actual config
│
├── nginx.conf.template           # ✨ NEW: Template with ${APP_DOMAIN}
├── nginx.conf                    # ⚠️  GITIGNORED: Generated config
├── nginx-config-updated.conf     # Old file (kept for reference)
│
├── ENVIRONMENT_SETUP.md          # ✨ NEW: Complete setup guide
├── SETUP_INSTRUCTIONS.md         # ✨ UPDATED: Generic placeholders
├── MASTER_REFERENCE.md           # ✨ UPDATED: Generic placeholders
├── QUICK_START.md                # ✨ UPDATED: Generic placeholders
├── README.md                     # ✨ UPDATED: Generic placeholders
│
└── .gitignore                    # ✨ UPDATED: Excludes .env and nginx.conf
```

### Legend:
- ✨ **NEW**: Newly created file
- ✨ **ENHANCED**: Significantly improved file
- ✨ **UPDATED**: Modified for security
- ⚠️  **GITIGNORED**: Not tracked by git (contains secrets)

---

## 🔐 Security Features Summary

### What's Protected:
✅ No hardcoded passwords or API keys
✅ No personal email addresses (piyush.dev@gmail.com removed)
✅ No hardcoded usernames (piyushdev replaced with trader)
✅ No hardcoded domains (piyushdev.com replaced with yourdomain.com)
✅ All test credentials moved to environment variables
✅ Automatic secure key generation
✅ Password strength validation
✅ All sensitive files properly gitignored

### What's Safe to Share:
✅ All code files (.py, .js, .ts)
✅ All documentation (.md files)
✅ All template files (.example, .template)
✅ Configuration examples
✅ Setup scripts

### What's Never Committed:
❌ `.env` files (actual credentials)
❌ `nginx.conf` (generated config with your domain)
❌ Database files
❌ Log files
❌ Secrets directory

---

## 📚 Additional Resources

### Internal Documentation:
- `ENVIRONMENT_SETUP.md` - Complete environment configuration guide (12 KB)
- `SETUP_INSTRUCTIONS.md` - Step-by-step setup instructions
- `MASTER_REFERENCE.md` - Complete API reference
- `README.md` - Project overview and quick start
- `QUICK_START.md` - Fast-track setup guide

### External Links:
- [Zerodha Kite Connect API Docs](https://kite.trade/docs/connect/v3/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)
- [Nginx Configuration Best Practices](https://www.nginx.com/resources/wiki/start/)
- [Python Cryptography Library](https://cryptography.io/en/latest/)

---

## 🆘 Getting Help

### If you encounter issues:

1. **Check the documentation:**
   - Read `ENVIRONMENT_SETUP.md` for detailed setup instructions
   - Review `SETUP_INSTRUCTIONS.md` for step-by-step guidance

2. **Enable debug mode:**
   ```bash
   # In backend/.env
   DEBUG=True
   LOG_LEVEL=DEBUG
   ```

3. **Check logs:**
   ```bash
   # Application logs
   tail -f backend/logs/app.log

   # Nginx logs (if deployed)
   sudo tail -f /var/log/nginx/trade-desk-error.log
   ```

4. **Validate configuration:**
   ```bash
   # Test if all required env vars are set
   cd backend
   python -c "from app.config import settings; print('✅ Config loaded successfully')"
   ```

5. **Open an issue:**
   - GitHub: https://github.com/piyushd1/trade-desk/issues
   - Include: Error message, environment (dev/prod), steps to reproduce

---

## 🎯 Next Steps

After setup is complete:

1. ✅ **Configure Zerodha Integration**
   - Get your API keys from Kite Connect
   - Add to `backend/.env`
   - Test OAuth flow

2. ✅ **Set Up SSL Certificates** (Production)
   ```bash
   sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
   ```

3. ✅ **Configure Database Backups**
   - Set up automated backups (daily recommended)
   - Store backups securely off-site
   - Test restore procedure

4. ✅ **Enable Monitoring**
   - Set up Prometheus/Grafana (ports configured)
   - Configure alert rules
   - Set up uptime monitoring

5. ✅ **Review Security**
   - Run security audit: `safety check`
   - Enable rate limiting
   - Configure firewall rules
   - Review SEBI compliance checklist

6. ✅ **Performance Tuning**
   - Configure Redis caching
   - Optimize database queries
   - Set up CDN (if needed)
   - Load testing

---

**Last Updated:** 2025-01-18
**Version:** 1.0
**Author:** TradeDesk Security Team
