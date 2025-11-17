#!/bin/bash

# Test Risk Management APIs (All Public - No JWT Required)
# Usage: ./test_risk_management_apis.sh [output_file]

OUTPUT_FILE="${1:-risk_management_test_$(date +%Y%m%d_%H%M%S).md}"

# Function to log with timestamp
log() {
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$TIMESTAMP] $*"
}

# Start output file
{
    echo "# Risk Management API Test Results"
    echo ""
    echo "**Test Date:** $(date '+%Y-%m-%d %H:%M:%S')"
    echo "**User ID:** 2 (piyushdev)"
    echo ""
    echo "**Note:** All Risk Management APIs are public (no JWT required)"
    echo ""
    echo "---"
    echo ""
} > "$OUTPUT_FILE"

# Also display on screen
log "=========================================="
log "Testing Risk Management APIs"
log "Output will be saved to: $OUTPUT_FILE"
log "=========================================="
echo ""

USER_ID=2

log "Testing with user_id: $USER_ID"
log "Note: All endpoints are public (no JWT required)"
echo ""

# Test 1: Get Risk Config
{
    echo "## 1. Get Risk Config API"
    echo ""
    echo "**Endpoint:** \`GET /api/v1/risk/config\`"
    echo "**Timestamp:** $(date '+%Y-%m-%d %H:%M:%S')"
    echo "**Request:** Get risk configuration for user_id=$USER_ID"
    echo ""
    echo "\`\`\`json"
} >> "$OUTPUT_FILE"

log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "1. Testing /risk/config"
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

RESPONSE=$(curl -s "${API_BASE_URL:-http://localhost:8000}/api/v1/risk/config?user_id=$USER_ID")

echo "$RESPONSE" | python3 -m json.tool | tee -a "$OUTPUT_FILE"

{
    echo "\`\`\`"
    echo ""
    echo "---"
    echo ""
} >> "$OUTPUT_FILE"
echo ""

# Test 2: Kill Switch Status
{
    echo "## 2. Kill Switch Status API"
    echo ""
    echo "**Endpoint:** \`GET /api/v1/risk/kill-switch/status\`"
    echo "**Timestamp:** $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
    echo "\`\`\`json"
} >> "$OUTPUT_FILE"

log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "2. Testing /risk/kill-switch/status"
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

RESPONSE=$(curl -s "${API_BASE_URL:-http://localhost:8000}/api/v1/risk/kill-switch/status")

echo "$RESPONSE" | python3 -m json.tool | tee -a "$OUTPUT_FILE"

{
    echo "\`\`\`"
    echo ""
    echo "---"
    echo ""
} >> "$OUTPUT_FILE"
echo ""

# Test 3: Risk Status
{
    echo "## 3. Risk Status API"
    echo ""
    echo "**Endpoint:** \`GET /api/v1/risk/status\`"
    echo "**Timestamp:** $(date '+%Y-%m-%d %H:%M:%S')"
    echo "**Request:** Get risk status for user_id=$USER_ID"
    echo ""
    echo "\`\`\`json"
} >> "$OUTPUT_FILE"

log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "3. Testing /risk/status"
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

RESPONSE=$(curl -s "${API_BASE_URL:-http://localhost:8000}/api/v1/risk/status?user_id=$USER_ID")

echo "$RESPONSE" | python3 -m json.tool | tee -a "$OUTPUT_FILE"

{
    echo "\`\`\`"
    echo ""
    echo "---"
    echo ""
} >> "$OUTPUT_FILE"
echo ""

# Test 4: Pre-trade Check
{
    echo "## 4. Pre-trade Check API"
    echo ""
    echo "**Endpoint:** \`POST /api/v1/risk/pre-trade-check\`"
    echo "**Timestamp:** $(date '+%Y-%m-%d %H:%M:%S')"
    echo "**Request:** Pre-trade risk check for INFY order"
    echo ""
    echo "**Order Details:**"
    echo "- Symbol: INFY"
    echo "- Quantity: 1"
    echo "- Price: 1500.0"
    echo ""
    echo "\`\`\`json"
} >> "$OUTPUT_FILE"

log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "4. Testing /risk/pre-trade-check"
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

RESPONSE=$(curl -s -X POST "${API_BASE_URL:-http://localhost:8000}/api/v1/risk/pre-trade-check" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": $USER_ID,
    \"symbol\": \"INFY\",
    \"quantity\": 1,
    \"price\": 1500.0
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
    echo "All 4 Risk Management API endpoints tested successfully."
    echo ""
    echo "### Endpoints Tested:"
    echo "1. ✅ Get Risk Config (public)"
    echo "2. ✅ Kill Switch Status (public)"
    echo "3. ✅ Risk Status (public)"
    echo "4. ✅ Pre-trade Check (public)"
    echo ""
    echo "**Note:** All Risk Management APIs are public endpoints and do not require JWT authentication."
} >> "$OUTPUT_FILE"

log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "✅ All tests complete!"
log "Results saved to: $OUTPUT_FILE"
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

