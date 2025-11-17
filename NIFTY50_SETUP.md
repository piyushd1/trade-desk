# Nifty 50 Historical Data Setup

**Date:** November 15, 2025

---

## 🎯 Quick Start

Fetch and store 200 days of historical data for all Nifty 50 stocks:

```bash
cd /home/trade-desk
python3 scripts/fetch_nifty50_data.py --user-identifier RO0252 --days 200
```

This will:
- ✅ Fetch data for all 50 Nifty 50 stocks
- ✅ Store ~10,000 candles in your database (200 days × 50 stocks)
- ✅ Take about 5-10 minutes (includes rate limit delays)
- ✅ Show progress for each stock

---

## 📊 Nifty 50 Stocks List

| Symbol | Token | Company Name |
|--------|-------|--------------|
| RELIANCE | 738561 | Reliance Industries |
| TCS | 2953217 | Tata Consultancy Services |
| HDFCBANK | 341249 | HDFC Bank |
| INFY | 408065 | Infosys |
| ICICIBANK | 1270529 | ICICI Bank |
| HINDUNILVR | 356865 | Hindustan Unilever |
| ITC | 424961 | ITC Ltd |
| SBIN | 779521 | State Bank of India |
| BHARTIARTL | 2714625 | Bharti Airtel |
| KOTAKBANK | 492033 | Kotak Mahindra Bank |
| LT | 2939649 | Larsen & Toubro |
| AXISBANK | 1510401 | Axis Bank |
| ASIANPAINT | 60417 | Asian Paints |
| MARUTI | 2815745 | Maruti Suzuki |
| BAJFINANCE | 81153 | Bajaj Finance |
| HCLTECH | 1850625 | HCL Technologies |
| WIPRO | 969473 | Wipro |
| ULTRACEMCO | 2952193 | UltraTech Cement |
| SUNPHARMA | 857857 | Sun Pharma |
| TITAN | 897537 | Titan Company |
| NTPC | 2977281 | NTPC |
| NESTLEIND | 4598529 | Nestle India |
| TECHM | 3465729 | Tech Mahindra |
| M&M | 519937 | Mahindra & Mahindra |
| POWERGRID | 3834113 | Power Grid Corp |
| BAJAJFINSV | 4268801 | Bajaj Finserv |
| TATAMOTORS | 884737 | Tata Motors |
| ONGC | 633601 | ONGC |
| ADANIPORTS | 3861249 | Adani Ports |
| COALINDIA | 5215745 | Coal India |
| TATASTEEL | 895745 | Tata Steel |
| JSWSTEEL | 3001089 | JSW Steel |
| HINDALCO | 348929 | Hindalco Industries |
| BPCL | 134657 | BPCL |
| INDUSINDBK | 1346049 | IndusInd Bank |
| DRREDDY | 225537 | Dr Reddy's Labs |
| CIPLA | 177665 | Cipla |
| EICHERMOT | 232961 | Eicher Motors |
| DIVISLAB | 2800641 | Divi's Labs |
| BRITANNIA | 140033 | Britannia Industries |
| APOLLOHOSP | 157953 | Apollo Hospitals |
| HEROMOTOCO | 345089 | Hero MotoCorp |
| GRASIM | 315393 | Grasim Industries |
| SHREECEM | 794369 | Shree Cement |
| TATACONSUM | 878593 | Tata Consumer |
| ADANIENT | 6401 | Adani Enterprises |
| HINDZINC | 364545 | Hindustan Zinc |
| SBILIFE | 5582849 | SBI Life Insurance |
| BAJAJ-AUTO | 4267265 | Bajaj Auto |
| UPL | 2889473 | UPL Ltd |

---

## 🚀 Usage Options

### Option 1: Fetch All (Recommended)

```bash
python3 scripts/fetch_nifty50_data.py --user-identifier RO0252 --days 200
```

### Option 2: Custom Days

```bash
# Fetch 1 year of data
python3 scripts/fetch_nifty50_data.py --user-identifier RO0252 --days 365

# Fetch 100 days of data
python3 scripts/fetch_nifty50_data.py --user-identifier RO0252 --days 100
```

### Option 3: Adjust Batch Size (for rate limiting)

```bash
# Process 3 stocks at a time (slower but safer for rate limits)
python3 scripts/fetch_nifty50_data.py --batch-size 3 --days 200
```

---

## 🧪 Test Technical Indicators

