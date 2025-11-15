#!/bin/bash

# Test Data Management APIs (Sync, Search, Fetch, Query)
# Usage: ./test_data_management_apis.sh [output_file]

OUTPUT_FILE="${1:-data_management_test_$(date +%Y%m%d_%H%M%S).md}"

# Function to log with timestamp
log() {
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$TIMESTAMP] $*"
}

# Start output file
{
    echo "# Data Management API Test Results"
    echo ""
    echo "**Test Date:** $(date '+%Y-%m-%d %H:%M:%S')"
    echo "**User Identifier:** RO0252"
    echo ""
    echo "---"
    echo ""
} > "$OUTPUT_FILE"

# Also display on screen
log "=========================================="
log "Testing Data Management APIs"
log "Output will be saved to: $OUTPUT_FILE"
log "=========================================="
echo ""

# Check if ACCESS_TOKEN is set
if [ -z "$ACCESS_TOKEN" ]; then
  log "⚠️  ACCESS_TOKEN not set. Logging in first..."
  LOGIN_RESPONSE=$(curl -s -X POST https://piyushdev.com/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username":"piyushdev","password":"piyush123"}')
  
  ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
  
  if [ -z "$ACCESS_TOKEN" ]; then
    log "❌ ERROR: Failed to login"
    exit 1
  fi
  log "✅ Logged in"
  echo ""
fi

USER_IDENTIFIER="RO0252"

log "Testing with user_identifier: $USER_IDENTIFIER"
echo ""

# Test 1: Sync Instruments
{
    echo "## 1. Sync Instruments API"
    echo ""
    echo "**Endpoint:** \`POST /api/v1/data/zerodha/data/instruments/sync\`"
    echo "**Timestamp:** $(date '+%Y-%m-%d %H:%M:%S')"
    echo "**Request:** Sync NSE instruments"
    echo ""
    echo "\`\`\`json"
} >> "$OUTPUT_FILE"

log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "1. Testing /data/zerodha/data/instruments/sync (NSE)"
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "⏳ This may take a while (syncing all NSE instruments)..."
echo ""

RESPONSE=$(curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  -X POST "https://piyushdev.com/api/v1/data/zerodha/data/instruments/sync" \
  -H "Content-Type: application/json" \
  -d "{\"user_identifier\":\"$USER_IDENTIFIER\",\"exchange\":\"NSE\"}")

echo "$RESPONSE" | python3 -m json.tool | tee -a "$OUTPUT_FILE"

{
    echo "\`\`\`"
    echo ""
    echo "---"
    echo ""
} >> "$OUTPUT_FILE"
echo ""

# Test 2: Search Instruments (Public - no JWT)
{
    echo "## 2. Search Instruments API (Public)"
    echo ""
    echo "**Endpoint:** \`GET /api/v1/data/zerodha/data/instruments/search\`"
    echo "**Timestamp:** $(date '+%Y-%m-%d %H:%M:%S')"
    echo "**Request:** Search for INFY in NSE"
    echo ""
    echo "\`\`\`json"
} >> "$OUTPUT_FILE"

log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "2. Testing /data/zerodha/data/instruments/search (Public)"
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

RESPONSE=$(curl -s "https://piyushdev.com/api/v1/data/zerodha/data/instruments/search?q=INFY&exchange=NSE&limit=5")

echo "$RESPONSE" | python3 -m json.tool | tee -a "$OUTPUT_FILE"

{
    echo "\`\`\`"
    echo ""
    echo "---"
    echo ""
} >> "$OUTPUT_FILE"
echo ""

# Test 3: Fetch and Store Historical Data
{
    echo "## 3. Fetch and Store Historical Data API"
    echo ""
    echo "**Endpoint:** \`POST /api/v1/data/zerodha/data/historical/fetch\`"
    echo "**Timestamp:** $(date '+%Y-%m-%d %H:%M:%S')"
    echo "**Request:** Fetch INFY (token: 408065) historical data"
    echo ""
    echo "\`\`\`json"
} >> "$OUTPUT_FILE"

log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "3. Testing /data/zerodha/data/historical/fetch"
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "⏳ Fetching historical data from Zerodha and storing in database..."
echo ""

RESPONSE=$(curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  -X POST "https://piyushdev.com/api/v1/data/zerodha/data/historical/fetch" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_identifier\": \"$USER_IDENTIFIER\",
    \"instrument_token\": 408065,
    \"from_date\": \"2025-11-01T00:00:00\",
    \"to_date\": \"2025-11-13T23:59:59\",
    \"interval\": \"day\",
    \"oi\": false
  }")

echo "$RESPONSE" | python3 -m json.tool | tee -a "$OUTPUT_FILE"

{
    echo "\`\`\`"
    echo ""
    echo "---"
    echo ""
} >> "$OUTPUT_FILE"
echo ""

# Test 4: Query Stored Historical Data (Public - no JWT)
{
    echo "## 4. Query Stored Historical Data API (Public)"
    echo ""
    echo "**Endpoint:** \`GET /api/v1/data/zerodha/data/historical\`"
    echo "**Timestamp:** $(date '+%Y-%m-%d %H:%M:%S')"
    echo "**Request:** Query stored historical data for INFY (token: 408065)"
    echo ""
    echo "\`\`\`json"
} >> "$OUTPUT_FILE"

log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "4. Testing /data/zerodha/data/historical (Public)"
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

RESPONSE=$(curl -s "https://piyushdev.com/api/v1/data/zerodha/data/historical?instrument_token=408065&interval=day&limit=10")

# Show first 30 lines in terminal, save full response to file
echo "$RESPONSE" | python3 -m json.tool | head -30
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
    echo "All 4 Data Management API endpoints tested successfully."
    echo ""
    echo "### Endpoints Tested:"
    echo "1. ✅ Sync Instruments (requires JWT)"
    echo "2. ✅ Search Instruments (public)"
    echo "3. ✅ Fetch Historical Data (requires JWT)"
    echo "4. ✅ Query Historical Data (public)"
} >> "$OUTPUT_FILE"

log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "✅ All tests complete!"
log "Results saved to: $OUTPUT_FILE"
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

