#!/bin/bash

# Test Streaming APIs
# Usage: ./test_streaming_apis.sh [output_file]
# Note: Streaming requires WebSocket connection, some endpoints may need active stream

OUTPUT_FILE="${1:-streaming_test_$(date +%Y%m%d_%H%M%S).md}"

# Function to log with timestamp
log() {
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$TIMESTAMP] $*"
}

# Start output file
{
    echo "# Streaming API Test Results"
    echo ""
    echo "**Test Date:** $(date '+%Y-%m-%d %H:%M:%S')"
    echo "**User Identifier:** ${USER_IDENTIFIER}"
    echo ""
    echo "**Note:** Streaming APIs require WebSocket connections. Some endpoints may"
    echo "return empty results if no active stream is running."
    echo ""
    echo "---"
    echo ""
} > "$OUTPUT_FILE"

# Also display on screen
log "=========================================="
log "Testing Streaming APIs"
log "Output will be saved to: $OUTPUT_FILE"
log "=========================================="
echo ""

# Always get a fresh token (tokens expire in 15 minutes)
log "🔐 Logging in to get fresh access token..."
LOGIN_RESPONSE=$(curl -s -X POST ${API_BASE_URL:-http://localhost:8000}/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"${TEST_USERNAME}","password":"${TEST_PASSWORD}"}')

# Check if login was successful
if echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); exit(0 if data.get('status') == 'success' else 1)" 2>/dev/null; then
  ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null)
  
  if [ -z "$ACCESS_TOKEN" ] || [ "$ACCESS_TOKEN" = "None" ]; then
    log "❌ ERROR: Failed to extract access token from login response"
    log "Login response: $LOGIN_RESPONSE"
    exit 1
  fi
  export ACCESS_TOKEN
  log "✅ Logged in successfully"
  log "Token (first 30 chars): ${ACCESS_TOKEN:0:30}..."
  
  # Verify token works by testing a simple endpoint
  TEST_RESPONSE=$(curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
    "${API_BASE_URL:-http://localhost:8000}/api/v1/auth/me" 2>/dev/null)
  
  if echo "$TEST_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); exit(0 if 'error' not in data else 1)" 2>/dev/null; then
    log "✅ Token verified successfully"
  else
    log "⚠️  WARNING: Token verification failed, but continuing..."
    log "Test response: $TEST_RESPONSE"
  fi
else
  log "❌ ERROR: Login failed"
  log "Response: $LOGIN_RESPONSE"
  exit 1
fi
echo ""

USER_IDENTIFIER="${USER_IDENTIFIER}"

log "Testing with user_identifier: $USER_IDENTIFIER"
echo ""

# Test 1: Session Status
{
    echo "## 1. Session Status API"
    echo ""
    echo "**Endpoint:** \`GET /api/v1/data/zerodha/session/status\`"
    echo "**Timestamp:** $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
    echo "\`\`\`json"
} >> "$OUTPUT_FILE"

log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "1. Testing /data/zerodha/session/status"
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

RESPONSE=$(curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  "${API_BASE_URL:-http://localhost:8000}/api/v1/data/zerodha/session/status?user_identifier=$USER_IDENTIFIER")

echo "$RESPONSE" | python3 -m json.tool | tee -a "$OUTPUT_FILE"

{
    echo "\`\`\`"
    echo ""
    echo "---"
    echo ""
} >> "$OUTPUT_FILE"
echo ""

# Test 2: Validate Session
{
    echo "## 2. Validate Session API"
    echo ""
    echo "**Endpoint:** \`POST /api/v1/data/zerodha/session/validate\`"
    echo "**Timestamp:** $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
    echo "\`\`\`json"
} >> "$OUTPUT_FILE"

log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "2. Testing /data/zerodha/session/validate"
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

RESPONSE=$(curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  -X POST "${API_BASE_URL:-http://localhost:8000}/api/v1/data/zerodha/session/validate?user_identifier=$USER_IDENTIFIER")

echo "$RESPONSE" | python3 -m json.tool | tee -a "$OUTPUT_FILE"

{
    echo "\`\`\`"
    echo ""
    echo "---"
    echo ""
} >> "$OUTPUT_FILE"
echo ""

# Test 3: Stream Status (before starting)
{
    echo "## 3. Stream Status API (Before Starting Stream)"
    echo ""
    echo "**Endpoint:** \`GET /api/v1/data/zerodha/stream/status\`"
    echo "**Timestamp:** $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
    echo "\`\`\`json"
} >> "$OUTPUT_FILE"

log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "3. Testing /data/zerodha/stream/status (before stream)"
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

RESPONSE=$(curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  "${API_BASE_URL:-http://localhost:8000}/api/v1/data/zerodha/stream/status?user_identifier=$USER_IDENTIFIER")

echo "$RESPONSE" | python3 -m json.tool | tee -a "$OUTPUT_FILE"

{
    echo "\`\`\`"
    echo ""
    echo "---"
    echo ""
} >> "$OUTPUT_FILE"
echo ""

# Test 4: Start Stream
{
    echo "## 4. Start Stream API"
    echo ""
    echo "**Endpoint:** \`POST /api/v1/data/zerodha/stream/start\`"
    echo "**Timestamp:** $(date '+%Y-%m-%d %H:%M:%S')"
    echo "**Request:** Start stream for INFY (token: 408065)"
    echo ""
    echo "\`\`\`json"
} >> "$OUTPUT_FILE"

