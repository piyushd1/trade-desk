# Fundamentals Analysis Documentation

**Module:** Fundamentals Data Integration  
**Data Source:** Yahoo Finance via yfinance library  
**Last Updated:** November 17, 2025

---

## Overview

The Fundamentals module provides access to fundamental analysis data for stocks, including financial ratios, valuation metrics, analyst recommendations, and earnings estimates. Data is fetched from Yahoo Finance and cached in the database for performance.

### Key Features

- ✅ **Fundamental Ratios**: PE, PB, PS, EPS, dividend yield, and more
- ✅ **Analyst Data**: Target prices, recommendations, earnings estimates
- ✅ **Symbol Mapping**: Automatic mapping from Zerodha instrument tokens to Yahoo Finance symbols
- ✅ **Database Caching**: 24-hour cache TTL to minimize API calls
- ✅ **Rate Limiting**: Built-in delays to respect Yahoo Finance rate limits
- ✅ **Bulk Operations**: Fetch data for multiple stocks efficiently

---

## Database Schema

### Tables

#### `symbol_mapping`
Maps Zerodha instrument tokens to Yahoo Finance symbols.

| Column | Type | Description |
|--------|------|-------------|
| `instrument_token` | BigInt (PK) | Zerodha instrument token |
| `yfinance_symbol` | String | Yahoo Finance symbol (e.g., "RELIANCE.NS") |
| `exchange_suffix` | String | Exchange suffix (".NS" for NSE, ".BO" for BSE) |
| `mapping_status` | String | Status: active, invalid, not_found |
| `last_verified_at` | DateTime | Last verification timestamp |
| `created_at` | DateTime | Creation timestamp |
| `updated_at` | DateTime | Last update timestamp |

#### `stock_fundamentals`
Stores fundamental ratios and metrics.

| Category | Fields |
|----------|--------|
| **Company Info** | long_name, sector, industry, full_time_employees |
| **Valuation** | trailing_pe, forward_pe, price_to_book, price_to_sales, enterprise_to_revenue, enterprise_to_ebitda |
| **Profitability** | trailing_eps, forward_eps, earnings_quarterly_growth, revenue_growth, profit_margins, return_on_assets, return_on_equity |
| **Market Data** | market_cap, enterprise_value, shares_outstanding, float_shares |
| **Dividends** | dividend_yield, payout_ratio, trailing_annual_dividend_rate, trailing_annual_dividend_yield |
| **Performance** | fifty_two_week_high, fifty_two_week_low, beta, average_volume, average_volume_10days |

#### `stock_analyst_data`
Stores analyst recommendations and estimates.

| Category | Fields |
|----------|--------|
| **Target Prices** | target_mean_price, target_high_price, target_low_price, target_median_price, current_price |
| **Recommendations** | recommendation_mean (1-5 scale), recommendation_key (buy/hold/sell), number_of_analyst_opinions |
| **Breakdown** | strong_buy_count, buy_count, hold_count, sell_count, strong_sell_count |
| **Earnings** | current_quarter_estimate, next_quarter_estimate, current_year_estimate, next_year_estimate |
| **Revenue** | current_quarter_revenue_estimate, next_quarter_revenue_estimate, current_year_revenue_estimate, next_year_revenue_estimate |
| **Calendar** | earnings_date, earnings_average, earnings_low, earnings_high |

---

## API Endpoints

### 1. Get Fundamentals

**Endpoint:** `GET /api/v1/fundamentals/{instrument_token}`

Get fundamental ratios and metrics for a stock.

**Parameters:**
- `instrument_token` (path): Zerodha instrument token
- `force_refresh` (query, optional): Bypass cache and fetch fresh data (default: false)

**Authentication:** Required (JWT Bearer token)

**Example:**
```bash
curl -H "Authorization: Bearer $TOKEN" \
  "https://piyushdev.com/api/v1/fundamentals/408065"
```

**Response:**
```json
{
  "instrument_token": 408065,
  "long_name": "Infosys Limited",
  "sector": "Technology",
  "industry": "Information Technology Services",
  "trailing_pe": 28.5,
  "forward_pe": 25.3,
  "price_to_book": 8.2,
  "market_cap": 6234567890000,
  "dividend_yield": 0.0235,
  "fifty_two_week_high": 1850.0,
  "fifty_two_week_low": 1350.0,
  "beta": 0.89,
  "data_source": "yfinance",
  "data_date": "2025-11-17",
  "updated_at": "2025-11-17T06:46:26"
}
```

