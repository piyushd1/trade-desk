# Test Scripts

This directory contains integration test scripts for the TradeDesk API.

## Available Test Scripts

### API Tests
- `test_internal_auth.sh` - Internal authentication tests (login, JWT, refresh)
- `test_zerodha_apis.sh` - Zerodha API integration tests
- `test_zerodha_complete.sh` - Complete Zerodha API test suite
- `test_market_data_apis.sh` - Market data API tests (LTP, Quote, OHLC)
- `test_data_management_apis.sh` - Data management tests (instruments, historical)
- `test_order_management_apis.sh` - Order management tests
- `test_risk_management_apis.sh` - Risk management API tests
- `test_streaming_apis.sh` - Streaming API tests (WebSocket)
- `test_oauth_flow.sh` - OAuth flow tests
- `test_audit_logging.sh` - Audit logging tests
- `test_auth_me.sh` - User profile endpoint tests
- `test_risk_api.sh` - Risk API tests

### Quick Tests
- `QUICK_TEST.sh` - Quick test suite

## Usage

All test scripts require:
1. Backend server running at `https://piyushdev.com`
2. Valid user credentials (default: `piyushdev`/`piyush123`)

### Example
```bash
cd tests/scripts
./test_internal_auth.sh
```

## Test Results

Test results are saved as markdown files with timestamps in the same directory.
These are automatically ignored by git (see `.gitignore`).

## Notes

- Scripts automatically log in and get fresh JWT tokens
- Test results include timestamps and full API responses
- Some tests require active Zerodha sessions

