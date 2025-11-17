#!/usr/bin/env python3
"""
Fetch and store historical data for Nifty 50 companies.

This script fetches the last 200 days of historical data for all Nifty 50
constituent stocks and stores them in the database for technical analysis.

Usage:
    export TEST_USERNAME=testuser
    export TEST_PASSWORD=testpass123
    export USER_IDENTIFIER=your_user_id
    export API_BASE_URL=http://localhost:8000  # Optional
    
    python fetch_nifty50_data.py --days 200
    
Or with command-line arguments:
    python fetch_nifty50_data.py --user-identifier YOUR_ID --username testuser --password testpass123 --days 200
"""

import asyncio
import argparse
import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict
import json

# Add backend to path
sys.path.insert(0, '/home/trade-desk/backend')

import httpx


# Nifty 50 companies with their NSE instrument tokens
# Source: Zerodha instruments list
NIFTY_50_STOCKS = [
    {"symbol": "RELIANCE", "token": 738561, "name": "Reliance Industries"},
    {"symbol": "TCS", "token": 2953217, "name": "Tata Consultancy Services"},
    {"symbol": "HDFCBANK", "token": 341249, "name": "HDFC Bank"},
    {"symbol": "INFY", "token": 408065, "name": "Infosys"},
    {"symbol": "ICICIBANK", "token": 1270529, "name": "ICICI Bank"},
    {"symbol": "HINDUNILVR", "token": 356865, "name": "Hindustan Unilever"},
    {"symbol": "ITC", "token": 424961, "name": "ITC Ltd"},
    {"symbol": "SBIN", "token": 779521, "name": "State Bank of India"},
    {"symbol": "BHARTIARTL", "token": 2714625, "name": "Bharti Airtel"},
    {"symbol": "KOTAKBANK", "token": 492033, "name": "Kotak Mahindra Bank"},
    {"symbol": "LT", "token": 2939649, "name": "Larsen & Toubro"},
    {"symbol": "AXISBANK", "token": 1510401, "name": "Axis Bank"},
    {"symbol": "ASIANPAINT", "token": 60417, "name": "Asian Paints"},
    {"symbol": "MARUTI", "token": 2815745, "name": "Maruti Suzuki"},
    {"symbol": "BAJFINANCE", "token": 81153, "name": "Bajaj Finance"},
    {"symbol": "HCLTECH", "token": 1850625, "name": "HCL Technologies"},
    {"symbol": "WIPRO", "token": 969473, "name": "Wipro"},
    {"symbol": "ULTRACEMCO", "token": 2952193, "name": "UltraTech Cement"},
    {"symbol": "SUNPHARMA", "token": 857857, "name": "Sun Pharma"},
    {"symbol": "TITAN", "token": 897537, "name": "Titan Company"},
    {"symbol": "NTPC", "token": 2977281, "name": "NTPC"},
    {"symbol": "NESTLEIND", "token": 4598529, "name": "Nestle India"},
    {"symbol": "TECHM", "token": 3465729, "name": "Tech Mahindra"},
    {"symbol": "M&M", "token": 519937, "name": "Mahindra & Mahindra"},
    {"symbol": "POWERGRID", "token": 3834113, "name": "Power Grid Corp"},
    {"symbol": "BAJAJFINSV", "token": 4268801, "name": "Bajaj Finserv"},
    {"symbol": "TATAMOTORS", "token": 884737, "name": "Tata Motors"},
    {"symbol": "ONGC", "token": 633601, "name": "ONGC"},
    {"symbol": "ADANIPORTS", "token": 3861249, "name": "Adani Ports"},
    {"symbol": "COALINDIA", "token": 5215745, "name": "Coal India"},
    {"symbol": "TATASTEEL", "token": 895745, "name": "Tata Steel"},
    {"symbol": "JSWSTEEL", "token": 3001089, "name": "JSW Steel"},
    {"symbol": "HINDALCO", "token": 348929, "name": "Hindalco Industries"},
    {"symbol": "BPCL", "token": 134657, "name": "BPCL"},
    {"symbol": "INDUSINDBK", "token": 1346049, "name": "IndusInd Bank"},
    {"symbol": "DRREDDY", "token": 225537, "name": "Dr Reddy's Labs"},
    {"symbol": "CIPLA", "token": 177665, "name": "Cipla"},
    {"symbol": "EICHERMOT", "token": 232961, "name": "Eicher Motors"},
    {"symbol": "DIVISLAB", "token": 2800641, "name": "Divi's Labs"},
    {"symbol": "BRITANNIA", "token": 140033, "name": "Britannia Industries"},
    {"symbol": "APOLLOHOSP", "token": 157953, "name": "Apollo Hospitals"},
    {"symbol": "HEROMOTOCO", "token": 345089, "name": "Hero MotoCorp"},
    {"symbol": "GRASIM", "token": 315393, "name": "Grasim Industries"},
    {"symbol": "SHREECEM", "token": 794369, "name": "Shree Cement"},
    {"symbol": "TATACONSUM", "token": 878593, "name": "Tata Consumer"},
    {"symbol": "ADANIENT", "token": 6401, "name": "Adani Enterprises"},
    {"symbol": "HINDZINC", "token": 364545, "name": "Hindustan Zinc"},
    {"symbol": "SBILIFE", "token": 5582849, "name": "SBI Life Insurance"},
    {"symbol": "BAJAJ-AUTO", "token": 4267265, "name": "Bajaj Auto"},
    {"symbol": "UPL", "token": 2889473, "name": "UPL Ltd"},
]


