#!/bin/bash

# Zerodha Re-authentication Helper
# 
# Usage:
#   export TEST_USERNAME=testuser
#   export TEST_PASSWORD=testpass123
#   export USER_IDENTIFIER=your_user_id
#   export API_BASE_URL=http://localhost:8000  # Optional, defaults to localhost
#   ./zerodha_reauth.sh

echo "=========================================="
echo "Zerodha Re-authentication Helper"
echo "=========================================="
echo ""

# Configuration
USERNAME="${TEST_USERNAME:?Error: TEST_USERNAME environment variable not set}"
PASSWORD="${TEST_PASSWORD:?Error: TEST_PASSWORD environment variable not set}"
USER_ID="${USER_IDENTIFIER:?Error: USER_IDENTIFIER environment variable not set}"
BASE_URL="${API_BASE_URL:-http://localhost:8000}/api/v1"

# Step 1: Get OAuth URL
echo "Step 1: Getting OAuth URL..."
OAUTH_RESPONSE=$(curl -s "${BASE_URL}/auth/zerodha/connect?state=${USER_ID}")
LOGIN_URL=$(echo "$OAUTH_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['login_url'])")

echo "✅ OAuth URL generated"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 NEXT STEPS:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1. Open this URL in your browser:"
echo "   $LOGIN_URL"
echo ""
echo "2. Login with your Zerodha credentials"
echo ""
echo "3. Authorize the application"
echo ""
echo "4. After authorization, you'll see a JSON response with session details"
echo ""
echo "5. Once you see the success message, come back here and press ENTER"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
read -p "Press ENTER after you've completed Zerodha authentication in browser..."

# Step 2: Login to TradeDesk
echo ""
echo "Step 2: Logging in to TradeDesk..."
LOGIN_RESPONSE=$(curl -s -X POST "${BASE_URL}/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"${USERNAME}\",\"password\":\"${PASSWORD}\"}")

ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

if [ -z "$ACCESS_TOKEN" ]; then
  echo "❌ ERROR: Failed to get access token"
  echo "Login response:"
  echo "$LOGIN_RESPONSE" | python3 -m json.tool
  exit 1
fi

echo "✅ Logged in successfully"
echo ""

# Step 3: Claim the session
echo "Step 3: Claiming Zerodha session (linking to your account)..."
CLAIM_RESPONSE=$(curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  -X POST "${BASE_URL}/auth/zerodha/session/claim?user_identifier=${USER_ID}")

echo "$CLAIM_RESPONSE" | python3 -m json.tool

# Check if claim was successful
STATUS=$(echo "$CLAIM_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('status', 'error'))" 2>/dev/null)

if [ "$STATUS" = "success" ]; then
  echo ""
  echo "✅ Session claimed successfully!"
  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "🎉 Ready to test Zerodha APIs!"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo ""
  echo "Your ACCESS_TOKEN is now set. You can test Zerodha APIs:"
  echo ""
  echo "  curl -s -H \"Authorization: Bearer $ACCESS_TOKEN\" \\"
  echo "    \"${BASE_URL}/data/zerodha/profile?user_identifier=${USER_ID}\" | python3 -m json.tool"
  echo ""
  echo "Or run: ./test_zerodha_apis.sh"
  echo ""
else
  echo ""
  echo "⚠️  Session claim may have failed. Check the response above."
  echo "   If session was already claimed, that's okay - you can proceed to test APIs."
  echo ""
fi

