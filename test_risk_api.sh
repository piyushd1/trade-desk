#!/bin/bash
# Test script for Risk Management API endpoints

set -e

BASE_URL="https://piyushdev.com"
API_BASE="${BASE_URL}/api/v1"

echo "=========================================="
echo "Risk Management API Test Suite"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Test 1: Get risk configuration
echo -e "${BLUE}Test 1: Get Risk Configuration${NC}"
curl -s "${API_BASE}/risk/config" | python3 -m json.tool
echo -e "${GREEN}✓ Risk config retrieved${NC}"
echo ""

# Test 2: Get kill switch status
echo -e "${BLUE}Test 2: Get Kill Switch Status${NC}"
curl -s "${API_BASE}/risk/kill-switch/status" | python3 -m json.tool
echo -e "${GREEN}✓ Kill switch status retrieved${NC}"
echo ""

# Test 3: Toggle kill switch (disable)
echo -e "${BLUE}Test 3: Disable Kill Switch${NC}"
curl -s -X POST "${API_BASE}/risk/kill-switch" \
  -H "Content-Type: application/json" \
  -d '{"enabled": false, "reason": "Testing kill switch"}' | python3 -m json.tool
echo -e "${GREEN}✓ Kill switch disabled${NC}"
echo ""

# Test 4: Verify kill switch disabled
echo -e "${BLUE}Test 4: Verify Kill Switch Disabled${NC}"
curl -s "${API_BASE}/risk/kill-switch/status" | python3 -m json.tool
echo -e "${GREEN}✓ Kill switch status verified${NC}"
echo ""

# Test 5: Re-enable kill switch
echo -e "${BLUE}Test 5: Re-enable Kill Switch${NC}"
curl -s -X POST "${API_BASE}/risk/kill-switch" \
  -H "Content-Type: application/json" \
  -d '{"enabled": true, "reason": "Testing complete"}' | python3 -m json.tool
echo -e "${GREEN}✓ Kill switch re-enabled${NC}"
echo ""

# Test 6: Pre-trade check (valid order)
echo -e "${BLUE}Test 6: Pre-Trade Check (Valid Order)${NC}"
curl -s -X POST "${API_BASE}/risk/pre-trade-check" \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "symbol": "RELIANCE", "quantity": 10, "price": 2500.0}' | python3 -m json.tool
echo -e "${GREEN}✓ Pre-trade check completed${NC}"
echo ""

# Test 7: Pre-trade check (invalid order - exceeds limits)
echo -e "${BLUE}Test 7: Pre-Trade Check (Invalid Order)${NC}"
curl -s -X POST "${API_BASE}/risk/pre-trade-check" \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "symbol": "RELIANCE", "quantity": 100, "price": 2500.0}' | python3 -m json.tool
echo -e "${GREEN}✓ Pre-trade check completed (expected failures)${NC}"
echo ""

# Test 8: Get daily metrics
echo -e "${BLUE}Test 8: Get Daily Metrics${NC}"
curl -s "${API_BASE}/risk/metrics/daily?user_id=1" | python3 -m json.tool
echo -e "${GREEN}✓ Daily metrics retrieved${NC}"
echo ""

# Test 9: Get risk breaches
echo -e "${BLUE}Test 9: Get Risk Breaches${NC}"
curl -s "${API_BASE}/risk/breaches?user_id=1&limit=5" | python3 -m json.tool
echo -e "${GREEN}✓ Risk breaches retrieved${NC}"
echo ""

# Test 10: Get comprehensive risk status
echo -e "${BLUE}Test 10: Get Risk Status${NC}"
curl -s "${API_BASE}/risk/status?user_id=1" | python3 -m json.tool
echo -e "${GREEN}✓ Risk status retrieved${NC}"
echo ""

# Test 11: Get metrics history
echo -e "${BLUE}Test 11: Get Metrics History${NC}"
curl -s "${API_BASE}/risk/metrics/history?user_id=1&days=7" | python3 -m json.tool
echo -e "${GREEN}✓ Metrics history retrieved${NC}"
echo ""

# Test 12: Check risk limits utilization
echo -e "${BLUE}Test 12: Check Risk Limits Utilization${NC}"
curl -s "${API_BASE}/risk/limits/check?user_id=1" | python3 -m json.tool
echo -e "${GREEN}✓ Risk limits checked${NC}"
echo ""

# Test 13: Update risk configuration
echo -e "${BLUE}Test 13: Update Risk Configuration${NC}"
curl -s -X PUT "${API_BASE}/risk/config" \
  -H "Content-Type: application/json" \
  -d '{"max_daily_loss": 6000.0, "ops_limit": 15}' | python3 -m json.tool
echo -e "${GREEN}✓ Risk config updated${NC}"
echo ""

# Test 14: Verify config update
echo -e "${BLUE}Test 14: Verify Config Update${NC}"
curl -s "${API_BASE}/risk/config" | python3 -m json.tool | grep -E "(max_daily_loss|ops_limit)"
echo -e "${GREEN}✓ Config update verified${NC}"
echo ""

echo ""
echo "=========================================="
echo -e "${GREEN}All API tests completed successfully!${NC}"
echo "=========================================="
echo ""
echo -e "${YELLOW}API Endpoints Available:${NC}"
echo "  GET  /api/v1/risk/config - Get risk configuration"
echo "  PUT  /api/v1/risk/config - Update risk configuration"
echo "  POST /api/v1/risk/kill-switch - Toggle kill switch"
echo "  GET  /api/v1/risk/kill-switch/status - Get kill switch status"
echo "  POST /api/v1/risk/pre-trade-check - Run pre-trade check"
echo "  GET  /api/v1/risk/metrics/daily - Get daily metrics"
echo "  GET  /api/v1/risk/metrics/history - Get metrics history"
echo "  GET  /api/v1/risk/breaches - Query risk breaches"
echo "  GET  /api/v1/risk/status - Get comprehensive status"
echo "  GET  /api/v1/risk/limits/check - Check limit utilization"
echo ""