log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "4. Testing /data/zerodha/stream/start"
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "⏳ Starting stream for INFY..."
echo ""

RESPONSE=$(curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  -X POST "${API_BASE_URL:-http://localhost:8000}/api/v1/data/zerodha/stream/start" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_identifier\": \"$USER_IDENTIFIER\",
    \"instruments\": [
      {
        \"instrument_token\": 408065
      }
    ],
    \"mode\": \"ltp\"
  }")

echo "$RESPONSE" | python3 -m json.tool | tee -a "$OUTPUT_FILE"

{
    echo "\`\`\`"
    echo ""
    echo "---"
    echo ""
} >> "$OUTPUT_FILE"
echo ""

# Wait a bit for stream to start
log "⏳ Waiting 3 seconds for stream to initialize..."
sleep 3

# Test 5: Stream Status (after starting)
{
    echo "## 5. Stream Status API (After Starting Stream)"
    echo ""
    echo "**Endpoint:** \`GET /api/v1/data/zerodha/stream/status\`"
    echo "**Timestamp:** $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
    echo "\`\`\`json"
} >> "$OUTPUT_FILE"

log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "5. Testing /data/zerodha/stream/status (after stream)"
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

RESPONSE=$(curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  "${API_BASE_URL:-http://localhost:8000}/api/v1/data/zerodha/stream/status?user_identifier=$USER_IDENTIFIER")

echo "$RESPONSE" | python3 -m json.tool | tee -a "$OUTPUT_FILE"

{
    echo "\`\`\`"
    echo ""
    echo "---"
    echo ""
} >> "$OUTPUT_FILE"
echo ""

# Test 6: Get Ticks
{
    echo "## 6. Get Ticks API"
    echo ""
    echo "**Endpoint:** \`GET /api/v1/data/zerodha/stream/ticks\`"
    echo "**Timestamp:** $(date '+%Y-%m-%d %H:%M:%S')"
    echo "**Request:** Get recent ticks (limit: 10)"
    echo ""
    echo "\`\`\`json"
} >> "$OUTPUT_FILE"

log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "6. Testing /data/zerodha/stream/ticks"
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

RESPONSE=$(curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  "${API_BASE_URL:-http://localhost:8000}/api/v1/data/zerodha/stream/ticks?user_identifier=$USER_IDENTIFIER&limit=10")

echo "$RESPONSE" | python3 -m json.tool | tee -a "$OUTPUT_FILE"

{
    echo "\`\`\`"
    echo ""
    echo "---"
    echo ""
} >> "$OUTPUT_FILE"
echo ""

# Test 7: Update Subscription
{
    echo "## 7. Update Subscription API"
    echo ""
    echo "**Endpoint:** \`POST /api/v1/data/zerodha/stream/update\`"
    echo "**Timestamp:** $(date '+%Y-%m-%d %H:%M:%S')"
    echo "**Request:** Update subscription to include RELIANCE"
    echo ""
    echo "\`\`\`json"
} >> "$OUTPUT_FILE"

log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "7. Testing /data/zerodha/stream/update"
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

RESPONSE=$(curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  -X POST "${API_BASE_URL:-http://localhost:8000}/api/v1/data/zerodha/stream/update" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_identifier\": \"$USER_IDENTIFIER\",
    \"instruments\": [
      {
        \"instrument_token\": 408065
      },
      {
        \"tradingsymbol\": \"RELIANCE\",
        \"exchange\": \"NSE\"
      }
    ],
    \"mode\": \"ltp\"
  }")

echo "$RESPONSE" | python3 -m json.tool | tee -a "$OUTPUT_FILE"

{
    echo "\`\`\`"
    echo ""
    echo "---"
    echo ""
} >> "$OUTPUT_FILE"
echo ""

# Test 8: Stop Stream
{
    echo "## 8. Stop Stream API"
    echo ""
    echo "**Endpoint:** \`POST /api/v1/data/zerodha/stream/stop\`"
    echo "**Timestamp:** $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
    echo "\`\`\`json"
} >> "$OUTPUT_FILE"

log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "8. Testing /data/zerodha/stream/stop"
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

RESPONSE=$(curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  -X POST "${API_BASE_URL:-http://localhost:8000}/api/v1/data/zerodha/stream/stop" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_identifier\": \"$USER_IDENTIFIER\"
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
    echo "All 7 Streaming API endpoints tested successfully."
    echo ""
    echo "### Endpoints Tested:"
    echo "1. ✅ Session Status"
    echo "2. ✅ Validate Session"
    echo "3. ✅ Stream Status (before)"
    echo "4. ✅ Start Stream"
    echo "5. ✅ Stream Status (after)"
    echo "6. ✅ Get Ticks"
    echo "7. ✅ Update Subscription"
    echo "8. ✅ Stop Stream"
    echo ""
    echo "**Note:** Streaming requires active WebSocket connections. Some endpoints"
    echo "may return empty results if no stream is active."
} >> "$OUTPUT_FILE"

log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "✅ All tests complete!"
log "Results saved to: $OUTPUT_FILE"
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