After fetching data, test indicators on any stock:

### Get JWT Token

```bash
export ACCESS_TOKEN=$(curl -s -X POST https://piyushdev.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"piyushdev","password":"piyush123"}' \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
```

### Test on Reliance

```bash
curl -X POST https://piyushdev.com/api/v1/technical-analysis/compute \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "instrument_token": 738561,
    "interval": "day",
    "indicators": ["rsi", "macd", "bollinger_bands", "sma", "ema"],
    "sma_periods": [20, 50, 200],
    "ema_periods": [12, 26],
    "limit": 200
  }' | python3 -m json.tool | head -150
```

### Test on TCS

```bash
curl -X POST https://piyushdev.com/api/v1/technical-analysis/compute \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "instrument_token": 2953217,
    "interval": "day",
    "indicators": ["rsi", "atr", "vwap", "adx"],
    "limit": 100
  }' | python3 -m json.tool
```

### Test on HDFC Bank

```bash
curl -X POST https://piyushdev.com/api/v1/technical-analysis/compute \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "instrument_token": 341249,
    "interval": "day",
    "indicators": ["stochastic", "williams_r", "cci"],
    "limit": 100
  }' | python3 -m json.tool
```

---

## 📋 Expected Output

```
======================================================================
Fetching 200 days of historical data for Nifty 50 stocks
======================================================================

🔐 Getting JWT token... ✅ Authenticated

📦 Batch 1/10 (5 stocks)
----------------------------------------------------------------------
  Fetching RELIANCE (token: 738561)... ✅ Stored 200 candles
  Fetching TCS (token: 2953217)... ✅ Stored 200 candles
  Fetching HDFCBANK (token: 341249)... ✅ Stored 200 candles
  Fetching INFY (token: 408065)... ✅ Stored 200 candles
  Fetching ICICIBANK (token: 1270529)... ✅ Stored 200 candles

⏳ Waiting 2 seconds before next batch...

📦 Batch 2/10 (5 stocks)
----------------------------------------------------------------------
  ...

======================================================================
📊 Summary
======================================================================
✅ Successful: 50/50
❌ Failed: 0/50
📈 Total candles stored: 10,000

✅ Done! You can now test technical indicators on these stocks.
```

---

## ⏱️ Time Estimates

| Operation | Time |
|-----------|------|
| Full Nifty 50 (200 days) | ~5-10 minutes |
| Per stock | ~10-15 seconds |
| Batch of 5 stocks | ~1 minute |

**Note:** Time includes 2-second delays between batches to respect Zerodha API rate limits (3 requests/second).

---

## 🔍 Troubleshooting

### Error: "No active Zerodha session found"

**Solution:** Your Zerodha session expired. Re-authenticate:
```bash
# Visit this URL in browser (replace with your user_identifier)
https://piyushdev.com/api/v1/auth/zerodha/connect?state=RO0252
```

### Error: Rate limit exceeded

**Solution:** Reduce batch size:
```bash
python3 scripts/fetch_nifty50_data.py --batch-size 3 --days 200
```

### Some stocks failed

**Solution:** The script will show which stocks failed. You can re-run for just those stocks or check your Zerodha session.

---

## 📈 What You Can Do Next

### 1. Compare Indicators Across Stocks

```bash
# Compare RSI for top 5 stocks
for TOKEN in 738561 2953217 341249 408065 1270529; do
  echo "Testing token: $TOKEN"
  curl -s -X POST https://piyushdev.com/api/v1/technical-analysis/compute \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"instrument_token\": $TOKEN, \"interval\": \"day\", \"indicators\": [\"rsi\"], \"limit\": 1}" \
    | python3 -m json.tool | grep -A 2 "rsi"
done
```

### 2. Backtest Strategies

Use the stored data with indicators to backtest trading strategies.

### 3. Build Dashboards

Fetch indicators for all 50 stocks and create comparison dashboards.

### 4. Screen for Opportunities

Find stocks with specific indicator values (e.g., RSI < 30 for oversold).

---

## 📚 Resources

- **Technical Analysis Docs:** `/home/trade-desk/docs/09_TECHNICAL_ANALYSIS.md`
- **API Documentation:** https://piyushdev.com/docs
- **Test Script:** `/home/trade-desk/tests/scripts/test_technical_analysis_apis.sh`

---

**Ready to test your technical indicators on real Nifty 50 data!** 🚀

