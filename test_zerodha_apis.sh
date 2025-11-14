#!/bin/bash

# Zerodha API Exploration Test Script
# Test all available Zerodha endpoints

set -e

BASE_URL="https://piyushdev.com/api/v1"
USER_ID="${1:-}"

if [ -z "$USER_ID" ]; then
    echo "❌ Error: User identifier required"
    echo "Usage: $0 <user_identifier>"
    echo ""
    echo "Your user_identifier is what you used as 'state' during Zerodha OAuth."
    echo ""
    echo "To find your user_identifier:"
    echo "  curl \"https://piyushdev.com/api/v1/auth/zerodha/session\" | python3 -m json.tool"
    exit 1
fi

echo "=================================="
echo "Zerodha API Explorer - Test Suite"
echo "=================================="
echo "User Identifier: $USER_ID"
echo "Base URL: $BASE_URL"
echo ""

# Helper function
test_endpoint() {
    local name="$1"
    local method="${2:-GET}"
    local url="$3"
    local data="$4"
    
    echo "-----------------------------------"
    echo "📊 Testing: $name"
    echo "Method: $method"
    echo "URL: $url"
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s "$url")
    else
        response=$(curl -s -X "$method" "$url" -H "Content-Type: application/json" -d "$data")
    fi
    
    status=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('status', 'unknown'))" 2>/dev/null || echo "error")
    
    if [ "$status" = "success" ]; then
        echo "✅ Success"
        echo "$response" | python3 -m json.tool | head -20
    else
        echo "❌ Failed"
        echo "$response" | python3 -m json.tool
    fi
    
    echo ""
}

echo "🎯 CATEGORY 1: Account Management"
test_endpoint "User Profile" "GET" "$BASE_URL/data/zerodha/profile?user_id=$USER_ID"
test_endpoint "Account Margins" "GET" "$BASE_URL/data/zerodha/margins?user_id=$USER_ID"

echo "🎯 CATEGORY 2: Portfolio Management"
test_endpoint "Holdings" "GET" "$BASE_URL/data/zerodha/holdings?user_id=$USER_ID"
test_endpoint "Positions" "GET" "$BASE_URL/data/zerodha/positions?user_id=$USER_ID"

echo "🎯 CATEGORY 3: Order Management"
test_endpoint "Orders List" "GET" "$BASE_URL/data/zerodha/orders?user_id=$USER_ID"
test_endpoint "Trades" "GET" "$BASE_URL/data/zerodha/trades?user_id=$USER_ID"

echo "🎯 CATEGORY 4: Market Data"
echo "-----------------------------------"
echo "📊 Testing: Instruments (NSE only - full list too large)"
echo "Method: GET"
curl -s "$BASE_URL/data/zerodha/instruments?user_id=$USER_ID&exchange=NSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(f\"✅ Success: {data.get('count', 0)} instruments fetched\"); print(json.dumps(data.get('data', [])[:3], indent=2))" 2>/dev/null || echo "❌ Failed"
echo ""

test_endpoint "LTP - Last Price" "POST" "$BASE_URL/data/zerodha/ltp?user_id=$USER_ID" '["NSE:INFY", "NSE:RELIANCE"]'
test_endpoint "OHLC" "POST" "$BASE_URL/data/zerodha/ohlc?user_id=$USER_ID" '["NSE:INFY"]'
test_endpoint "Full Quote" "POST" "$BASE_URL/data/zerodha/quote?user_id=$USER_ID" '["NSE:INFY"]'

echo "🎯 CATEGORY 5: Historical Data"
echo "-----------------------------------"
echo "📊 Testing: Historical Data (INFY - last 10 days)"
echo "Note: Using instrument_token 408065 (INFY)"
FROM_DATE=$(date -d "10 days ago" +%Y-%m-%d)
TO_DATE=$(date +%Y-%m-%d)
test_endpoint "Historical Candles" "GET" "$BASE_URL/data/zerodha/historical/408065?user_id=$USER_ID&from_date=$FROM_DATE&to_date=$TO_DATE&interval=day"

echo "🎯 CATEGORY 6: API Capabilities"
test_endpoint "Capabilities Overview" "GET" "$BASE_URL/data/zerodha/capabilities"

echo "=================================="
echo "✅ Test Suite Complete!"
echo "=================================="
echo ""
echo "Next Steps:"
echo "1. Review the responses above"
echo "2. Check Swagger UI: https://piyushdev.com/docs"
echo "3. Read full guide: ZERODHA_API_EXPLORATION.md"
echo "4. Model your application around available data"
echo ""
echo "🔥 Key Endpoints for Algo Trading:"
echo "  - Historical Data: For backtesting"
echo "  - Market Quote/LTP: For real-time signals"
echo "  - Margins Check: For risk management"
echo "  - Orders API: For execution"
echo "  - Positions: For P&L tracking"
echo ""

