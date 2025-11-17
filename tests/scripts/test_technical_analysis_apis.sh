#!/bin/bash

# Test Technical Analysis APIs
# 
# Usage:
#   export TEST_USERNAME=testuser
#   export TEST_PASSWORD=testpass123
#   export API_BASE_URL=http://localhost:8000  # Optional, defaults to localhost
#   ./test_technical_analysis_apis.sh [output_file]

# Configuration
BASE_URL="${API_BASE_URL:-http://localhost:8000}/api/v1"
OUTPUT_FILE="${1:-technical_analysis_test_$(date +%Y%m%d_%H%M%S).md}"

# Function to log with timestamp
log() {
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$TIMESTAMP] $*"
}

# Start output file
{
    echo "# Technical Analysis API Test Results"
    echo ""
    echo "**Test Date:** $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
    echo "---"
    echo ""
} > "$OUTPUT_FILE"

# Also display on screen
log "=========================================="
log "Testing Technical Analysis APIs"
log "Output will be saved to: $OUTPUT_FILE"
log "=========================================="
echo ""

# Check if ACCESS_TOKEN is set
if [ -z "$ACCESS_TOKEN" ]; then
  log "⚠️  ACCESS_TOKEN not set. Logging in first..."
  
  # Validate credentials are set
  if [ -z "$TEST_USERNAME" ] || [ -z "$TEST_PASSWORD" ]; then
    log "❌ ERROR: TEST_USERNAME and TEST_PASSWORD environment variables must be set"
    exit 1
  fi
  
  LOGIN_RESPONSE=$(curl -s -X POST "${BASE_URL}/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"${TEST_USERNAME}\",\"password\":\"${TEST_PASSWORD}\"}")
  
  ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null)
  
  if [ -z "$ACCESS_TOKEN" ]; then
    log "❌ ERROR: Failed to login"
    exit 1
  fi
  log "✅ Logged in successfully"
  echo ""
fi

# Test 1: List Available Indicators
log "Test 1: List Available Indicators (Public endpoint)"
{
    echo "## Test 1: List Available Indicators"
    echo ""
    echo "**Endpoint:** \`GET /api/v1/technical-analysis/indicators/list\`"
    echo ""
    echo "**Description:** List all available technical indicators (no auth required)"
    echo ""
    echo "**Request:**"
    echo "\`\`\`bash"
    echo "curl \${API_BASE_URL:-http://localhost:8000}/api/v1/technical-analysis/indicators/list"
    echo "\`\`\`"
    echo ""
    echo "**Response:**"
    echo "\`\`\`json"
} >> "$OUTPUT_FILE"

RESPONSE=$(curl -s "${BASE_URL}/technical-analysis/indicators/list")
echo "$RESPONSE" | python3 -m json.tool >> "$OUTPUT_FILE" 2>&1

{
    echo "\`\`\`"
    echo ""
    echo "---"
    echo ""
} >> "$OUTPUT_FILE"

if echo "$RESPONSE" | grep -q "momentum"; then
    log "✅ Test 1 PASSED: Indicator list retrieved"
else
    log "❌ Test 1 FAILED: Could not retrieve indicator list"
fi
echo ""

# Test 2: Compute Specific Indicators (RSI, MACD, Bollinger Bands)
log "Test 2: Compute Specific Indicators (RSI, MACD, Bollinger Bands)"
{
    echo "## Test 2: Compute Specific Indicators"
    echo ""
    echo "**Endpoint:** \`POST /api/v1/technical-analysis/compute\`"
    echo ""
    echo "**Description:** Compute RSI, MACD, and Bollinger Bands for INFY (token: 408065)"
    echo ""
    echo "**Request:**"
    echo "\`\`\`bash"
    echo 'curl -X POST ${API_BASE_URL:-http://localhost:8000}/api/v1/technical-analysis/compute \'
    echo '  -H "Authorization: Bearer $ACCESS_TOKEN" \'
    echo '  -H "Content-Type: application/json" \'
    echo '  -d '"'"'{'
    echo '    "instrument_token": 408065,'
    echo '    "interval": "day",'
    echo '    "indicators": ["rsi", "macd", "bollinger_bands"],'
    echo '    "limit": 50'
    echo '  }'"'"
    echo "\`\`\`"
    echo ""
    echo "**Response:**"
    echo "\`\`\`json"
} >> "$OUTPUT_FILE"

