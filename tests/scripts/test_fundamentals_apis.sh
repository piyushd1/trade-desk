#!/bin/bash

# ================================================
# Fundamentals API Test Script
# ================================================
# Tests all fundamentals-related endpoints
# 
# Usage:
#   export TEST_USERNAME=testuser
#   export TEST_PASSWORD=testpass123
#   export API_BASE_URL=http://localhost:8000  # Optional, defaults to localhost
#   ./test_fundamentals_apis.sh
# ================================================

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BASE_URL="${API_BASE_URL:-http://localhost:8000}/api/v1"
OUTPUT_DIR="$(dirname "$0")"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_FILE="${OUTPUT_DIR}/fundamentals_test_${TIMESTAMP}.md"

# Test credentials from environment variables
USERNAME="${TEST_USERNAME:?Error: TEST_USERNAME environment variable not set. Please set it before running this script.}"
PASSWORD="${TEST_PASSWORD:?Error: TEST_PASSWORD environment variable not set. Please set it before running this script.}"

# Test data
TEST_INSTRUMENT_TOKEN=408065  # INFY

# ================================================
# Helper Functions
# ================================================

log() {
    echo -e "${BLUE}[$(date +%H:%M:%S)]${NC} $1" | tee -a "$OUTPUT_FILE"
}

log_success() {
    echo -e "${GREEN}✓${NC} $1" | tee -a "$OUTPUT_FILE"
}

log_error() {
    echo -e "${RED}✗${NC} $1" | tee -a "$OUTPUT_FILE"
}

log_warning() {
    echo -e "${YELLOW}⚠${NC} $1" | tee -a "$OUTPUT_FILE"
}

# ================================================
# Initialization
# ================================================

echo "================================================" | tee "$OUTPUT_FILE"
echo "Fundamentals API Test Suite" | tee -a "$OUTPUT_FILE"
echo "Started: $(date)" | tee -a "$OUTPUT_FILE"
echo "================================================" | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

# ================================================
# Step 1: Authentication
# ================================================

log "Step 1: Authenticating..."
echo "" | tee -a "$OUTPUT_FILE"

LOGIN_RESPONSE=$(curl -s -X POST "${BASE_URL}/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"${USERNAME}\",\"password\":\"${PASSWORD}\"}")

ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null)

if [ -z "$ACCESS_TOKEN" ]; then
    log_error "Authentication failed"
    echo "Response: $LOGIN_RESPONSE" | tee -a "$OUTPUT_FILE"
    exit 1
fi

log_success "Authentication successful"
echo "" | tee -a "$OUTPUT_FILE"

# ================================================
# Step 2: Symbol Mapping Tests
# ================================================

log "Step 2: Testing Symbol Mapping Endpoints..."
echo "" | tee -a "$OUTPUT_FILE"

# Test 2.1: Get symbol mapping for a stock
log "Test 2.1: Get symbol mapping for INFY (${TEST_INSTRUMENT_TOKEN})"
MAPPING_RESPONSE=$(curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  "${BASE_URL}/fundamentals/mapping/${TEST_INSTRUMENT_TOKEN}")

echo "Response:" | tee -a "$OUTPUT_FILE"
echo "$MAPPING_RESPONSE" | python3 -m json.tool 2>&1 | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

if echo "$MAPPING_RESPONSE" | grep -q "yfinance_symbol"; then
    log_success "Symbol mapping retrieved successfully"
else
    log_warning "Symbol mapping may not exist yet"
fi
echo "" | tee -a "$OUTPUT_FILE"

# Test 2.2: Sync symbol mappings for NSE
log "Test 2.2: Sync symbol mappings for NSE (limit 10)"
SYNC_RESPONSE=$(curl -s -X POST -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"exchange": "NSE", "limit": 10}' \
  "${BASE_URL}/fundamentals/mapping/sync")

echo "Response:" | tee -a "$OUTPUT_FILE"
echo "$SYNC_RESPONSE" | python3 -m json.tool 2>&1 | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

if echo "$SYNC_RESPONSE" | grep -q "created"; then
    log_success "Symbol mapping sync completed"
else
    log_error "Symbol mapping sync failed"
fi
echo "" | tee -a "$OUTPUT_FILE"

