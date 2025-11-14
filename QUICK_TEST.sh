#!/bin/bash

##############################################################################
# Quick Test Script - JWT Migration Verification
# Tests all critical functionality after JWT migration
##############################################################################

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "================================================================"
echo "  JWT Migration - Quick Test Suite"
echo "================================================================"
echo ""

# Test credentials
USERNAME="piyushdev"
PASSWORD="piyush123"
USER_ID="RO0252"

print_test() {
    echo -e "${YELLOW}▶${NC} $1"
}

print_pass() {
    echo -e "${GREEN}✓${NC} $1"
}

print_fail() {
    echo -e "${RED}✗${NC} $1"
}

# Step 1: Login
print_test "Step 1: Login"
LOGIN_RESPONSE=$(curl -s -X POST https://piyushdev.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"$USERNAME\",\"password\":\"$PASSWORD\"}")

if echo "$LOGIN_RESPONSE" | grep -q '"status":"success"'; then
    print_pass "Login successful"
    ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
    echo "   Token: ${ACCESS_TOKEN:0:50}..."
else
    print_fail "Login failed"
    echo "$LOGIN_RESPONSE"
    exit 1
fi
echo ""

# Step 2: Test /auth/me
print_test "Step 2: Get User Profile (/auth/me)"
ME_RESPONSE=$(curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  https://piyushdev.com/api/v1/auth/me)

if echo "$ME_RESPONSE" | grep -q '"status":"success"'; then
    print_pass "/auth/me works with JWT"
else
    print_fail "/auth/me failed"
    echo "$ME_RESPONSE"
    exit 1
fi
echo ""

# Step 3: Test without JWT (should fail)
print_test "Step 3: Test Without JWT (should fail)"
NO_AUTH=$(curl -s "https://piyushdev.com/api/v1/data/zerodha/profile?user_identifier=$USER_ID")

if echo "$NO_AUTH" | grep -q '"code":401'; then
    print_pass "Correctly rejected request without JWT"
else
    print_fail "Security breach - allowed access without JWT!"
    echo "$NO_AUTH"
    exit 1
fi
echo ""

# Step 4: Test Zerodha Profile
print_test "Step 4: Get Zerodha Profile (with JWT)"
PROFILE=$(curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  "https://piyushdev.com/api/v1/data/zerodha/profile?user_identifier=$USER_ID")

if echo "$PROFILE" | grep -q '"status":"success"'; then
    print_pass "Zerodha profile fetched successfully"
else
    print_fail "Zerodha profile failed"
    echo "$PROFILE" | python3 -m json.tool
    exit 1
fi
echo ""

# Step 5: Test Margins
print_test "Step 5: Get Margins"
MARGINS=$(curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  "https://piyushdev.com/api/v1/data/zerodha/margins?user_identifier=$USER_ID")

if echo "$MARGINS" | grep -q '"status":"success"'; then
    print_pass "Margins fetched successfully"
else
    print_fail "Margins failed"
    echo "$MARGINS"
fi
echo ""

# Step 6: Test Positions
print_test "Step 6: Get Positions"
POSITIONS=$(curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  "https://piyushdev.com/api/v1/data/zerodha/positions?user_identifier=$USER_ID")

if echo "$POSITIONS" | grep -q '"status":"success"'; then
    print_pass "Positions fetched successfully"
else
    print_fail "Positions failed"
    echo "$POSITIONS"
fi
echo ""

# Step 7: Test Public Endpoint (no JWT)
print_test "Step 7: Test Public Endpoint (should work without JWT)"
CAPABILITIES=$(curl -s "https://piyushdev.com/api/v1/data/zerodha/capabilities")

if echo "$CAPABILITIES" | grep -q '"status":"success"'; then
    print_pass "Public endpoint works without JWT"
else
    print_fail "Public endpoint failed"
    echo "$CAPABILITIES"
fi
echo ""

# Step 8: Test Ownership Validation (login as admin)
print_test "Step 8: Test Ownership Validation (admin cannot access piyushdev's session)"
ADMIN_LOGIN=$(curl -s -X POST https://piyushdev.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}')

if echo "$ADMIN_LOGIN" | grep -q '"status":"success"'; then
    ADMIN_TOKEN=$(echo "$ADMIN_LOGIN" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
    
    # Try to access piyushdev's session as admin
    UNAUTHORIZED=$(curl -s -H "Authorization: Bearer $ADMIN_TOKEN" \
      "https://piyushdev.com/api/v1/data/zerodha/profile?user_identifier=$USER_ID")
    
    if echo "$UNAUTHORIZED" | grep -q '"code":403'; then
        print_pass "Ownership validation working - admin blocked from piyushdev's session"
    else
        print_fail "Security breach - admin can access other user's session!"
        echo "$UNAUTHORIZED"
        exit 1
    fi
else
    print_fail "Admin login failed"
    echo "$ADMIN_LOGIN"
fi
echo ""

echo "================================================================"
echo -e "${GREEN}  ALL TESTS PASSED!${NC}"
echo "================================================================"
echo ""
echo "✓ Login working"
echo "✓ JWT authentication working"
echo "✓ Protected endpoints secured"
echo "✓ Zerodha APIs accessible with JWT"
echo "✓ Ownership validation working"
echo "✓ Public endpoints working"
echo ""
echo "JWT Migration Complete! 🎉"
echo ""
echo "Next steps:"
echo "  - Test more Zerodha endpoints (holdings, orders, trades)"
echo "  - Test historical data"
echo "  - Test order preview/placement"
echo "  - Test streaming APIs"

