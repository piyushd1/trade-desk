#!/bin/bash
# OAuth Flow Testing Script

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║           ZERODHA OAUTH FLOW - MANUAL TEST                   ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Step 1: Get login URL
STATE="$1"
if [ -n "$STATE" ]; then
  echo "📋 Step 1: Getting Zerodha login URL for user identifier: $STATE"
  RESPONSE=$(curl -s "${API_BASE_URL:-http://localhost:8000}/api/v1/auth/zerodha/connect?state=$STATE")
else
  echo "📋 Step 1: Getting Zerodha login URL..."
  RESPONSE=$(curl -s ${API_BASE_URL:-http://localhost:8000}/api/v1/auth/zerodha/connect)
fi
LOGIN_URL=$(echo $RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['login_url'])")

echo "✅ Login URL obtained:"
echo "   $LOGIN_URL"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 MANUAL TESTING STEPS:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1. Open this URL in your browser:"
echo "   $LOGIN_URL"
echo ""
echo "2. Login with your Zerodha credentials"
echo ""
echo "3. Click 'Authorize' to grant access"
echo ""
echo "4. You'll be redirected to:"
if [ -n "$STATE" ]; then
  echo "   ${API_BASE_URL:-http://localhost:8000}/api/v1/auth/zerodha/callback?request_token=XXX&status=success&state=$STATE"
else
  echo "   ${API_BASE_URL:-http://localhost:8000}/api/v1/auth/zerodha/callback?request_token=XXX&status=success"
fi
echo ""
echo "5. The page will show your connection status"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🔍 What to look for:"
echo "   • Status: success"
echo "   • User ID: Your Zerodha user ID"
echo "   • Access token: Should be displayed (partially hidden)"
if [ -n "$STATE" ]; then
  echo "   • User identifier: $STATE"
fi
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

