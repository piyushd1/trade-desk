#!/bin/bash

# Step 1: Login and get access token
echo "Step 1: Logging in..."
LOGIN_RESPONSE=$(curl -s -X POST https://piyushdev.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"piyushdev","password":"piyush123"}')

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
  https://piyushdev.com/api/v1/auth/me | python3 -m json.tool

echo ""
echo "Done!"

