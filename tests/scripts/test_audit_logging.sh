#!/bin/bash
# Test script for audit logging and token refresh functionality

set -e

BASE_URL="${API_BASE_URL:-http://localhost:8000}"
API_BASE="${BASE_URL}/api/v1"

echo "=========================================="
echo "TradeDesk Audit Logging Test Suite"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Health check
echo -e "${BLUE}Test 1: Health Check${NC}"
echo "Testing health endpoint..."
curl -s "${BASE_URL}/health" | python3 -m json.tool
echo -e "${GREEN}✓ Health check passed${NC}"
echo ""

# Test 2: System events
echo -e "${BLUE}Test 2: Query System Events${NC}"
echo "Fetching recent system events..."
curl -s "${API_BASE}/system/events?limit=5" | python3 -m json.tool
echo -e "${GREEN}✓ System events retrieved${NC}"
echo ""

# Test 3: Audit logs
echo -e "${BLUE}Test 3: Query Audit Logs${NC}"
echo "Fetching recent audit logs..."
curl -s "${API_BASE}/audit/logs?limit=5" | python3 -m json.tool
echo -e "${GREEN}✓ Audit logs retrieved${NC}"
echo ""

# Test 4: Token refresh service status
echo -e "${BLUE}Test 4: Token Refresh Service Status${NC}"
echo "Checking token refresh service status..."
curl -s "${API_BASE}/auth/zerodha/refresh/status" | python3 -m json.tool
echo -e "${GREEN}✓ Token refresh status retrieved${NC}"
echo ""

# Test 5: OAuth initiation (creates audit log)
echo -e "${BLUE}Test 5: OAuth Initiation (Audit Logging)${NC}"
echo "Initiating OAuth flow (this creates an audit log)..."
curl -s "${API_BASE}/auth/zerodha/connect?state=test_user" | python3 -m json.tool
echo -e "${GREEN}✓ OAuth initiation logged${NC}"
echo ""

# Test 6: Check for OAuth audit log
echo -e "${BLUE}Test 6: Verify OAuth Audit Log${NC}"
echo "Fetching OAuth-related audit logs..."
curl -s "${API_BASE}/audit/logs?action=oauth_initiate&limit=3" | python3 -m json.tool
echo -e "${GREEN}✓ OAuth audit logs verified${NC}"
echo ""

# Test 7: Check health check audit logs
echo -e "${BLUE}Test 7: Verify Health Check System Events${NC}"
echo "Fetching health check system events..."
curl -s "${API_BASE}/system/events?event_type=health_check&limit=3" | python3 -m json.tool
echo -e "${GREEN}✓ Health check events verified${NC}"
echo ""

# Test 8: Broker status
echo -e "${BLUE}Test 8: Broker Connection Status${NC}"
echo "Checking broker connection status..."
curl -s "${API_BASE}/auth/brokers/status" | python3 -m json.tool
echo -e "${GREEN}✓ Broker status retrieved${NC}"
echo ""

echo ""
echo "=========================================="
echo -e "${GREEN}All tests completed successfully!${NC}"
echo "=========================================="
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Complete OAuth flow manually to test callback logging"
echo "2. Test manual token refresh: curl -X POST '${API_BASE}/auth/zerodha/refresh?user_identifier=YOUR_USER'"
echo "3. Monitor automatic token refresh in logs"
echo ""

