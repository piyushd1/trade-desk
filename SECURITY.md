# Security Best Practices

## Overview

This document outlines security best practices for the TradeDesk application.

## Secrets Management

### Environment Variables

**Never commit secrets to git**. All secrets must be stored in environment variables.

**Required Environment Variables:**
- `SECRET_KEY` - Application secret key (32+ characters)
- `ENCRYPTION_KEY` - Fernet encryption key (32 bytes, base64)
- `JWT_SECRET_KEY` - JWT signing key (32+ characters)
- `ZERODHA_API_KEY` - Zerodha API key
- `ZERODHA_API_SECRET` - Zerodha API secret

**Generating Secure Keys:**

```bash
# Generate SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate ENCRYPTION_KEY
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Generate JWT_SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Setting Up Environment

1. **Backend:**
   ```bash
   cd backend
   cp .env.example .env
   # Edit .env with your actual values
   ```

2. **Frontend:**
   ```bash
   cd frontend
   cp .env.local.example .env.local
   # Edit .env.local with your actual values
   ```

3. **Test Environment:**
   ```bash
   cp TEST_ENV.example TEST_ENV
   # Edit TEST_ENV with your test credentials
   source TEST_ENV
   ```

## Testing Securely

### Running Test Scripts

All test scripts now require environment variables:

```bash
export TEST_USERNAME=testuser
export TEST_PASSWORD=testpass123
export USER_IDENTIFIER=your_user_id
export API_BASE_URL=http://localhost:8000

# Run tests
./tests/scripts/test_fundamentals_apis.sh
```

**Never hardcode credentials** in test scripts or documentation.

## Git Best Practices

### Before Committing

1. **Never commit:**
   - `.env` files
   - Files containing API keys or passwords
   - Files containing real user data
   - Files containing production URLs

2. **Always commit:**
   - `.env.example` files (with placeholders)
   - `TEST_ENV.example` (with placeholders)
   - Test scripts (using environment variables)

### Pre-commit Checks

Run these checks before committing:

```bash
# Check for hardcoded secrets
grep -r "piyushdev.com" . --exclude-dir=.git --exclude-dir=node_modules
grep -r "piyush123" . --exclude-dir=.git --exclude-dir=node_modules
grep -r "RO0252" . --exclude-dir=.git --exclude-dir=node_modules

# Check .env files are not staged
git status | grep ".env"
```

## Code Review Checklist

- [ ] No hardcoded credentials
- [ ] No hardcoded URLs (use environment variables)
- [ ] No real user data in examples
- [ ] All secrets in environment variables
- [ ] `.env` files not committed
- [ ] Example files use placeholders

## Reporting Security Issues

If you discover a security vulnerability, please:
1. **Do not** create a public GitHub issue
2. Contact the repository owner directly
3. Provide details of the vulnerability
4. Wait for a response before disclosing publicly

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [SEBI Compliance Requirements](docs/02_COMPLIANCE_REQUIREMENTS.md)
- [Testing Documentation](TESTING.md)

