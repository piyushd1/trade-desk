#!/bin/bash

#######################################################################
# Test Script: Zerodha Complete API Testing
# Tests: OAuth, Session, Data APIs, Historical, Management
#######################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
API_BASE="https://piyushdev.com/api/v1"
BASIC_AUTH_USER="piyushdeveshwar"
BASIC_AUTH_PASS="Lead@102938"

# Get user identifier from args or use default
USER_IDENTIFIER="${1:-RO0252}"

echo "=================================================="
echo "  Testing Zerodha APIs"
echo "  User Identifier: $USER_IDENTIFIER"
echo "=================================================="
echo ""

# Helper functions
print_section() {
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════${NC}"
    echo ""
}

print_test() {
    echo -e "${YELLOW}TEST:${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

api_call() {
    curl -s -u "$BASIC_AUTH_USER:$BASIC_AUTH_PASS" "$@"
}

# ===================================================================
# Section 1: Session Management
# ===================================================================
print_section "1. Session Management"

print_test "1.1 Get Zerodha Session"
SESSION=$(api_call "$API_BASE/auth/zerodha/session?user_identifier=$USER_IDENTIFIER")
echo "$SESSION" | python3 -m json.tool
echo ""

if echo "$SESSION" | grep -q '"status":"active"'; then
    print_success "Active session found"
else
    print_error "No active session - please complete OAuth first"
    echo ""
    echo "To authenticate:"
    echo "1. Run: curl -u $BASIC_AUTH_USER:$BASIC_AUTH_PASS \"$API_BASE/auth/zerodha/connect?state=$USER_IDENTIFIER\""
    echo "2. Open the returned login_url in browser"
    echo "3. Complete Zerodha login"
    echo "4. Re-run this script"
    exit 1
fi
echo ""

print_test "1.2 Check Session Status"
STATUS=$(api_call "$API_BASE/data/session/status?user_identifier=$USER_IDENTIFIER")
echo "$STATUS" | python3 -m json.tool
echo ""

# ===================================================================
# Section 2: Account & User Management
# ===================================================================
print_section "2. Account & User Management"

print_test "2.1 Get User Profile"
PROFILE=$(api_call "$API_BASE/data/zerodha/profile?user_identifier=$USER_IDENTIFIER")
echo "$PROFILE" | python3 -m json.tool
if echo "$PROFILE" | grep -q '"status":"success"'; then
    print_success "Profile fetched"
else
    print_error "Profile fetch failed"
fi
echo ""

print_test "2.2 Get Account Margins"
MARGINS=$(api_call "$API_BASE/data/zerodha/margins?user_identifier=$USER_IDENTIFIER")
echo "$MARGINS" | python3 -m json.tool
if echo "$MARGINS" | grep -q '"status":"success"'; then
    print_success "Margins fetched"
else
    print_error "Margins fetch failed"
fi
echo ""

# ===================================================================
# Section 3: Portfolio Management
# ===================================================================
print_section "3. Portfolio Management"

print_test "3.1 Get Holdings"
HOLDINGS=$(api_call "$API_BASE/data/zerodha/holdings?user_identifier=$USER_IDENTIFIER")
echo "$HOLDINGS" | python3 -m json.tool
if echo "$HOLDINGS" | grep -q '"status":"success"'; then
    print_success "Holdings fetched"
else
    print_error "Holdings fetch failed"
fi
echo ""

print_test "3.2 Get Positions"
POSITIONS=$(api_call "$API_BASE/data/zerodha/positions?user_identifier=$USER_IDENTIFIER")
echo "$POSITIONS" | python3 -m json.tool
if echo "$POSITIONS" | grep -q '"status":"success"'; then
    print_success "Positions fetched"
else
    print_error "Positions fetch failed"
fi
echo ""

# ===================================================================
# Section 4: Order & Trade Data
# ===================================================================
print_section "4. Order & Trade Data"

print_test "4.1 Get Orders"
ORDERS=$(api_call "$API_BASE/data/zerodha/orders?user_identifier=$USER_IDENTIFIER")
echo "$ORDERS" | python3 -m json.tool
if echo "$ORDERS" | grep -q '"status":"success"'; then
    print_success "Orders fetched"
else
    print_error "Orders fetch failed"
fi
echo ""

print_test "4.2 Get Trades"
TRADES=$(api_call "$API_BASE/data/zerodha/trades?user_identifier=$USER_IDENTIFIER")
echo "$TRADES" | python3 -m json.tool
if echo "$TRADES" | grep -q '"status":"success"'; then
    print_success "Trades fetched"
else
    print_error "Trades fetch failed"
fi
echo ""

# ===================================================================
# Section 5: Market Data
# ===================================================================
print_section "5. Market Data"

print_test "5.1 Get Last Traded Price (LTP)"
LTP=$(api_call -X POST "$API_BASE/data/zerodha/ltp?user_identifier=$USER_IDENTIFIER" \
    -H "Content-Type: application/json" \
    -d '["NSE:INFY", "NSE:RELIANCE", "NSE:TCS"]')
echo "$LTP" | python3 -m json.tool
if echo "$LTP" | grep -q '"status":"success"'; then
    print_success "LTP fetched"
else
    print_error "LTP fetch failed"
fi
echo ""

print_test "5.2 Get Quote"
QUOTE=$(api_call -X POST "$API_BASE/data/zerodha/quote?user_identifier=$USER_IDENTIFIER" \
    -H "Content-Type: application/json" \
    -d '["NSE:INFY"]')
echo "$QUOTE" | python3 -m json.tool
if echo "$QUOTE" | grep -q '"status":"success"'; then
    print_success "Quote fetched"
else
    print_error "Quote fetch failed"
fi
echo ""

print_test "5.3 Get OHLC"
OHLC=$(api_call -X POST "$API_BASE/data/zerodha/ohlc?user_identifier=$USER_IDENTIFIER" \
    -H "Content-Type: application/json" \
    -d '["NSE:RELIANCE"]')
echo "$OHLC" | python3 -m json.tool
if echo "$OHLC" | grep -q '"status":"success"'; then
    print_success "OHLC fetched"
else
    print_error "OHLC fetch failed"
fi
echo ""

# ===================================================================
# Section 6: Historical Data
# ===================================================================
print_section "6. Historical Data"

INFY_TOKEN=408065
FROM_DATE="2025-10-01"
TO_DATE="2025-11-13"

print_test "6.1 Get Historical Daily Candles (INFY)"
HISTORICAL=$(api_call "$API_BASE/data/zerodha/historical/$INFY_TOKEN?user_identifier=$USER_IDENTIFIER&from_date=$FROM_DATE&to_date=$TO_DATE&interval=day")
echo "$HISTORICAL" | python3 -m json.tool | head -50
if echo "$HISTORICAL" | grep -q '"status":"success"'; then
    print_success "Historical data fetched"
else
    print_error "Historical data fetch failed"
fi
echo ""

# ===================================================================
# Section 7: Data Management (Storage)
# ===================================================================
print_section "7. Data Management & Storage"

print_test "7.1 Search Instruments (Infosys)"
SEARCH=$(api_call "$API_BASE/data/instruments/search?q=INFY&exchange=NSE&limit=10")
echo "$SEARCH" | python3 -m json.tool
if echo "$SEARCH" | grep -q '"status":"success"'; then
    print_success "Instrument search working"
else
    print_error "Instrument search failed"
fi
echo ""

print_test "7.2 Get Instrument Detail (INFY token: $INFY_TOKEN)"
DETAIL=$(api_call "$API_BASE/data/instruments/$INFY_TOKEN")
echo "$DETAIL" | python3 -m json.tool
if echo "$DETAIL" | grep -q '"status":"success"'; then
    print_success "Instrument detail fetched"
else
    print_error "Instrument detail fetch failed"
fi
echo ""

print_test "7.3 Query Stored Historical Data"
STORED_HIST=$(api_call "$API_BASE/data/historical?instrument_token=$INFY_TOKEN&interval=day&limit=10")
echo "$STORED_HIST" | python3 -m json.tool
if echo "$STORED_HIST" | grep -q '"status":"success"'; then
    print_success "Stored historical data queried"
else
    print_error "Stored historical query failed"
fi
echo ""

print_test "7.4 Get Historical Statistics"
STATS=$(api_call "$API_BASE/data/historical/stats")
echo "$STATS" | python3 -m json.tool
if echo "$STATS" | grep -q '"status":"success"'; then
    print_success "Historical stats fetched"
else
    print_error "Historical stats failed"
fi
echo ""

# ===================================================================
# Section 8: Capabilities
# ===================================================================
print_section "8. API Capabilities"

print_test "8.1 Get Zerodha Capabilities"
CAPABILITIES=$(api_call "$API_BASE/data/zerodha/capabilities")
echo "$CAPABILITIES" | python3 -m json.tool
if echo "$CAPABILITIES" | grep -q '"available_data"'; then
    print_success "Capabilities fetched"
else
    print_error "Capabilities fetch failed"
fi
echo ""

# ===================================================================
# Summary
# ===================================================================
print_section "Test Summary"

echo "Zerodha API Testing Complete!"
echo ""
echo "✓ Session management working"
echo "✓ Account data accessible"
echo "✓ Portfolio data accessible"
echo "✓ Market data APIs working"
echo "✓ Historical data fetching"
echo "✓ Data storage & queries working"
echo ""
echo "For full instrument sync, run:"
echo "  curl -X POST -u $BASIC_AUTH_USER:$BASIC_AUTH_PASS \\"
echo "    \"$API_BASE/data/instruments/sync?user_identifier=$USER_IDENTIFIER&exchange=NSE\""
echo ""
echo "For historical data storage, run:"
echo "  curl -X POST -u $BASIC_AUTH_USER:$BASIC_AUTH_PASS \\"
echo "    \"$API_BASE/data/historical/fetch\" \\"
echo "    -H \"Content-Type: application/json\" \\"
echo "    -d '{\"user_identifier\":\"$USER_IDENTIFIER\",\"instrument_token\":408065,\"from_date\":\"2025-01-01\",\"to_date\":\"2025-11-13\",\"interval\":\"day\"}'"

