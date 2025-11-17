#!/bin/bash

# Test /auth/me endpoint
# 
# Usage:
#   export TEST_USERNAME=testuser
#   export TEST_PASSWORD=testpass123
#   export API_BASE_URL=http://localhost:8000  # Optional, defaults to localhost
#   ./test_auth_me.sh

# Configuration
USERNAME="${TEST_USERNAME:?Error: TEST_USERNAME environment variable not set}"
PASSWORD="${TEST_PASSWORD:?Error: TEST_PASSWORD environment variable not set}"
BASE_URL="${API_BASE_URL:-http://localhost:8000}/api/v1"

# Step 1: Login and get access token
echo "Step 1: Logging in..."
LOGIN_RESPONSE=$(curl -s -X POST "${BASE_URL}/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"${USERNAME}\",\"password\":\"${PASSWORD}\"}")

echo "Login response:"
echo "$LOGIN_RESPONSE" | python3 -m json.tool

# Step 2: Extract access token
ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

if [ -z "$ACCESS_TOKEN" ]; then
  echo "ERROR: Failed to get access token"
  exit 1
fi

echo ""
echo "Step 2: Access token extracted (length: ${#ACCESS_TOKEN})"
echo ""

# Step 3: Test /auth/me endpoint
echo "Step 3: Testing /auth/me endpoint..."
curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  "${BASE_URL}/auth/me" | python3 -m json.tool

echo ""
echo "Done!"

