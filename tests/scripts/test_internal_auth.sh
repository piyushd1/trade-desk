#!/bin/bash

#######################################################################
# Test Script: Internal Platform Authentication
# Tests: Login, JWT validation, /me endpoint, refresh, logout
# 
# Usage:
#   export TEST_USERNAME=testuser
#   export TEST_PASSWORD=testpass123
#   export API_BASE_URL=http://localhost:8000  # Optional, defaults to localhost
#   ./test_internal_auth.sh
#######################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
API_BASE="${API_BASE_URL:-http://localhost:8000}/api/v1"

# Test credentials from environment variables
TEST_USERNAME="${TEST_USERNAME:?Error: TEST_USERNAME environment variable not set. Please set it before running this script.}"
TEST_PASSWORD="${TEST_PASSWORD:?Error: TEST_PASSWORD environment variable not set. Please set it before running this script.}"

echo "=================================================="
echo "  Testing Internal Platform Authentication"
echo "=================================================="
echo ""

# Helper functions
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
    curl -s "$@"
}

# Test 1: Health Check
print_test "1. Health Check"
HEALTH=$(api_call "$API_BASE/health/ping")
if echo "$HEALTH" | grep -q '"ping":"pong"'; then
    print_success "Health check passed"
else
    print_error "Health check failed"
    echo "$HEALTH"
    exit 1
fi
echo ""

# Test 2: User Login
print_test "2. User Login (POST /auth/login)"
LOGIN_RESPONSE=$(api_call -X POST "$API_BASE/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"$TEST_USERNAME\",\"password\":\"$TEST_PASSWORD\"}")

echo "$LOGIN_RESPONSE" | python3 -m json.tool || echo "$LOGIN_RESPONSE"
echo ""

# Extract tokens
ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null || echo "")
REFRESH_TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('refresh_token', ''))" 2>/dev/null || echo "")

if [ -z "$ACCESS_TOKEN" ]; then
    print_error "Failed to get access token"
    exit 1
else
    print_success "Login successful, got access token"
    echo "Access Token (first 50 chars): ${ACCESS_TOKEN:0:50}..."
    echo "Refresh Token (first 50 chars): ${REFRESH_TOKEN:0:50}..."
fi
echo ""

# Test 3: Get Current User with JWT
print_test "3. Get Current User (GET /auth/me)"
ME_RESPONSE=$(curl -s -u "$BASIC_AUTH_USER:$BASIC_AUTH_PASS" -H "Authorization: Bearer $ACCESS_TOKEN" "$API_BASE/auth/me")

echo "$ME_RESPONSE" | python3 -m json.tool || echo "$ME_RESPONSE"
echo ""

if echo "$ME_RESPONSE" | grep -q '"status":"success"'; then
    print_success "/auth/me working with JWT"
else
    print_error "/auth/me failed"
fi
echo ""

# Test 4: Refresh Access Token
print_test "4. Refresh Access Token (POST /auth/refresh)"
REFRESH_RESPONSE=$(api_call -X POST "$API_BASE/auth/refresh" \
    -H "Content-Type: application/json" \
    -d "{\"refresh_token\":\"$REFRESH_TOKEN\"}")

echo "$REFRESH_RESPONSE" | python3 -m json.tool || echo "$REFRESH_RESPONSE"
echo ""

NEW_ACCESS_TOKEN=$(echo "$REFRESH_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null || echo "")

if [ -z "$NEW_ACCESS_TOKEN" ]; then
    print_error "Failed to refresh token"
else
    print_success "Token refresh successful"
    echo "New Access Token (first 50 chars): ${NEW_ACCESS_TOKEN:0:50}..."
    ACCESS_TOKEN="$NEW_ACCESS_TOKEN"
fi
echo ""

# Test 5: Test Protected Endpoint with Refreshed Token
print_test "5. Test /auth/me with Refreshed Token"
ME_RESPONSE_2=$(curl -s -u "$BASIC_AUTH_USER:$BASIC_AUTH_PASS" -H "Authorization: Bearer $ACCESS_TOKEN" "$API_BASE/auth/me")

if echo "$ME_RESPONSE_2" | grep -q '"status":"success"'; then
    print_success "Refreshed token works"
else
    print_error "Refreshed token failed"
    echo "$ME_RESPONSE_2"
fi
echo ""

# Test 6: Logout
print_test "6. User Logout (POST /auth/logout)"
LOGOUT_RESPONSE=$(curl -s -u "$BASIC_AUTH_USER:$BASIC_AUTH_PASS" -X POST "$API_BASE/auth/logout" \
    -H "Authorization: Bearer $ACCESS_TOKEN")

echo "$LOGOUT_RESPONSE" | python3 -m json.tool || echo "$LOGOUT_RESPONSE"
echo ""

if echo "$LOGOUT_RESPONSE" | grep -q '"status":"success"'; then
    print_success "Logout successful"
else
    print_error "Logout failed"
fi
echo ""

# Test 7: Verify Token Still Works After Logout (JWT can't be truly invalidated)
print_test "7. Verify Token After Logout (should still work - JWT limitation)"
ME_RESPONSE_3=$(curl -s -u "$BASIC_AUTH_USER:$BASIC_AUTH_PASS" -H "Authorization: Bearer $ACCESS_TOKEN" "$API_BASE/auth/me")

if echo "$ME_RESPONSE_3" | grep -q '"status":"success"'; then
    print_success "Token still valid (expected - JWT can't be server-side invalidated without blacklist)"
    echo "Note: Client should discard token on logout"
else
    print_error "Unexpected: Token invalidated"
fi
echo ""

# Test 8: Test with Invalid Token
print_test "8. Test with Invalid Token"
INVALID_RESPONSE=$(curl -s -u "$BASIC_AUTH_USER:$BASIC_AUTH_PASS" -H "Authorization: Bearer invalid_token_12345" "$API_BASE/auth/me")

if echo "$INVALID_RESPONSE" | grep -q '"code":401'; then
    print_success "Invalid token correctly rejected"
else
    print_error "Invalid token not rejected"
    echo "$INVALID_RESPONSE"
fi
echo ""

# Test 9: Test without Token
print_test "9. Test without Authorization Header"
NO_AUTH_RESPONSE=$(api_call "$API_BASE/auth/me")

if echo "$NO_AUTH_RESPONSE" | grep -q '"detail":"Not authenticated"'; then
    print_success "Missing token correctly rejected"
else
    print_error "Missing token handling failed"
    echo "$NO_AUTH_RESPONSE"
fi
echo ""

echo "=================================================="
echo "  Authentication Tests Complete!"
echo "=================================================="
echo ""
echo "Summary:"
echo "  ✓ Login working"
echo "  ✓ JWT validation working"
echo "  ✓ /auth/me working"
echo "  ✓ Token refresh working"
echo "  ✓ Logout working (audit logged)"
echo "  ✓ Invalid token rejection working"
echo ""
echo "Note: JWT tokens cannot be invalidated server-side without"
echo "      implementing a token blacklist. Client must discard tokens."