---

### 2. Get Analyst Data

**Endpoint:** `GET /api/v1/fundamentals/{instrument_token}/analyst`

Get analyst recommendations and estimates for a stock.

**Parameters:**
- `instrument_token` (path): Zerodha instrument token
- `force_refresh` (query, optional): Fetch fresh analyst data (default: false)

**Authentication:** Required (JWT Bearer token)

**Example:**
```bash
curl -H "Authorization: Bearer $TOKEN" \
  "https://piyushdev.com/api/v1/fundamentals/408065/analyst"
```

**Response:**
```json
{
  "instrument_token": 408065,
  "data_date": "2025-11-17",
  "target_mean_price": 1750.0,
  "target_high_price": 1950.0,
  "target_low_price": 1550.0,
  "current_price": 1680.0,
  "recommendation_mean": 2.1,
  "recommendation_key": "buy",
  "number_of_analyst_opinions": 35,
  "strong_buy_count": 8,
  "buy_count": 15,
  "hold_count": 10,
  "sell_count": 2,
  "strong_sell_count": 0,
  "current_quarter_estimate": 18.50,
  "next_quarter_estimate": 19.20,
  "earnings_date": "2026-01-15",
  "data_source": "yfinance",
  "updated_at": "2025-11-17T06:50:00"
}
```

---

### 3. Force Fetch Fundamentals

**Endpoint:** `POST /api/v1/fundamentals/fetch`

Force fetch fresh fundamental data from Yahoo Finance, bypassing cache.

**Parameters:**
- `instrument_token` (query): Instrument token to fetch
- `include_analyst` (query, optional): Also fetch analyst data (default: false)

**Authentication:** Required (JWT Bearer token)

**Example:**
```bash
curl -X POST -H "Authorization: Bearer $TOKEN" \
  "https://piyushdev.com/api/v1/fundamentals/fetch?instrument_token=408065&include_analyst=true"
```

**Response:**
```json
{
  "message": "Fundamentals fetched successfully",
  "instrument_token": 408065,
  "fundamentals_updated": true,
  "analyst_data_updated": true
}
```

---

### 4. Bulk Fetch Fundamentals

**Endpoint:** `POST /api/v1/fundamentals/bulk-fetch`

Fetch fundamentals for multiple stocks in bulk.

**Authentication:** Required (JWT Bearer token)

**Request Body:**
```json
{
  "instrument_tokens": [408065, 738561, 2953217],
  "include_analyst": false
}
```

**Example:**
```bash
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "instrument_tokens": [408065, 738561, 2953217],
    "include_analyst": true
  }' \
  "https://piyushdev.com/api/v1/fundamentals/bulk-fetch"
```

**Response:**
```json
{
  "success": 2,
  "failed": 1,
  "skipped": 0,
  "total": 3
}
```

---

### 5. Get Symbol Mapping

**Endpoint:** `GET /api/v1/fundamentals/mapping/{instrument_token}`

Get or create symbol mapping for an instrument.

**Authentication:** Required (JWT Bearer token)

**Example:**
```bash
curl -H "Authorization: Bearer $TOKEN" \
  "https://piyushdev.com/api/v1/fundamentals/mapping/408065"
```

**Response:**
```json
{
  "instrument_token": 408065,
  "yfinance_symbol": "INFY.NS",
  "exchange_suffix": ".NS",
  "mapping_status": "active",
  "last_verified_at": null,
  "created_at": "2025-11-17T06:46:26",
  "updated_at": "2025-11-17T06:46:26"
}
```

---

### 6. Sync Symbol Mappings

**Endpoint:** `POST /api/v1/fundamentals/mapping/sync`

Bulk sync symbol mappings for an exchange.

**Authentication:** Required (JWT Bearer token)

**Request Body:**
```json
{
  "exchange": "NSE",
  "limit": 100
}
```

**Example:**
```bash
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"exchange": "NSE", "limit": 100}' \
  "https://piyushdev.com/api/v1/fundamentals/mapping/sync"
```

**Response:**
```json
{
  "message": "Symbol mapping sync complete for NSE",
  "exchange": "NSE",
  "created": 95,
  "skipped": 5,
  "failed": 0,
  "total_processed": 100
}
```

---

## Configuration

The following settings can be configured in `.env`:

