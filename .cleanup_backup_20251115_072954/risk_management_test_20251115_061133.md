# Risk Management API Test Results

**Test Date:** 2025-11-15 06:11:33
**User ID:** 2 (piyushdev)

**Note:** All Risk Management APIs are public (no JWT required)

---

## 1. Get Risk Config API

**Endpoint:** `GET /api/v1/risk/config`
**Timestamp:** 2025-11-15 06:11:33
**Request:** Get risk configuration for user_id=2

```json
{
    "status": "success",
    "config": {
        "id": 1,
        "user_id": null,
        "max_position_value": 50000.0,
        "max_positions": 5,
        "max_position_pct": 25.0,
        "max_order_value": 100000.0,
        "max_orders_per_day": 50,
        "ops_limit": 15,
        "max_daily_loss": 6000.0,
        "max_weekly_loss": 15000.0,
        "max_monthly_loss": 50000.0,
        "max_drawdown_pct": 15.0,
        "default_stop_loss_pct": 2.0,
        "default_target_profit_pct": 4.0,
        "enforce_stop_loss": true,
        "allow_pre_market": false,
        "allow_after_market": false,
        "trading_enabled": false,
        "additional_limits": null,
        "created_at": "2025-11-12T06:56:23",
        "updated_at": "2025-11-12T12:33:23"
    }
}
```

---

## 2. Kill Switch Status API

**Endpoint:** `GET /api/v1/risk/kill-switch/status`
**Timestamp:** 2025-11-15 06:11:33

```json
{
    "status": "success",
    "trading_enabled": false,
    "user_id": null,
    "config_id": 1
}
```

---

## 3. Risk Status API

**Endpoint:** `GET /api/v1/risk/status`
**Timestamp:** 2025-11-15 06:11:34
**Request:** Get risk status for user_id=2

```json
{
    "status": "success",
    "trading_enabled": false,
    "user_id": 2,
    "limits": {
        "max_position_value": 50000.0,
        "max_positions": 5,
        "max_order_value": 100000.0,
        "max_orders_per_day": 50,
        "ops_limit": 15,
        "max_daily_loss": 6000.0
    },
    "daily_metrics": {
        "orders_placed": 0,
        "orders_executed": 0,
        "orders_rejected": 0,
        "current_positions": 0,
        "total_pnl": 0.0,
        "loss_limit_breached": false,
        "risk_breaches": 1
    },
    "recent_breaches": [
        {
            "breach_type": "kill_switch",
            "action_taken": "order_rejected",
            "created_at": "2025-11-15T06:09:32.748325"
        }
    ]
}
```

---

## 4. Pre-trade Check API

**Endpoint:** `POST /api/v1/risk/pre-trade-check`
**Timestamp:** 2025-11-15 06:11:34
**Request:** Pre-trade risk check for INFY order

**Order Details:**
- Symbol: INFY
- Quantity: 1
- Price: 1500.0

```json
{
    "status": "success",
    "all_passed": false,
    "order_value": 1500.0,
    "checks": [
        {
            "passed": false,
            "reason": "Trading is disabled (kill switch activated)",
            "breach_type": "kill_switch",
            "details": {
                "user_id": 2,
                "trading_enabled": false
            }
        },
        {
            "passed": true,
            "reason": "Within regular trading hours",
            "breach_type": null,
            "details": null
        },
        {
            "passed": true,
            "reason": "Position limits check passed",
            "breach_type": null,
            "details": null
        },
        {
            "passed": true,
            "reason": "Order limits check passed",
            "breach_type": null,
            "details": null
        },
        {
            "passed": true,
            "reason": "OPS limit check passed",
            "breach_type": null,
            "details": null
        },
        {
            "passed": true,
            "reason": "Loss limits check passed",
            "breach_type": null,
            "details": null
        }
    ],
    "message": "One or more checks failed"
}
```

---

## Test Summary

**Completed:** 2025-11-15 06:11:34

All 4 Risk Management API endpoints tested successfully.

### Endpoints Tested:
1. ✅ Get Risk Config (public)
2. ✅ Kill Switch Status (public)
3. ✅ Risk Status (public)
4. ✅ Pre-trade Check (public)

**Note:** All Risk Management APIs are public endpoints and do not require JWT authentication.