RESPONSE=$(curl -s -X POST "${BASE_URL}/technical-analysis/compute" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "instrument_token": 408065,
    "interval": "day",
    "indicators": ["rsi", "macd", "bollinger_bands"],
    "limit": 50
  }')

echo "$RESPONSE" | python3 -m json.tool >> "$OUTPUT_FILE" 2>&1

{
    echo "\`\`\`"
    echo ""
    echo "---"
    echo ""
} >> "$OUTPUT_FILE"

if echo "$RESPONSE" | grep -q "rsi"; then
    log "✅ Test 2 PASSED: Specific indicators computed"
else
    log "❌ Test 2 FAILED: Could not compute specific indicators"
fi
echo ""

# Test 3: Compute SMA with Custom Periods
log "Test 3: Compute SMA with Custom Periods (20, 50, 200)"
{
    echo "## Test 3: Compute SMA with Custom Periods"
    echo ""
    echo "**Endpoint:** \`POST /api/v1/technical-analysis/compute\`"
    echo ""
    echo "**Description:** Compute SMA with custom periods for RELIANCE (token: 738561)"
    echo ""
    echo "**Request:**"
    echo "\`\`\`bash"
    echo 'curl -X POST ${API_BASE_URL:-http://localhost:8000}/api/v1/technical-analysis/compute \'
    echo '  -H "Authorization: Bearer $ACCESS_TOKEN" \'
    echo '  -H "Content-Type: application/json" \'
    echo '  -d '"'"'{'
    echo '    "instrument_token": 738561,'
    echo '    "interval": "day",'
    echo '    "indicators": ["sma"],'
    echo '    "sma_periods": [20, 50, 200],'
    echo '    "limit": 250'
    echo '  }'"'"
    echo "\`\`\`"
    echo ""
    echo "**Response:**"
    echo "\`\`\`json"
} >> "$OUTPUT_FILE"

RESPONSE=$(curl -s -X POST "${BASE_URL}/technical-analysis/compute" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "instrument_token": 738561,
    "interval": "day",
    "indicators": ["sma"],
    "sma_periods": [20, 50, 200],
    "limit": 250
  }')

echo "$RESPONSE" | python3 -m json.tool >> "$OUTPUT_FILE" 2>&1

{
    echo "\`\`\`"
    echo ""
    echo "---"
    echo ""
} >> "$OUTPUT_FILE"

if echo "$RESPONSE" | grep -q "sma_20"; then
    log "✅ Test 3 PASSED: Custom SMA periods computed"
else
    log "❌ Test 3 FAILED: Could not compute custom SMA periods"
fi
echo ""

# Test 4: Compute All Indicators
log "Test 4: Compute All Indicators (default behavior)"
{
    echo "## Test 4: Compute All Indicators"
    echo ""
    echo "**Endpoint:** \`POST /api/v1/technical-analysis/compute\`"
    echo ""
    echo "**Description:** Compute all available indicators by not specifying indicators parameter"
    echo ""
    echo "**Request:**"
    echo "\`\`\`bash"
    echo 'curl -X POST ${API_BASE_URL:-http://localhost:8000}/api/v1/technical-analysis/compute \'
    echo '  -H "Authorization: Bearer $ACCESS_TOKEN" \'
    echo '  -H "Content-Type: application/json" \'
    echo '  -d '"'"'{'
    echo '    "instrument_token": 408065,'
    echo '    "interval": "day",'
    echo '    "limit": 100'
    echo '  }'"'"
    echo "\`\`\`"
    echo ""
    echo "**Response (first 50 lines):**"
    echo "\`\`\`json"
} >> "$OUTPUT_FILE"

RESPONSE=$(curl -s -X POST "${BASE_URL}/technical-analysis/compute" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "instrument_token": 408065,
    "interval": "day",
    "limit": 100
  }')

echo "$RESPONSE" | python3 -m json.tool | head -50 >> "$OUTPUT_FILE" 2>&1

{
    echo "... (truncated for brevity)"
    echo "\`\`\`"
    echo ""
    echo "---"
    echo ""
} >> "$OUTPUT_FILE"

if echo "$RESPONSE" | grep -q "rsi" && echo "$RESPONSE" | grep -q "macd" && echo "$RESPONSE" | grep -q "atr"; then
    log "✅ Test 4 PASSED: All indicators computed"
else
    log "❌ Test 4 FAILED: Could not compute all indicators"
fi
echo ""