async def get_jwt_token(base_url: str, username: str, password: str) -> str:
    """Get JWT access token."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{base_url}/auth/login",
            json={"username": username, "password": password}
        )
        response.raise_for_status()
        data = response.json()
        return data["access_token"]


async def fetch_and_store_historical(
    base_url: str,
    token: str,
    user_identifier: str,
    instrument_token: int,
    symbol: str,
    days: int = 200
) -> Dict:
    """Fetch and store historical data for one instrument."""
    to_date = datetime.now()
    from_date = to_date - timedelta(days=days)
    
    payload = {
        "user_identifier": user_identifier,
        "instrument_token": instrument_token,
        "from_date": from_date.strftime("%Y-%m-%dT00:00:00"),
        "to_date": to_date.strftime("%Y-%m-%dT23:59:59"),
        "interval": "day",
        "continuous": False,
        "oi": False
    }
    
    print(f"  Fetching {symbol} (token: {instrument_token})...", end=" ", flush=True)
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                f"{base_url}/data/zerodha/data/historical/fetch",
                headers={"Authorization": f"Bearer {token}"},
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            
            # The API returns count inside summary field
            count = data.get("summary", {}).get("count", 0)
            if count == 0:
                print(f"⚠️  Stored 0 candles (check Zerodha session)")
            else:
                print(f"✅ Stored {count} candles")
            return {"symbol": symbol, "status": "success", "count": count}
            
        except httpx.HTTPStatusError as e:
            error_msg = e.response.text
            print(f"❌ Failed: {e.response.status_code}")
            return {"symbol": symbol, "status": "error", "error": error_msg}
        except Exception as e:
            print(f"❌ Failed: {str(e)}")
            return {"symbol": symbol, "status": "error", "error": str(e)}


async def check_zerodha_session(base_url: str, token: str, user_identifier: str) -> bool:
    """Check if there's an active Zerodha session for the given user_identifier."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(
                f"{base_url}/data/zerodha/session/status",
                headers={"Authorization": f"Bearer {token}"},
                params={"user_identifier": user_identifier}
            )
            if response.status_code == 200:
                data = response.json()
                # Check if session is active
                return data.get("status") == "active"
            return False
        except Exception:
            return False


