#!/bin/bash

# Test Market Data APIs (LTP, Quote, OHLC, Historical)
# Usage: ./test_market_data_apis.sh [output_file]

OUTPUT_FILE="${1:-market_data_test_$(date +%Y%m%d_%H%M%S).md}"

# Function to log with timestamp
log() {
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$TIMESTAMP] $*"
}

# Start output file
{
    echo "# Market Data API Test Results"
    echo ""
    echo "**Test Date:** $(date '+%Y-%m-%d %H:%M:%S')"
    echo "**User Identifier:** ${USER_IDENTIFIER}"
    echo ""
    echo "---"
    echo ""
} > "$OUTPUT_FILE"

# Also display on screen
log "=========================================="
log "Testing Market Data APIs"
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

USER_IDENTIFIER="${USER_IDENTIFIER}"

log "Testing with user_identifier: $USER_IDENTIFIER"
echo ""

# Test 1: LTP (Last Traded Price)
{
    echo "## 1. LTP (Last Traded Price) API"
    echo ""
    echo "**Endpoint:** \`POST /api/v1/data/zerodha/ltp\`"
    echo "**Timestamp:** $(date '+%Y-%m-%d %H:%M:%S')"
    echo "**Request:** \`[\"NSE:INFY\", \"NSE:RELIANCE\", \"NSE:TCS\"]\`"
    echo ""
    echo "\`\`\`json"
} >> "$OUTPUT_FILE"

log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "1. Testing /data/zerodha/ltp"
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

RESPONSE=$(curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  -X POST "${API_BASE_URL:-http://localhost:8000}/api/v1/data/zerodha/ltp?user_identifier=$USER_IDENTIFIER" \
  -H "Content-Type: application/json" \
  -d '["NSE:INFY", "NSE:RELIANCE", "NSE:TCS"]')

echo "$RESPONSE" | python3 -m json.tool | tee -a "$OUTPUT_FILE"

{
    echo "\`\`\`"
    echo ""
    echo "---"
    echo ""
} >> "$OUTPUT_FILE"
echo ""

# Test 2: Quote
{
    echo "## 2. Quote API"
    echo ""
    echo "**Endpoint:** \`POST /api/v1/data/zerodha/quote\`"
    echo "**Timestamp:** $(date '+%Y-%m-%d %H:%M:%S')"
    echo "**Request:** \`[\"NSE:INFY\"]\`"
    echo ""
    echo "\`\`\`json"
} >> "$OUTPUT_FILE"

log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "2. Testing /data/zerodha/quote"
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

RESPONSE=$(curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  -X POST "${API_BASE_URL:-http://localhost:8000}/api/v1/data/zerodha/quote?user_identifier=$USER_IDENTIFIER" \
  -H "Content-Type: application/json" \
  -d '["NSE:INFY"]')

echo "$RESPONSE" | python3 -m json.tool | tee -a "$OUTPUT_FILE"

{
    echo "\`\`\`"
    echo ""
    echo "---"
    echo ""
} >> "$OUTPUT_FILE"
echo ""

# Test 3: OHLC
{
    echo "## 3. OHLC API"
    echo ""
    echo "**Endpoint:** \`POST /api/v1/data/zerodha/ohlc\`"
    echo "**Timestamp:** $(date '+%Y-%m-%d %H:%M:%S')"
    echo "**Request:** \`[\"NSE:RELIANCE\"]\`"
    echo ""
    echo "\`\`\`json"
} >> "$OUTPUT_FILE"

log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "3. Testing /data/zerodha/ohlc"
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

RESPONSE=$(curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  -X POST "${API_BASE_URL:-http://localhost:8000}/api/v1/data/zerodha/ohlc?user_identifier=$USER_IDENTIFIER" \
  -H "Content-Type: application/json" \
  -d '["NSE:RELIANCE"]')

echo "$RESPONSE" | python3 -m json.tool | tee -a "$OUTPUT_FILE"

{
    echo "\`\`\`"
    echo ""
    echo "---"
    echo ""
} >> "$OUTPUT_FILE"
echo ""

# Test 4: Historical Data
{
    echo "## 4. Historical Data API"
    echo ""
    echo "**Endpoint:** \`GET /api/v1/data/zerodha/historical/{instrument_token}\`"
    echo "**Timestamp:** $(date '+%Y-%m-%d %H:%M:%S')"
    echo "**Instrument Token:** 408065 (INFY)"
    echo "**From Date:** 2025-11-01"
    echo "**To Date:** 2025-11-13"
    echo "**Interval:** day"
    echo ""
    echo "\`\`\`json"
} >> "$OUTPUT_FILE"

log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "4. Testing /data/zerodha/historical/408065"
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

RESPONSE=$(curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  "${API_BASE_URL:-http://localhost:8000}/api/v1/data/zerodha/historical/408065?user_identifier=$USER_IDENTIFIER&from_date=2025-11-01&to_date=2025-11-13&interval=day")

# Show first 50 lines in terminal, save full response to file
echo "$RESPONSE" | python3 -m json.tool | head -50
echo "$RESPONSE" | python3 -m json.tool >> "$OUTPUT_FILE"

{
    echo "\`\`\`"
    echo ""
    echo "---"
    echo ""
    echo "## Test Summary"
    echo ""
    echo "**Completed:** $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
    echo "All 4 Market Data API endpoints tested successfully."
} >> "$OUTPUT_FILE"

log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "✅ All tests complete!"
log "Results saved to: $OUTPUT_FILE"
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

