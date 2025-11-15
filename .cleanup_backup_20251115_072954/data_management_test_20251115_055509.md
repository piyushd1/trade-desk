# Data Management API Test Results

**Test Date:** 2025-11-15 05:55:09
**User Identifier:** RO0252

---

## 1. Sync Instruments API

**Endpoint:** `POST /api/v1/data/zerodha/data/instruments/sync`
**Timestamp:** 2025-11-15 05:55:10
**Request:** Sync NSE instruments

```json
{
    "status": "success",
    "summary": {
        "total": 8588,
        "exchange": "NSE",
        "unique_symbols": 8588
    }
}
```

---

## 2. Search Instruments API (Public)

**Endpoint:** `GET /api/v1/data/zerodha/data/instruments/search`
**Timestamp:** 2025-11-15 05:55:13
**Request:** Search for INFY in NSE

```json
{
    "count": 1,
    "results": [
        {
            "instrument_token": 408065,
            "exchange_token": 1594,
            "tradingsymbol": "INFY",
            "name": "INFOSYS",
            "last_price": 0.0,
            "expiry": null,
            "strike": 0.0,
            "tick_size": 0.1,
            "lot_size": 1,
            "instrument_type": "EQ",
            "segment": "NSE",
            "exchange": "NSE",
            "underlying": null,
            "updated_at": "2025-11-15T05:55:11"
        }
    ]
}
```

---

## 3. Fetch and Store Historical Data API

**Endpoint:** `POST /api/v1/data/zerodha/data/historical/fetch`
**Timestamp:** 2025-11-15 05:55:13
**Request:** Fetch INFY (token: 408065) historical data

```json
{
    "status": "success",
    "summary": {
        "instrument_token": 408065,
        "interval": "day",
        "count": 8,
        "from": "2025-11-02T18:30:00+00:00",
        "to": "2025-11-12T18:30:00+00:00"
    }
}
```

---

## 4. Query Stored Historical Data API (Public)

**Endpoint:** `GET /api/v1/data/zerodha/data/historical`
**Timestamp:** 2025-11-15 05:55:14
**Request:** Query stored historical data for INFY (token: 408065)

```json
{
    "count": 8,
    "candles": [
        {
            "timestamp": "2025-11-02T18:30:00",
            "open": 1482.3,
            "high": 1491.4,
            "low": 1474.2,
            "close": 1485.5,
            "volume": 5470600,
            "oi": null
        },
        {
            "timestamp": "2025-11-03T18:30:00",
            "open": 1479.7,
            "high": 1481.9,
            "low": 1462.9,
            "close": 1467.9,
            "volume": 8691330,
            "oi": null
        },
        {
            "timestamp": "2025-11-05T18:30:00",
            "open": 1478.6,
            "high": 1483.0,
            "low": 1461.9,
            "close": 1466.7,
            "volume": 7944752,
            "oi": null
        },
        {
            "timestamp": "2025-11-06T18:30:00",
            "open": 1470.0,
            "high": 1480.9,
            "low": 1449.1,
            "close": 1476.8,
            "volume": 8765759,
            "oi": null
        },
        {
            "timestamp": "2025-11-09T18:30:00",
            "open": 1490.1,
            "high": 1520.0,
            "low": 1490.0,
            "close": 1513.5,
            "volume": 9787975,
            "oi": null
        },
        {
            "timestamp": "2025-11-10T18:30:00",
            "open": 1525.0,
            "high": 1533.4,
            "low": 1511.1,
            "close": 1530.3,
            "volume": 13692989,
            "oi": null
        },
        {
            "timestamp": "2025-11-11T18:30:00",
            "open": 1540.0,
            "high": 1559.2,
            "low": 1538.1,
            "close": 1551.7,
            "volume": 14635417,
            "oi": null
        },
        {
            "timestamp": "2025-11-12T18:30:00",
            "open": 1557.1,
            "high": 1557.5,
            "low": 1530.3,
            "close": 1541.8,
            "volume": 19655689,
            "oi": null
        }
    ]
}
```

---

## Test Summary

**Completed:** 2025-11-15 05:55:14

All 4 Data Management API endpoints tested successfully.

### Endpoints Tested:
1. ✅ Sync Instruments (requires JWT)
2. ✅ Search Instruments (public)
3. ✅ Fetch Historical Data (requires JWT)
4. ✅ Query Historical Data (public)