```bash
# Yahoo Finance / Fundamentals Configuration
YFINANCE_CACHE_ENABLED=true
YFINANCE_CACHE_TTL_HOURS=24
YFINANCE_RATE_LIMIT_PER_SECOND=0.9
FUNDAMENTALS_UPDATE_THRESHOLD_HOURS=24
```

---

## Usage Examples

### Example 1: Get Fundamentals for Nifty 50 Stocks

```python
import httpx
import asyncio

async def fetch_nifty50_fundamentals():
    """Fetch fundamentals for Nifty 50 stocks."""
    base_url = "https://piyushdev.com/api/v1"
    token = "your_jwt_token"
    
    # Nifty 50 instrument tokens (example subset)
    nifty50_tokens = [
        408065,  # INFY
        738561,  # RELIANCE
        2953217, # TCS
        # ... add more
    ]
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{base_url}/fundamentals/bulk-fetch",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "instrument_tokens": nifty50_tokens,
                "include_analyst": True
            },
            timeout=300.0  # 5 minutes for bulk operation
        )
        return response.json()

# Run
result = asyncio.run(fetch_nifty50_fundamentals())
print(f"Success: {result['success']}, Failed: {result['failed']}")
```

### Example 2: Compare PE Ratios

```python
async def compare_pe_ratios(tokens: list):
    """Compare PE ratios across multiple stocks."""
    fundamentals_list = []
    
    async with httpx.AsyncClient() as client:
        for token in tokens:
            response = await client.get(
                f"https://piyushdev.com/api/v1/fundamentals/{token}",
                headers={"Authorization": f"Bearer {your_token}"}
            )
            if response.status_code == 200:
                fundamentals_list.append(response.json())
    
    # Sort by PE ratio
    sorted_stocks = sorted(
        fundamentals_list,
        key=lambda x: x.get('trailing_pe') or float('inf')
    )
    
    for stock in sorted_stocks:
        print(f"{stock['long_name']}: PE = {stock['trailing_pe']}")
```

---

## Rate Limiting & Best Practices

### Yahoo Finance Rate Limits

- **Recommended Rate**: 0.9 requests per second
- **Caching**: Always use cached data when available
- **Bulk Operations**: Use bulk endpoints for multiple stocks
- **Off-Peak Hours**: Fetch data during off-peak hours when possible

### Best Practices

1. **Use Cache First**: Don't use `force_refresh=true` unless absolutely necessary
2. **Bulk Fetch**: When fetching multiple stocks, use the bulk endpoint
3. **Scheduled Updates**: Set up daily cron jobs for Nifty 50/portfolio stocks
4. **Symbol Mapping**: Sync symbol mappings once after instrument sync
5. **Error Handling**: Handle 404/429 errors gracefully

---

## Troubleshooting

### Common Issues

**1. "Instrument not found" Error**
- **Cause**: Instrument doesn't exist in database
- **Solution**: Run instrument sync first: `/api/v1/data/zerodha/data/instruments/sync`

**2. "Could not fetch fundamentals" Error**
- **Cause**: Symbol mapping failed or yfinance rate limited
- **Solution**: Check symbol mapping, wait a few seconds, retry

**3. "Rate limit exceeded" (429)**
- **Cause**: Too many requests to Yahoo Finance
- **Solution**: Implement exponential backoff, use cached data

**4. Missing Analyst Data**
- **Cause**: Not all stocks have analyst coverage
- **Solution**: This is normal; analyst data may not be available for all stocks

---

## Integration with Technical Analysis

Combine fundamental and technical analysis for comprehensive insights:

```python
# Get fundamentals
fundamentals = await client.get(f"/api/v1/fundamentals/{token}")

# Get technical indicators
technicals = await client.post(
    "/api/v1/technical-analysis/compute",
    json={
        "instrument_token": token,
        "interval": "day",
        "indicators": ["rsi", "macd"],
        "limit": 50
    }
)

# Combine for decision making
if fundamentals['trailing_pe'] < 20 and technicals['data'][-1]['rsi'] < 30:
    print("Buy signal: Undervalued and oversold")
```

---

## Future Enhancements

Potential future additions:
- Financial statements (P&L, Balance Sheet, Cash Flow)
- Historical fundamental data tracking
- Peer comparison features
- Fundamental-based screening
- Scheduled background updates via Celery
- Support for more data providers (Financial Modeling Prep, etc.)

---

**For questions or issues, refer to the main documentation or contact support.**

