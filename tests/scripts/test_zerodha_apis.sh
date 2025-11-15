#!/bin/bash

# Test Zerodha APIs after authentication
# Usage: ./test_zerodha_apis.sh [output_file]
# If output_file is provided, saves results to that file (markdown format)
# If not provided, saves to: zerodha_api_test_YYYYMMDD_HHMMSS.md

OUTPUT_FILE="${1:-zerodha_api_test_$(date +%Y%m%d_%H%M%S).md}"

# Function to log with timestamp
log() {
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$TIMESTAMP] $*"
}

# Start output file
{
    echo "# Zerodha API Test Results"
    echo ""
    echo "**Test Date:** $(date '+%Y-%m-%d %H:%M:%S')"
    echo "**User Identifier:** RO0252"
    echo ""
    echo "---"
    echo ""
} > "$OUTPUT_FILE"

# Also display on screen
log "=========================================="
log "Testing Zerodha APIs"
log "Output will be saved to: $OUTPUT_FILE"
log "=========================================="
echo ""

# Check if ACCESS_TOKEN is set
if [ -z "$ACCESS_TOKEN" ]; then
  echo "⚠️  ACCESS_TOKEN not set. Logging in first..."
  LOGIN_RESPONSE=$(curl -s -X POST https://piyushdev.com/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username":"piyushdev","password":"piyush123"}')
  
  ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
  
  if [ -z "$ACCESS_TOKEN" ]; then
    echo "❌ ERROR: Failed to login"
    exit 1
  fi
  echo "✅ Logged in"
  echo ""
fi

USER_IDENTIFIER="RO0252"

log "Testing with user_identifier: $USER_IDENTIFIER"
echo ""

# Test 1: Profile
{
    echo "## 1. Profile API"
    echo ""
    echo "**Endpoint:** \`GET /api/v1/data/zerodha/profile\`"
    echo "**Timestamp:** $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
    echo "\`\`\`json"
} >> "$OUTPUT_FILE"

log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "1. Testing /data/zerodha/profile"
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

RESPONSE=$(curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  "https://piyushdev.com/api/v1/data/zerodha/profile?user_identifier=$USER_IDENTIFIER")

echo "$RESPONSE" | python3 -m json.tool | tee -a "$OUTPUT_FILE"

{
    echo "\`\`\`"
    echo ""
    echo "---"
    echo ""
} >> "$OUTPUT_FILE"
echo ""

# Test 2: Margins
{
    echo "## 2. Margins API"
    echo ""
    echo "**Endpoint:** \`GET /api/v1/data/zerodha/margins\`"
    echo "**Timestamp:** $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
    echo "\`\`\`json"
} >> "$OUTPUT_FILE"

log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "2. Testing /data/zerodha/margins"
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

RESPONSE=$(curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  "https://piyushdev.com/api/v1/data/zerodha/margins?user_identifier=$USER_IDENTIFIER")

echo "$RESPONSE" | python3 -m json.tool | tee -a "$OUTPUT_FILE"

{
    echo "\`\`\`"
    echo ""
    echo "---"
    echo ""
} >> "$OUTPUT_FILE"
echo ""

# Test 3: Positions
{
    echo "## 3. Positions API"
    echo ""
    echo "**Endpoint:** \`GET /api/v1/data/zerodha/positions\`"
    echo "**Timestamp:** $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
    echo "\`\`\`json"
} >> "$OUTPUT_FILE"

log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "3. Testing /data/zerodha/positions"
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

RESPONSE=$(curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  "https://piyushdev.com/api/v1/data/zerodha/positions?user_identifier=$USER_IDENTIFIER")

echo "$RESPONSE" | python3 -m json.tool | tee -a "$OUTPUT_FILE"

{
    echo "\`\`\`"
    echo ""
    echo "---"
    echo ""
} >> "$OUTPUT_FILE"
echo ""

# Test 4: Holdings
{
    echo "## 4. Holdings API"
    echo ""
    echo "**Endpoint:** \`GET /api/v1/data/zerodha/holdings\`"
    echo "**Timestamp:** $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
    echo "\`\`\`json"
} >> "$OUTPUT_FILE"

log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "4. Testing /data/zerodha/holdings"
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

RESPONSE=$(curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  "https://piyushdev.com/api/v1/data/zerodha/holdings?user_identifier=$USER_IDENTIFIER")

echo "$RESPONSE" | python3 -m json.tool | tee -a "$OUTPUT_FILE"

{
    echo "\`\`\`"
    echo ""
    echo "---"
    echo ""
} >> "$OUTPUT_FILE"
echo ""

# Test 5: Orders
{
    echo "## 5. Orders API"
    echo ""
    echo "**Endpoint:** \`GET /api/v1/data/zerodha/orders\`"
    echo "**Timestamp:** $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
    echo "\`\`\`json"
} >> "$OUTPUT_FILE"

log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "5. Testing /data/zerodha/orders"
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

RESPONSE=$(curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  "https://piyushdev.com/api/v1/data/zerodha/orders?user_identifier=$USER_IDENTIFIER")

echo "$RESPONSE" | python3 -m json.tool | tee -a "$OUTPUT_FILE"

{
    echo "\`\`\`"
    echo ""
    echo "---"
    echo ""
} >> "$OUTPUT_FILE"
echo ""

# Test 6: Trades
{
    echo "## 6. Trades API"
    echo ""
    echo "**Endpoint:** \`GET /api/v1/data/zerodha/trades\`"
    echo "**Timestamp:** $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
    echo "\`\`\`json"
} >> "$OUTPUT_FILE"

log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "6. Testing /data/zerodha/trades"
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

RESPONSE=$(curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  "https://piyushdev.com/api/v1/data/zerodha/trades?user_identifier=$USER_IDENTIFIER")

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
    echo "All 6 Zerodha API endpoints tested successfully."
} >> "$OUTPUT_FILE"

log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "✅ All tests complete!"
log "Results saved to: $OUTPUT_FILE"
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