# ================================================
# Step 3: Fundamentals Data Tests
# ================================================

log "Step 3: Testing Fundamentals Data Endpoints..."
echo "" | tee -a "$OUTPUT_FILE"

# Test 3.1: Get fundamentals (cached)
log "Test 3.1: Get fundamentals for INFY (cached)"
FUNDAMENTALS_RESPONSE=$(curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  "${BASE_URL}/fundamentals/${TEST_INSTRUMENT_TOKEN}")

echo "Response:" | tee -a "$OUTPUT_FILE"
echo "$FUNDAMENTALS_RESPONSE" | python3 -m json.tool 2>&1 | head -40 | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

if echo "$FUNDAMENTALS_RESPONSE" | grep -q "instrument_token"; then
    log_success "Fundamentals retrieved successfully"
else
    log_warning "Fundamentals not available (may need fresh fetch or data not available)"
fi
echo "" | tee -a "$OUTPUT_FILE"

# Test 3.2: Force fetch fundamentals
log "Test 3.2: Force fetch fresh fundamentals"
log_warning "Note: This may take a few seconds due to rate limiting..."
FORCE_FETCH_RESPONSE=$(curl -s -X POST -H "Authorization: Bearer $ACCESS_TOKEN" \
  "${BASE_URL}/fundamentals/fetch?instrument_token=${TEST_INSTRUMENT_TOKEN}&include_analyst=false")

echo "Response:" | tee -a "$OUTPUT_FILE"
echo "$FORCE_FETCH_RESPONSE" | python3 -m json.tool 2>&1 | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

if echo "$FORCE_FETCH_RESPONSE" | grep -q "fundamentals_updated"; then
    log_success "Force fetch completed"
else
    log_warning "Force fetch may have failed (rate limiting or data unavailable)"
fi
echo "" | tee -a "$OUTPUT_FILE"

# ================================================
# Step 4: Analyst Data Tests
# ================================================

log "Step 4: Testing Analyst Data Endpoints..."
echo "" | tee -a "$OUTPUT_FILE"

# Test 4.1: Get analyst data
log "Test 4.1: Get analyst data for INFY"
ANALYST_RESPONSE=$(curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  "${BASE_URL}/fundamentals/${TEST_INSTRUMENT_TOKEN}/analyst")

echo "Response:" | tee -a "$OUTPUT_FILE"
echo "$ANALYST_RESPONSE" | python3 -m json.tool 2>&1 | head -30 | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

if echo "$ANALYST_RESPONSE" | grep -q "recommendation"; then
    log_success "Analyst data retrieved successfully"
else
    log_warning "Analyst data may not be available for this stock"
fi
echo "" | tee -a "$OUTPUT_FILE"

# ================================================
# Step 5: Bulk Operations Tests
# ================================================

log "Step 5: Testing Bulk Operations..."
echo "" | tee -a "$OUTPUT_FILE"

# Test 5.1: Bulk fetch fundamentals
log "Test 5.1: Bulk fetch fundamentals for multiple stocks"
log_warning "Note: This will take longer due to rate limiting..."
BULK_RESPONSE=$(curl -s -X POST -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "instrument_tokens": [408065, 738561],
    "include_analyst": false
  }' \
  "${BASE_URL}/fundamentals/bulk-fetch")

echo "Response:" | tee -a "$OUTPUT_FILE"
echo "$BULK_RESPONSE" | python3 -m json.tool 2>&1 | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

if echo "$BULK_RESPONSE" | grep -q "total"; then
    log_success "Bulk fetch completed"
else
    log_error "Bulk fetch failed"
fi
echo "" | tee -a "$OUTPUT_FILE"

# ================================================
# Summary
# ================================================

echo "================================================" | tee -a "$OUTPUT_FILE"
echo "Test Summary" | tee -a "$OUTPUT_FILE"
echo "================================================" | tee -a "$OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

log "Tests completed: $(date)"
log "Results saved to: $OUTPUT_FILE"
echo "" | tee -a "$OUTPUT_FILE"

log_warning "Note: Yahoo Finance rate limiting is expected and handled by the service"
log_warning "Some tests may show warnings if data is not immediately available"
echo "" | tee -a "$OUTPUT_FILE"

echo "================================================" | tee -a "$OUTPUT_FILE"

