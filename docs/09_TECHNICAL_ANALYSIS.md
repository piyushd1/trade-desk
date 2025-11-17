# 09 - Technical Analysis

[← Back to Master PRD](MASTER_PRD.md)

---

## 📊 Overview

The Technical Analysis module provides runtime computation of 60+ technical indicators from stored historical OHLCV data. All indicators are computed on-demand using the industry-standard `ta` library (Technical Analysis Library in Python).

---

## 🎯 Key Features

- **60+ Indicators**: Momentum, Volume, Volatility, Trend, and Return indicators
- **Runtime Computation**: All indicators computed on-demand from stored data
- **Flexible Parameters**: Customize indicator parameters (e.g., MA periods)
- **RESTful API**: Simple HTTP endpoints with JWT authentication
- **No Pre-computation**: No additional storage overhead
- **Comprehensive Coverage**: All major indicator categories supported

---

## 📋 Available Indicators

### Momentum Indicators (14)

| Indicator | Code | Description | Output Columns |
|-----------|------|-------------|----------------|
| **RSI** | `rsi` | Relative Strength Index | `rsi` |
| **ROC** | `roc` | Rate of Change | `roc` |
| **Awesome Oscillator** | `awesome_oscillator` | Market momentum | `awesome_oscillator` |
| **KAMA** | `kama` | Kaufman's Adaptive MA | `kama` |
| **PPO** | `ppo` | Percentage Price Oscillator | `ppo`, `ppo_signal`, `ppo_hist` |
| **Stochastic** | `stochastic` | Stochastic Oscillator | `stoch`, `stoch_signal` |
| **Williams %R** | `williams_r` | Williams %R | `williams_r` |

### Volume Indicators (9)

| Indicator | Code | Description | Output Columns |
|-----------|------|-------------|----------------|
| **AD** | `ad` | Accumulation/Distribution | `ad` |
| **CMF** | `cmf` | Chaikin Money Flow | `cmf` |
| **VWAP** | `vwap` | Volume Weighted Avg Price | `vwap` |
| **MFI** | `mfi` | Money Flow Index | `mfi` |
| **OBV** | `obv` | On-Balance Volume | `obv` |

### Volatility Indicators (5)

| Indicator | Code | Description | Output Columns |
|-----------|------|-------------|----------------|
| **ATR** | `atr` | Average True Range | `atr` |
| **Bollinger Bands** | `bollinger_bands` | Bollinger Bands | `bb_high`, `bb_mid`, `bb_low`, `bb_width`, `bb_pct` |
| **Keltner Channel** | `keltner_channel` | Keltner Channel | `kc_high`, `kc_mid`, `kc_low` |
| **Donchian Channel** | `donchian_channel` | Donchian Channel | `dc_high`, `dc_mid`, `dc_low` |

### Trend Indicators (15)

| Indicator | Code | Description | Output Columns |
|-----------|------|-------------|----------------|
| **SMA** | `sma` | Simple Moving Average | `sma_20`, `sma_50`, `sma_200` (customizable) |
| **EMA** | `ema` | Exponential Moving Average | `ema_12`, `ema_26` (customizable) |
| **WMA** | `wma` | Weighted Moving Average | `wma_9` (customizable) |
| **MACD** | `macd` | MACD | `macd`, `macd_signal`, `macd_diff` |
| **ADX** | `adx` | Average Directional Index | `adx`, `adx_pos`, `adx_neg` |
| **Aroon** | `aroon` | Aroon Indicator | `aroon_up`, `aroon_down` |
| **CCI** | `cci` | Commodity Channel Index | `cci` |
| **Ichimoku** | `ichimoku` | Ichimoku Cloud | `ichimoku_a`, `ichimoku_b`, `ichimoku_base`, `ichimoku_conversion` |
| **PSAR** | `psar` | Parabolic SAR | `psar`, `psar_up`, `psar_down` |
| **Vortex** | `vortex` | Vortex Indicator | `vortex_pos`, `vortex_neg` |

### Other Indicators (3)

| Indicator | Code | Description | Output Columns |
|-----------|------|-------------|----------------|
| **Daily Return** | `daily_return` | Daily percentage return | `daily_return` |
| **Cumulative Return** | `cumulative_return` | Cumulative return | `cumulative_return` |

---

## 🔌 API Endpoints

### 1. List Available Indicators

**GET** `/api/v1/technical-analysis/indicators/list`

List all available indicators categorized by type.

**Authentication:** Public (no JWT required)

**Response:**
```json
{
  "momentum": ["rsi", "roc", "awesome_oscillator", ...],
  "volume": ["ad", "cmf", "vwap", ...],
  "volatility": ["atr", "bollinger_bands", ...],
  "trend": ["sma", "ema", "macd", ...],
  "others": ["daily_return", "cumulative_return"]
}
```

