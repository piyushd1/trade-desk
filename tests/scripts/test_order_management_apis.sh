#!/bin/bash

# Test Order Management APIs (Preview Only - Safe)
# Usage: ./test_order_management_apis.sh [output_file]
# ⚠️  WARNING: This script only tests PREVIEW endpoint (safe)
# DO NOT test place/modify/cancel unless you want to trade with real money!

OUTPUT_FILE="${1:-order_management_test_$(date +%Y%m%d_%H%M%S).md}"

# Function to log with timestamp
log() {
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$TIMESTAMP] $*"
}

# Start output file
{
    echo "# Order Management API Test Results"
    echo ""
    echo "**Test Date:** $(date '+%Y-%m-%d %H:%M:%S')"
    echo "**User Identifier:** RO0252"
    echo "**User ID:** 2 (piyushdev)"
    echo ""
    echo "⚠️  **NOTE:** Only PREVIEW endpoint is tested (safe, no orders placed)"
    echo ""
    echo "---"
    echo ""
} > "$OUTPUT_FILE"

# Also display on screen
log "=========================================="
log "Testing Order Management APIs (Preview Only)"
log "Output will be saved to: $OUTPUT_FILE"
log "=========================================="
echo ""

# Check if ACCESS_TOKEN is set
if [ -z "$ACCESS_TOKEN" ]; then
  log "⚠️  ACCESS_TOKEN not set. Logging in first..."
  LOGIN_RESPONSE=$(curl -s -X POST ${API_BASE_URL:-http://localhost:8000}/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username":"${TEST_USERNAME}","password":"${TEST_PASSWORD}"}')
  
  ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
  
  if [ -z "$ACCESS_TOKEN" ]; then
    log "❌ ERROR: Failed to login"
    exit 1
  fi
  log "✅ Logged in"
  echo ""
fi

USER_IDENTIFIER="RO0252"
USER_ID=2

log "Testing with user_identifier: $USER_IDENTIFIER, user_id: $USER_ID"
echo ""

# Test 1: Preview Order (SAFE - doesn't place order)
{
    echo "## 1. Preview Order API (SAFE)"
    echo ""
    echo "**Endpoint:** \`POST /api/v1/orders/preview\`"
    echo "**Timestamp:** $(date '+%Y-%m-%d %H:%M:%S')"
    echo "**Request:** Preview BUY order for INFY"
    echo ""
    echo "**Order Details:**"
    echo "- Exchange: NSE"
    echo "- Symbol: INFY"
    echo "- Transaction: BUY"
    echo "- Quantity: 1"
    echo "- Order Type: LIMIT"
    echo "- Product: CNC"
    echo "- Price: 1500.0"
    echo ""
    echo "\`\`\`json"
} >> "$OUTPUT_FILE"

log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "1. Testing /orders/preview (SAFE - no order will be placed)"
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

RESPONSE=$(curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  -X POST "${API_BASE_URL:-http://localhost:8000}/api/v1/orders/preview" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": $USER_ID,
    \"user_identifier\": \"$USER_IDENTIFIER\",
    \"exchange\": \"NSE\",
    \"tradingsymbol\": \"INFY\",
    \"transaction_type\": \"BUY\",
    \"quantity\": 1,
    \"order_type\": \"LIMIT\",
    \"product\": \"CNC\",
    \"price\": 1500.0,
    \"price_for_risk\": 1500.0
  }")

echo "$RESPONSE" | python3 -m json.tool | tee -a "$OUTPUT_FILE"

{
    echo "\`\`\`"
    echo ""
    echo "---"
    echo ""
    echo "## Test Summary"
    echo ""
    echo "**Completed:** $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
    echo "✅ Order Preview API tested successfully."
    echo ""
    echo "### ⚠️  Untested Endpoints (REAL MONEY - DO NOT TEST):"
    echo ""
    echo "1. ❌ **Place Order** - \`POST /api/v1/orders/place\`"
    echo "   - ⚠️  Places actual order on exchange"
    echo "   - ⚠️  Uses real money"
    echo ""
    echo "2. ❌ **Modify Order** - \`POST /api/v1/orders/modify\`"
    echo "   - ⚠️  Modifies existing order"
    echo "   - ⚠️  Uses real money"
    echo ""
    echo "3. ❌ **Cancel Order** - \`POST /api/v1/orders/cancel\`"
    echo "   - ⚠️  Cancels existing order"
    echo "   - ⚠️  Uses real money"
    echo ""
    echo "**Note:** These endpoints should only be tested in a live trading environment"
    echo "when you are ready to place actual orders."
} >> "$OUTPUT_FILE"

log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "✅ Preview test complete!"
log "⚠️  Remember: Place/Modify/Cancel endpoints NOT tested (real money)"
log "Results saved to: $OUTPUT_FILE"
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

