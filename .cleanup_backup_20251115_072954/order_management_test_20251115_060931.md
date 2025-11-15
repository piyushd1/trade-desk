# Order Management API Test Results

**Test Date:** 2025-11-15 06:09:31
**User Identifier:** RO0252
**User ID:** 2 (piyushdev)

⚠️  **NOTE:** Only PREVIEW endpoint is tested (safe, no orders placed)

---

## 1. Preview Order API (SAFE)

**Endpoint:** `POST /api/v1/orders/preview`
**Timestamp:** 2025-11-15 06:09:32
**Request:** Preview BUY order for INFY

**Order Details:**
- Exchange: NSE
- Symbol: INFY
- Transaction: BUY
- Quantity: 1
- Order Type: LIMIT
- Product: CNC
- Price: 1500.0

```json
{
    "all_checks_passed": false,
    "risk_checks": [
        {
            "check": "kill_switch",
            "passed": false,
            "reason": "Trading is disabled (kill switch activated)",
            "breach_type": "kill_switch",
            "details": {
                "user_id": 2,
                "trading_enabled": false
            }
        },
        {
            "check": "trading_hours",
            "passed": true,
            "reason": "Within regular trading hours",
            "breach_type": "",
            "details": {}
        },
        {
            "check": "position_limits",
            "passed": true,
            "reason": "Position limits check passed",
            "breach_type": "",
            "details": {}
        },
        {
            "check": "order_limits",
            "passed": true,
            "reason": "Order limits check passed",
            "breach_type": "",
            "details": {}
        },
        {
            "check": "ops_limit",
            "passed": true,
            "reason": "OPS limit check passed",
            "breach_type": "",
            "details": {}
        },
        {
            "check": "loss_limits",
            "passed": true,
            "reason": "Loss limits check passed",
            "breach_type": "",
            "details": {}
        }
    ],
    "margin": [
        {
            "type": "equity",
            "tradingsymbol": "INFY",
            "exchange": "NSE",
            "span": 0,
            "exposure": 0,
            "option_premium": 0,
            "additional": 0,
            "bo": 0,
            "cash": 0,
            "var": 1500,
            "pnl": {
                "realised": 0,
                "unrealised": 0
            },
            "leverage": 1,
            "charges": {
                "transaction_tax": 1.5,
                "transaction_tax_type": "stt",
                "exchange_turnover_charge": 0.04605,
                "sebi_turnover_charge": 0.0015,
                "brokerage": 0,
                "stamp_duty": 0,
                "gst": {
                    "igst": 0.008559,
                    "cgst": 0,
                    "sgst": 0,
                    "total": 0.008559
                },
                "total": 1.556109
            },
            "total": 1500
        }
    ]
}
```

---

## Test Summary

**Completed:** 2025-11-15 06:09:32

✅ Order Preview API tested successfully.

### ⚠️  Untested Endpoints (REAL MONEY - DO NOT TEST):

1. ❌ **Place Order** - `POST /api/v1/orders/place`
   - ⚠️  Places actual order on exchange
   - ⚠️  Uses real money

2. ❌ **Modify Order** - `POST /api/v1/orders/modify`
   - ⚠️  Modifies existing order
   - ⚠️  Uses real money

3. ❌ **Cancel Order** - `POST /api/v1/orders/cancel`
   - ⚠️  Cancels existing order
   - ⚠️  Uses real money

**Note:** These endpoints should only be tested in a live trading environment
when you are ready to place actual orders.