**Example:**
```bash
curl https://piyushdev.com/api/v1/technical-analysis/indicators/list | python3 -m json.tool
```

---

### 2. Compute Indicators

**POST** `/api/v1/technical-analysis/compute`

Compute technical indicators for an instrument from stored historical data.

**Authentication:** JWT Bearer token required

**Request Body:**
```json
{
  "instrument_token": 408065,
  "interval": "day",
  "indicators": ["rsi", "macd", "bollinger_bands"],
  "limit": 200,
  "sma_periods": [20, 50, 200],
  "ema_periods": [12, 26]
}
```

**Parameters:**

| Parameter | Type | Required | Description | Default |
|-----------|------|----------|-------------|---------|
| `instrument_token` | integer | Yes | Zerodha instrument token | - |
| `interval` | string | No | Time interval | `"day"` |
| `indicators` | array | No | List of indicators (null = all) | `null` |
| `limit` | integer | No | Number of candles | `500` |
| `sma_periods` | array | No | SMA periods | `[20, 50, 200]` |
| `ema_periods` | array | No | EMA periods | `[12, 26]` |
| `wma_periods` | array | No | WMA periods | `[9]` |

**Response:**
```json
{
  "instrument_token": 408065,
  "interval": "day",
  "count": 200,
  "columns": ["timestamp", "open", "high", "low", "close", "volume", "oi", "rsi", "macd", ...],
  "data": [
    {
      "timestamp": "2025-11-01T00:00:00",
      "open": 1450.0,
      "high": 1455.0,
      "low": 1445.0,
      "close": 1452.0,
      "volume": 1000000,
      "oi": 0,
      "rsi": 55.34,
      "macd": 2.45,
      "macd_signal": 1.89,
      "macd_diff": 0.56,
      "bb_high": 1460.0,
      "bb_mid": 1450.0,
      "bb_low": 1440.0
    },
    ...
  ]
}
```

---

## 📖 Usage Examples

### Example 1: Compute Specific Indicators

Compute RSI, MACD, and Bollinger Bands for INFY:

```bash
curl -X POST https://piyushdev.com/api/v1/technical-analysis/compute \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "instrument_token": 408065,
    "interval": "day",
    "indicators": ["rsi", "macd", "bollinger_bands"],
    "limit": 100
  }' | python3 -m json.tool
```

### Example 2: Custom Moving Averages

Compute SMA with custom periods:

```bash
curl -X POST https://piyushdev.com/api/v1/technical-analysis/compute \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "instrument_token": 738561,
    "interval": "day",
    "indicators": ["sma", "ema"],
    "sma_periods": [20, 50, 200],
    "ema_periods": [12, 26, 50],
    "limit": 300
  }' | python3 -m json.tool
```

### Example 3: Compute All Indicators

Compute all available indicators by omitting the `indicators` parameter:

```bash
curl -X POST https://piyushdev.com/api/v1/technical-analysis/compute \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "instrument_token": 408065,
    "interval": "day",
    "limit": 200
  }' | python3 -m json.tool
```

### Example 4: Intraday Analysis

Compute indicators for 5-minute candles:

```bash
curl -X POST https://piyushdev.com/api/v1/technical-analysis/compute \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "instrument_token": 408065,
    "interval": "5minute",
    "indicators": ["rsi", "vwap", "atr"],
    "limit": 100
  }' | python3 -m json.tool
```

---

## 🔄 Data Pipeline Integration

### Prerequisites

Before computing indicators, ensure historical data is stored in the database:

```bash
# 1. Sync instruments (if not already done)
curl -X POST https://piyushdev.com/api/v1/data/zerodha/data/instruments/sync \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_identifier": "RO0252",
    "exchange": "NSE"
  }'

# 2. Fetch and store historical data
curl -X POST https://piyushdev.com/api/v1/data/zerodha/data/historical/fetch \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_identifier": "RO0252",
    "instrument_token": 408065,
    "from_date": "2025-01-01T00:00:00",
    "to_date": "2025-11-15T23:59:59",
    "interval": "day"
  }'

# 3. Now compute indicators
curl -X POST https://piyushdev.com/api/v1/technical-analysis/compute \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "instrument_token": 408065,
    "interval": "day",
    "indicators": ["rsi", "macd"],
    "limit": 200
  }'
```

### Data Flow

```
┌─────────────────────────────────────────────────────┐
│  Zerodha Historical Data API                        │
└─────────────────────┬───────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────┐
│  Data Management API                                │
│  POST /data/zerodha/data/historical/fetch           │
└─────────────────────┬───────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────┐
│  PostgreSQL Database                                │
│  historical_candles table                           │
│  (instrument_token, interval, timestamp, OHLCV)     │
└─────────────────────┬───────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────┐
│  Technical Analysis Service                         │
│  - Fetch OHLCV data                                 │
│  - Convert to pandas DataFrame                      │
│  - Compute indicators using ta library              │
└─────────────────────┬───────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────┐
│  Technical Analysis API                             │
│  POST /technical-analysis/compute                   │
│  Returns: OHLCV + Indicators as JSON                │
└─────────────────────────────────────────────────────┘
```