async def fetch_all_nifty50(
    base_url: str,
    user_identifier: str,
    username: str,
    password: str,
    days: int = 200,
    batch_size: int = 5
):
    """Fetch historical data for all Nifty 50 stocks."""
    print("=" * 70)
    print(f"Fetching {days} days of historical data for Nifty 50 stocks")
    print("=" * 70)
    print()
    
    # Get JWT token
    print("🔐 Getting JWT token...", end=" ", flush=True)
    token = await get_jwt_token(base_url, username, password)
    print("✅ Authenticated")
    print()
    
    # Check if Zerodha session exists
    print("🔍 Checking Zerodha session...", end=" ", flush=True)
    has_session = await check_zerodha_session(base_url, token, user_identifier)
    if not has_session:
        print("❌ No active Zerodha session found!")
        print()
        print("=" * 70)
        print("⚠️  ERROR: No Zerodha OAuth session found")
        print("=" * 70)
        print()
        print("You need to authenticate with Zerodha first before fetching data.")
        print()
        print("Steps to authenticate:")
        print(f"1. Visit this URL in your browser:")
        base_domain = base_url.replace('/api/v1', '') if '/api/v1' in base_url else base_url
        print(f"   {base_domain}/api/v1/auth/zerodha/connect?state={user_identifier}")
        print()
        print("2. Log in to Zerodha and authorize the app")
        print()
        print("3. After successful authentication, run this script again")
        print()
        print("=" * 70)
        return
    print("✅ Active session found")
    print()
    
    # Fetch data in batches to avoid overwhelming the API
    results = []
    total = len(NIFTY_50_STOCKS)
    
    for i in range(0, total, batch_size):
        batch = NIFTY_50_STOCKS[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (total + batch_size - 1) // batch_size
        
        print(f"📦 Batch {batch_num}/{total_batches} ({len(batch)} stocks)")
        print("-" * 70)
        
        # Process batch in parallel
        tasks = [
            fetch_and_store_historical(
                base_url, token, user_identifier,
                stock["token"], stock["symbol"], days
            )
            for stock in batch
        ]
        
        batch_results = await asyncio.gather(*tasks)
        results.extend(batch_results)
        
        print()
        
        # Small delay between batches to respect rate limits
        if i + batch_size < total:
            print("⏳ Waiting 2 seconds before next batch...")
            await asyncio.sleep(2)
            print()
    
    # Summary
    print("=" * 70)
    print("📊 Summary")
    print("=" * 70)
    
    success = [r for r in results if r["status"] == "success"]
    failed = [r for r in results if r["status"] == "error"]
    
    total_candles = sum(r.get("count", 0) for r in success)
    
    print(f"✅ Successful: {len(success)}/{total}")
    print(f"❌ Failed: {len(failed)}/{total}")
    print(f"📈 Total candles stored: {total_candles:,}")
    print()
    
    if failed:
        print("❌ Failed stocks:")
        for r in failed:
            print(f"   - {r['symbol']}: {r.get('error', 'Unknown error')[:100]}")
        print()
    
    if total_candles == 0:
        print("⚠️  WARNING: No candles were stored!")
        print()
        print("This usually means:")
        print("1. Your Zerodha session has expired (sessions expire daily at 6 AM IST)")
        print("2. You don't have an active Zerodha session")
        print()
        print("To fix this, authenticate with Zerodha:")
        base_domain = base_url.replace('/api/v1', '') if '/api/v1' in base_url else base_url
        print(f"   {base_domain}/api/v1/auth/zerodha/connect?state={user_identifier}")
        print()
    else:
        print("✅ Done! You can now test technical indicators on these stocks.")
        print()
        print("Example test command:")
        print(f"  curl -X POST {base_url}/technical-analysis/compute \\")
        print("    -H 'Authorization: Bearer $ACCESS_TOKEN' \\")
        print("    -H 'Content-Type: application/json' \\")
        print("    -d '{")
        print('      "instrument_token": 738561,')
        print('      "interval": "day",')
        print('      "indicators": ["rsi", "macd", "bollinger_bands"],')
        print('      "limit": 200')
        print("    }' | python3 -m json.tool")


def main():
    parser = argparse.ArgumentParser(
        description="Fetch and store historical data for Nifty 50 stocks",
        epilog="Environment variables: TEST_USERNAME, TEST_PASSWORD, USER_IDENTIFIER, API_BASE_URL"
    )
    parser.add_argument(
        "--user-identifier",
        default=os.getenv("USER_IDENTIFIER"),
        help="Zerodha user identifier (env: USER_IDENTIFIER)"
    )
    parser.add_argument(
        "--username",
        default=os.getenv("TEST_USERNAME"),
        help="Platform username (env: TEST_USERNAME)"
    )
    parser.add_argument(
        "--password",
        default=os.getenv("TEST_PASSWORD"),
        help="Platform password (env: TEST_PASSWORD)"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=200,
        help="Number of days of historical data to fetch (default: 200)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=5,
        help="Number of stocks to process in parallel (default: 5)"
    )
    parser.add_argument(
        "--base-url",
        default=os.getenv("API_BASE_URL", "http://localhost:8000") + "/api/v1",
        help="Base API URL (env: API_BASE_URL, default: http://localhost:8000/api/v1)"
    )
    
    args = parser.parse_args()
    
    # Validate required arguments
    if not args.user_identifier:
        parser.error("--user-identifier is required (or set USER_IDENTIFIER environment variable)")
    if not args.username:
        parser.error("--username is required (or set TEST_USERNAME environment variable)")
    if not args.password:
        parser.error("--password is required (or set TEST_PASSWORD environment variable)")
    
    # Run async function
    asyncio.run(fetch_all_nifty50(
        base_url=args.base_url,
        user_identifier=args.user_identifier,
        username=args.username,
        password=args.password,
        days=args.days,
        batch_size=args.batch_size
    ))


if __name__ == "__main__":
    main()