# Test 5: Volume Indicators (VWAP, OBV, MFI)
log "Test 5: Compute Volume Indicators (VWAP, OBV, MFI)"
{
    echo "## Test 5: Compute Volume Indicators"
    echo ""
    echo "**Endpoint:** \`POST /api/v1/technical-analysis/compute\`"
    echo ""
    echo "**Description:** Compute volume-based indicators"
    echo ""
    echo "**Request:**"
    echo "\`\`\`bash"
    echo 'curl -X POST ${API_BASE_URL:-http://localhost:8000}/api/v1/technical-analysis/compute \'
    echo '  -H "Authorization: Bearer $ACCESS_TOKEN" \'
    echo '  -H "Content-Type: application/json" \'
    echo '  -d '"'"'{'
    echo '    "instrument_token": 408065,'
    echo '    "interval": "day",'
    echo '    "indicators": ["vwap", "obv", "mfi"],'
    echo '    "limit": 50'
    echo '  }'"'"
    echo "\`\`\`"
    echo ""
    echo "**Response:**"
    echo "\`\`\`json"
} >> "$OUTPUT_FILE"

RESPONSE=$(curl -s -X POST "${BASE_URL}/technical-analysis/compute" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "instrument_token": 408065,
    "interval": "day",
    "indicators": ["vwap", "obv", "mfi"],
    "limit": 50
  }')

echo "$RESPONSE" | python3 -m json.tool >> "$OUTPUT_FILE" 2>&1

{
    echo "\`\`\`"
    echo ""
    echo "---"
    echo ""
} >> "$OUTPUT_FILE"

if echo "$RESPONSE" | grep -q "vwap"; then
    log "✅ Test 5 PASSED: Volume indicators computed"
else
    log "❌ Test 5 FAILED: Could not compute volume indicators"
fi
echo ""

# Test 6: Error Case - Invalid Instrument Token
log "Test 6: Error Case - Invalid Instrument Token"
{
    echo "## Test 6: Error Case - Invalid Instrument Token"
    echo ""
    echo "**Endpoint:** \`POST /api/v1/technical-analysis/compute\`"
    echo ""
    echo "**Description:** Test error handling with non-existent instrument"
    echo ""
    echo "**Request:**"
    echo "\`\`\`bash"
    echo 'curl -X POST ${API_BASE_URL:-http://localhost:8000}/api/v1/technical-analysis/compute \'
    echo '  -H "Authorization: Bearer $ACCESS_TOKEN" \'
    echo '  -H "Content-Type: application/json" \'
    echo '  -d '"'"'{'
    echo '    "instrument_token": 999999999,'
    echo '    "interval": "day",'
    echo '    "indicators": ["rsi"],'
    echo '    "limit": 50'
    echo '  }'"'"
    echo "\`\`\`"
    echo ""
    echo "**Response:**"
    echo "\`\`\`json"
} >> "$OUTPUT_FILE"

RESPONSE=$(curl -s -X POST "${BASE_URL}/technical-analysis/compute" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "instrument_token": 999999999,
    "interval": "day",
    "indicators": ["rsi"],
    "limit": 50
  }')

echo "$RESPONSE" | python3 -m json.tool >> "$OUTPUT_FILE" 2>&1

{
    echo "\`\`\`"
    echo ""
    echo "---"
    echo ""
} >> "$OUTPUT_FILE"

if echo "$RESPONSE" | grep -q "404"; then
    log "✅ Test 6 PASSED: Error handled correctly (404)"
else
    log "❌ Test 6 FAILED: Error not handled properly"
fi
echo ""

# Summary
log "=========================================="
log "Test Complete!"
log "Results saved to: $OUTPUT_FILE"
log "=========================================="

{
    echo "## Test Summary"
    echo ""
    echo "**Total Tests:** 6"
    echo "**Date:** $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
    echo "| Test | Description | Status |"
    echo "|------|-------------|--------|"
    echo "| 1 | List Available Indicators | See above |"
    echo "| 2 | Compute Specific Indicators | See above |"
    echo "| 3 | Custom SMA Periods | See above |"
    echo "| 4 | Compute All Indicators | See above |"
    echo "| 5 | Volume Indicators | See above |"
    echo "| 6 | Error Handling | See above |"
    echo ""
    echo "---"
    echo ""
    echo "**Note:** Requires historical data to be stored in database first."
    echo "Use \`/data/zerodha/data/historical/fetch\` to fetch and store historical data."
} >> "$OUTPUT_FILE"

echo ""
log "📊 View the detailed results in: $OUTPUT_FILE"

