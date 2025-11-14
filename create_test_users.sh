#!/bin/bash

#######################################################################
# Script to Create Test Users
#######################################################################

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

API_BASE="https://piyushdev.com/api/v1"
BASIC_AUTH_USER="piyushdeveshwar"
BASIC_AUTH_PASS="Lead@102938"

echo "=================================================="
echo "  Creating Test Users"
echo "=================================================="
echo ""

api_call() {
    curl -s -u "$BASIC_AUTH_USER:$BASIC_AUTH_PASS" "$@"
}

# Create Admin User
echo -e "${YELLOW}Creating admin user...${NC}"
ADMIN_RESPONSE=$(api_call -X POST "$API_BASE/auth/register" \
    -H "Content-Type: application/json" \
    -d '{
        "username": "admin",
        "email": "admin@tradedesk.com",
        "password": "admin123",
        "full_name": "Admin User"
    }')

echo "$ADMIN_RESPONSE" | python3 -m json.tool
echo ""

if echo "$ADMIN_RESPONSE" | grep -q '"status":"success"'; then
    echo -e "${GREEN}✓ Admin user created${NC}"
else
    echo -e "${RED}✗ Admin user creation failed (may already exist)${NC}"
fi
echo ""

# Create Regular User
echo -e "${YELLOW}Creating piyushdev user...${NC}"
USER_RESPONSE=$(api_call -X POST "$API_BASE/auth/register" \
    -H "Content-Type: application/json" \
    -d '{
        "username": "piyushdev",
        "email": "piyush@tradedesk.com",
        "password": "piyush123",
        "full_name": "Piyush Deveshwar"
    }')

echo "$USER_RESPONSE" | python3 -m json.tool
echo ""

if echo "$USER_RESPONSE" | grep -q '"status":"success"'; then
    echo -e "${GREEN}✓ Piyushdev user created${NC}"
else
    echo -e "${RED}✗ Piyushdev user creation failed (may already exist)${NC}"
fi
echo ""

echo "=================================================="
echo "  User Creation Complete"
echo "=================================================="
echo ""
echo "Test Users:"
echo "  1. admin / admin123"
echo "  2. piyushdev / piyush123"
echo ""
echo "You can now run:"
echo "  ./test_internal_auth.sh"