---

## ⚙️ Configuration

### Supported Intervals

All Zerodha-supported intervals:
- `minute` - 1-minute candles
- `3minute` - 3-minute candles
- `5minute` - 5-minute candles
- `15minute` - 15-minute candles
- `30minute` - 30-minute candles
- `60minute` - 1-hour candles
- `day` - Daily candles

### Default Parameters

| Parameter | Default Value | Customizable |
|-----------|---------------|--------------|
| SMA Periods | [20, 50, 200] | ✅ Yes |
| EMA Periods | [12, 26] | ✅ Yes |
| WMA Periods | [9] | ✅ Yes |
| RSI Window | 14 | ❌ No (library default) |
| MACD Fast/Slow/Signal | 12/26/9 | ❌ No (library default) |
| Bollinger Bands Window | 20 | ❌ No (library default) |

---

## 🔍 Implementation Details

### Architecture

- **Service Layer**: `TechnicalAnalysisService` in `app/services/technical_analysis_service.py`
- **API Layer**: `technical_analysis.py` in `app/api/v1/`
- **Dependencies**: `ta==0.11.0`, `pandas==2.2.3`, `numpy==1.26.4`
- **Computation**: Runtime (no pre-storage)
- **Authentication**: JWT Bearer token

### Performance Considerations

1. **Computation Time**: Typically < 1 second for 200-500 candles
2. **Memory Usage**: ~10-50 MB per request (depends on data size)
3. **Database Load**: Single query to fetch OHLCV data
4. **Concurrency**: Multiple users can compute simultaneously

### Error Handling

| Error Code | Condition | Message |
|------------|-----------|---------|
| 404 | No historical data | "No historical data found for instrument token..." |
| 401 | Missing/invalid JWT | "Could not validate credentials" |
| 422 | Invalid parameters | "Validation error" |
| 500 | Computation error | "Internal server error" |

---

## 🧪 Testing

### Test Script

Run the comprehensive test suite:

```bash
cd /home/trade-desk/tests/scripts
./test_technical_analysis_apis.sh
```

### Manual Testing

```bash
# 1. Get JWT token
export ACCESS_TOKEN=$(curl -s -X POST https://piyushdev.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"piyushdev","password":"piyush123"}' \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

# 2. List indicators
curl https://piyushdev.com/api/v1/technical-analysis/indicators/list | python3 -m json.tool

# 3. Compute indicators
curl -X POST https://piyushdev.com/api/v1/technical-analysis/compute \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "instrument_token": 408065,
    "interval": "day",
    "indicators": ["rsi", "macd"],
    "limit": 50
  }' | python3 -m json.tool
```

---

## 📊 Use Cases

### 1. Strategy Development

Compute indicators to develop trading strategies:

```python
# Fetch indicators via API
data = api.compute_indicators(
    instrument_token=408065,
    indicators=["rsi", "macd", "bollinger_bands"],
    limit=200
)

# Analyze crossovers, overbought/oversold, etc.
if data['rsi'][-1] < 30:
    # RSI oversold - potential buy signal
    ...
```

### 2. Backtesting

Historical indicator values for backtesting:

```python
# Get historical data with indicators
data = api.compute_indicators(
    instrument_token=408065,
    interval="day",
    limit=1000  # Last 1000 days
)

# Run backtest with indicator-based strategy
backtest_strategy(data)
```

### 3. Dashboard Visualization

Real-time indicator charts:

```javascript
// Fetch indicators for charting
const data = await fetch('/api/v1/technical-analysis/compute', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    instrument_token: 408065,
    indicators: ['rsi', 'macd', 'bollinger_bands'],
    limit: 100
  })
});

// Render charts with indicators
renderChart(data);
```

---

## 🚀 Future Enhancements

### Phase 2 (Future)
- Pre-computed indicator storage for common indicators
- Background jobs for daily computation
- Redis caching for frequently accessed indicators
- Custom indicator formulas
- Indicator alerts and notifications

---

## 📚 References

- **ta Library Documentation**: https://technical-analysis-library-in-python.readthedocs.io/
- **Zerodha Historical Data**: https://kite.trade/docs/connect/v3/historical/
- **Technical Analysis Basics**: https://www.investopedia.com/terms/t/technicalanalysis.asp

---

**Implementation Date:** November 15, 2025  
**Status:** ✅ Complete (Phase 1 - Runtime Computation)

