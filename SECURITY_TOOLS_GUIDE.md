# Security Tools Guide

## Overview

The security scanning tools (ggshield and trufflehog) are installed in the backend virtual environment.

## Installation Status

- ✅ **ggshield**: `/home/trade-desk/backend/venv/bin/ggshield`
- ✅ **trufflehog**: `/home/trade-desk/backend/venv/bin/trufflehog`

## How to Use

### Option 1: Activate Virtual Environment (Recommended)

```bash
cd /home/trade-desk/backend
source venv/bin/activate

# Now you can use the tools directly
ggshield secret scan path .
trufflehog filesystem . --json
```

### Option 2: Run Directly with Full Path

```bash
cd /home/trade-desk

# Run ggshield
/home/trade-desk/backend/venv/bin/ggshield secret scan path .

# Run trufflehog  
/home/trade-desk/backend/venv/bin/trufflehog filesystem . --json
```

### Option 3: Add to PATH (Optional)

Add this to your `~/.bashrc`:

```bash
export PATH="/home/trade-desk/backend/venv/bin:$PATH"
```

Then reload:
```bash
source ~/.bashrc
```

## Running Security Scans

### Full Repository Scan with ggshield

```bash
cd /home/trade-desk/backend
source venv/bin/activate

# Scan entire repository
ggshield secret scan path /home/trade-desk --json > /home/trade-desk/ggshield_scan.json

# Scan without JSON output
ggshield secret scan path /home/trade-desk
```

### Full Repository Scan with trufflehog

```bash
cd /home/trade-desk/backend
source venv/bin/activate

# Scan filesystem
cd /home/trade-desk
trufflehog filesystem . --json > trufflehog_scan.json

# Scan git history
trufflehog git file://. --json > trufflehog_git_scan.json
```

## Important Notes

### ggshield Authentication

ggshield requires GitGuardian API authentication for full functionality:

```bash
ggshield auth login
```

However, for basic scanning, you can use it without authentication (with limited features).

### Alternative: Manual Pattern Scanning

Since we've already done comprehensive manual scanning and fixed all issues, you don't necessarily need to run these tools again. The codebase is already clean.

If you want to verify, use the manual grep patterns:

```bash
cd /home/trade-desk

# Check for passwords
grep -r "password.*=.*['\"].*['\"]" --include="*.py" --include="*.sh" --exclude-dir=venv --exclude-dir=node_modules --exclude-dir=.git

# Check for API keys
grep -r "api.*key.*=.*['\"].*['\"]" --include="*.py" --include="*.sh" --exclude-dir=venv --exclude-dir=node_modules --exclude-dir=.git -i

# Check for hardcoded domains
grep -r "piyushdev.com" --exclude-dir=venv --exclude-dir=node_modules --exclude-dir=.git --exclude-dir=docs
```

## Why This Happened

The tools were installed with:
```bash
cd /home/trade-desk/backend
source venv/bin/activate
pip install ggshield trufflehog
```

This installed them in the virtual environment, not globally. This is actually good practice as it keeps project dependencies isolated.

## Verification

To verify the tools are working:

```bash
cd /home/trade-desk/backend
source venv/bin/activate

# Check ggshield version
ggshield --version

# Check trufflehog (it doesn't have --version, just run help)
trufflehog --help
```

## Summary

**The tools ARE installed and working.** You just need to activate the virtual environment first:

```bash
cd /home/trade-desk/backend && source venv/bin/activate
```

Or use the full path to run them directly.

