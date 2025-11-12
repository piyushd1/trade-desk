# 06 - Risk Management System

[← Back to Master PRD](MASTER_PRD.md)

---

## 🛡️ Risk Management Overview

### Philosophy
**"Protect capital first, make profits second."**

The risk management system is designed with multiple layers of protection to prevent catastrophic losses. Every order goes through multiple risk checks before execution.

### Priority: 🔴 P0 (Critical - Must Have from Day 1)

---

## 🎯 Risk Management Layers

```
┌─────────────────────────────────────────────────────────────────┐
│                      Risk Management Layers                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Layer 1: Pre-Trade Risk Checks                                  │
│  ├─ Position size validation                                     │
│  ├─ Available margin check                                       │
│  ├─ Max positions limit                                          │
│  └─ Instrument trading hours                                     │
│                                                                   │
│  Layer 2: Order-Level Controls                                   │
│  ├─ Order per second (OPS) limit monitoring                      │
│  ├─ Maximum order value                                          │
│  ├─ Price sanity checks                                          │
│  └─ Duplicate order prevention                                   │
│                                                                   │
│  Layer 3: Position-Level Controls                                │
│  ├─ Position limits per instrument                               │
│  ├─ Sector exposure limits                                       │
│  ├─ Portfolio concentration limits                               │
│  └─ Overnight position limits                                    │
│                                                                   │
│  Layer 4: Loss Controls                                          │
│  ├─ Stop loss per trade                                          │
│  ├─ Daily loss limits                                            │
│  ├─ Weekly/Monthly loss limits                                   │
│  └─ Drawdown limits                                              │
│                                                                   │
│  Layer 5: Strategy-Level Controls                                │
│  ├─ Strategy-specific limits                                     │
│  ├─ Strategy performance monitoring                              │
│  ├─ Auto-pause on underperformance                               │
│  └─ Strategy correlation checks                                  │
│                                                                   │
│  Layer 6: System-Level Controls                                  │
│  ├─ Emergency kill switch                                        │
│  ├─ Circuit breakers                                             │
│  ├─ Market volatility checks                                     │
│  └─ System health monitoring                                     │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Layer 1: Pre-Trade Risk Checks

### 1. Position Size Validation

```python
class PositionSizeValidator:
    """
    Validates position sizes before order placement.
    """
    
    def __init__(self, config: Dict):
        self.max_position_value = config.get("max_position_value", 50000)  # ₹50K per position
        self.max_position_pct = config.get("max_position_pct", 25)  # 25% of portfolio
    
    def validate(self, symbol: str, quantity: int, price: float, portfolio_value: float) -> Dict:
        """
        Validate if position size is within limits.
        
        Returns:
            {
                "valid": bool,
                "reason": str (if invalid),
                "adjusted_quantity": int (suggested quantity if invalid)
            }
        """
        position_value = quantity * price
        
        # Check absolute position value
        if position_value > self.max_position_value:
            adjusted_quantity = int(self.max_position_value / price)
            return {
                "valid": False,
                "reason": f"Position value ₹{position_value:,.2f} exceeds max ₹{self.max_position_value:,.2f}",
                "adjusted_quantity": adjusted_quantity
            }
        
        # Check portfolio percentage
        position_pct = (position_value / portfolio_value) * 100
        if position_pct > self.max_position_pct:
            max_allowed_value = (self.max_position_pct / 100) * portfolio_value
            adjusted_quantity = int(max_allowed_value / price)
            return {
                "valid": False,
                "reason": f"Position would be {position_pct:.1f}% of portfolio (max {self.max_position_pct}%)",
                "adjusted_quantity": adjusted_quantity
            }
        
        return {
            "valid": True,
            "reason": None,
            "adjusted_quantity": quantity
        }
```

### 2. Available Margin Check

```python
def check_margin_availability(
    broker: BaseBroker,
    order_value: float,
    product: str
) -> bool:
    """
    Check if sufficient margin is available.
    
    Args:
        broker: Broker instance
        order_value: Total value of the order
        product: CNC, MIS, NRML
    
    Returns:
        True if sufficient margin, False otherwise
    """
    margins = broker.get_margins()
    
    # Different products have different margin requirements
    margin_multipliers = {
        "CNC": 1.0,  # 100% margin for delivery
        "MIS": 0.2,  # ~20% for intraday (varies by broker)
        "NRML": 0.4  # ~40% for F&O
    }
    
    required_margin = order_value * margin_multipliers.get(product, 1.0)
    available_margin = margins.get("available", {}).get("cash", 0)
    
    # Keep 10% buffer
    buffer = required_margin * 0.1
    
    return available_margin >= (required_margin + buffer)
```

### 3. Max Positions Limit

```python
class MaxPositionsValidator:
    """
    Ensures maximum number of positions is not exceeded.
    """
    
    def __init__(self, max_positions: int = 5):
        self.max_positions = max_positions
    
    def validate(self, current_positions: int, new_order_creates_position: bool) -> Dict:
        """
        Check if new position can be opened.
        
        Returns:
            {
                "valid": bool,
                "reason": str (if invalid)
            }
        """
        if not new_order_creates_position:
            # Order is closing/reducing existing position
            return {"valid": True}
        
        if current_positions >= self.max_positions:
            return {
                "valid": False,
                "reason": f"Maximum positions limit ({self.max_positions}) reached"
            }
        
        return {"valid": True}
```

---

## Layer 2: Order-Level Controls

### 1. Orders Per Second (OPS) Monitoring

```python
class OPSMonitor:
    """
    Monitor and enforce SEBI's Orders Per Second limits.
    Current limit: 120 OPS for commodities (rolling 5-second window)
    """
    
    def __init__(self, ops_limit: int = 10):  # We use 10 OPS (12x safety margin)
        self.ops_limit = ops_limit
        self.window_seconds = 5
        self.order_timestamps = deque()
        self.lock = Lock()
    
    def can_place_order(self) -> Dict:
        """
        Check if order can be placed without exceeding OPS limit.
        
        Returns:
            {
                "allowed": bool,
                "current_ops": int,
                "wait_time": float (seconds to wait if not allowed)
            }
        """
        with self.lock:
            now = time.time()
            
            # Remove orders outside the window
            while self.order_timestamps and (now - self.order_timestamps[0]) > self.window_seconds:
                self.order_timestamps.popleft()
            
            current_ops = len(self.order_timestamps) / self.window_seconds
            
            if len(self.order_timestamps) >= (self.ops_limit * self.window_seconds):
                # Calculate wait time
                oldest_order = self.order_timestamps[0]
                wait_time = self.window_seconds - (now - oldest_order)
                
                return {
                    "allowed": False,
                    "current_ops": current_ops,
                    "wait_time": max(0, wait_time)
                }
            
            return {
                "allowed": True,
                "current_ops": current_ops,
                "wait_time": 0
            }
    
    def record_order(self):
        """Record that an order was placed."""
        with self.lock:
            self.order_timestamps.append(time.time())
    
    def get_current_ops(self) -> float:
        """Get current OPS rate."""
        with self.lock:
            now = time.time()
            
            # Remove old timestamps
            while self.order_timestamps and (now - self.order_timestamps[0]) > self.window_seconds:
                self.order_timestamps.popleft()
            
            if not self.order_timestamps:
                return 0.0
            
            time_span = now - self.order_timestamps[0]
            if time_span == 0:
                return len(self.order_timestamps)
            
            return len(self.order_timestamps) / time_span
```

### 2. Price Sanity Checks

```python
class PriceSanityChecker:
    """
    Validates order prices to prevent fat-finger errors.
    """
    
    def __init__(self):
        self.max_deviation_pct = 5.0  # 5% from LTP
    
    def validate_price(
        self,
        order_price: float,
        order_type: str,
        ltp: float,
        transaction_type: str
    ) -> Dict:
        """
        Validate order price against LTP.
        
        Returns:
            {
                "valid": bool,
                "reason": str (if invalid),
                "deviation_pct": float
            }
        """
        # Market orders always valid
        if order_type in ["MARKET", "SL-M"]:
            return {"valid": True}
        
        # Calculate deviation
        deviation = abs(order_price - ltp) / ltp * 100
        
        # Check if deviation exceeds limit
        if deviation > self.max_deviation_pct:
            return {
                "valid": False,
                "reason": f"Price ₹{order_price} deviates {deviation:.1f}% from LTP ₹{ltp} (max {self.max_deviation_pct}%)",
                "deviation_pct": deviation
            }
        
        # Additional check: Buy orders should not be too high, sell orders should not be too low
        if transaction_type == "BUY" and order_price > ltp * 1.05:
            return {
                "valid": False,
                "reason": f"Buy price ₹{order_price} is 5% higher than LTP ₹{ltp}",
                "deviation_pct": deviation
            }
        
        if transaction_type == "SELL" and order_price < ltp * 0.95:
            return {
                "valid": False,
                "reason": f"Sell price ₹{order_price} is 5% lower than LTP ₹{ltp}",
                "deviation_pct": deviation
            }
        
        return {
            "valid": True,
            "deviation_pct": deviation
        }
```

### 3. Duplicate Order Prevention

```python
class DuplicateOrderPreventer:
    """
    Prevents accidental duplicate orders.
    """
    
    def __init__(self, cooldown_seconds: int = 5):
        self.cooldown_seconds = cooldown_seconds
        self.recent_orders = {}  # {order_hash: timestamp}
        self.lock = Lock()
    
    def get_order_hash(self, order: Dict) -> str:
        """Generate unique hash for an order."""
        key = f"{order['symbol']}:{order['transaction_type']}:{order['quantity']}:{order['price']}"
        return hashlib.md5(key.encode()).hexdigest()
    
    def check_duplicate(self, order: Dict) -> Dict:
        """
        Check if order is a duplicate.
        
        Returns:
            {
                "is_duplicate": bool,
                "reason": str (if duplicate)
            }
        """
        with self.lock:
            order_hash = self.get_order_hash(order)
            now = time.time()
            
            # Clean old entries
            expired_hashes = [
                h for h, t in self.recent_orders.items()
                if now - t > self.cooldown_seconds
            ]
            for h in expired_hashes:
                del self.recent_orders[h]
            
            # Check if duplicate
            if order_hash in self.recent_orders:
                time_since = now - self.recent_orders[order_hash]
                return {
                    "is_duplicate": True,
                    "reason": f"Identical order placed {time_since:.1f} seconds ago (cooldown: {self.cooldown_seconds}s)"
                }
            
            # Record order
            self.recent_orders[order_hash] = now
            
            return {"is_duplicate": False}
```

---

## Layer 3: Position-Level Controls

### 1. Position Limits Per Instrument

```python
class InstrumentPositionLimiter:
    """
    Limits position size per instrument.
    """
    
    def __init__(self):
        self.max_quantity_per_instrument = {}  # Custom limits per instrument
        self.default_max_quantity = 100
    
    def set_limit(self, symbol: str, max_quantity: int):
        """Set custom limit for an instrument."""
        self.max_quantity_per_instrument[symbol] = max_quantity
    
    def validate(self, symbol: str, new_quantity: int, current_quantity: int = 0) -> Dict:
        """
        Check if position is within limits.
        
        Returns:
            {
                "valid": bool,
                "reason": str (if invalid),
                "max_allowed": int
            }
        """
        max_allowed = self.max_quantity_per_instrument.get(symbol, self.default_max_quantity)
        total_quantity = abs(current_quantity + new_quantity)
        
        if total_quantity > max_allowed:
            return {
                "valid": False,
                "reason": f"Total position {total_quantity} exceeds limit {max_allowed} for {symbol}",
                "max_allowed": max_allowed
            }
        
        return {
            "valid": True,
            "max_allowed": max_allowed
        }
```

### 2. Sector Exposure Limits

```python
class SectorExposureLimiter:
    """
    Limits exposure to any single sector.
    """
    
    def __init__(self):
        self.max_sector_exposure_pct = 40  # Max 40% in any sector
        self.instrument_sectors = {}  # {symbol: sector}
    
    def load_sector_mapping(self):
        """Load instrument to sector mapping."""
        # Load from database or file
        pass
    
    def validate(self, symbol: str, position_value: float, portfolio_value: float, current_positions: Dict) -> Dict:
        """
        Check sector exposure limits.
        
        Returns:
            {
                "valid": bool,
                "reason": str (if invalid),
                "sector": str,
                "current_exposure_pct": float
            }
        """
        sector = self.instrument_sectors.get(symbol, "Unknown")
        
        # Calculate current sector exposure
        sector_value = sum(
            pos['value'] for sym, pos in current_positions.items()
            if self.instrument_sectors.get(sym) == sector
        )
        
        # Add new position value
        new_sector_value = sector_value + position_value
        sector_exposure_pct = (new_sector_value / portfolio_value) * 100
        
        if sector_exposure_pct > self.max_sector_exposure_pct:
            return {
                "valid": False,
                "reason": f"Sector '{sector}' exposure would be {sector_exposure_pct:.1f}% (max {self.max_sector_exposure_pct}%)",
                "sector": sector,
                "current_exposure_pct": sector_exposure_pct
            }
        
        return {
            "valid": True,
            "sector": sector,
            "current_exposure_pct": sector_exposure_pct
        }
```

---

## Layer 4: Loss Controls

### 1. Stop Loss Per Trade

```python
class StopLossManager:
    """
    Manages stop losses for individual positions.
    """
    
    def __init__(self):
        self.stop_losses = {}  # {symbol: {"price": float, "quantity": int}}
    
    def set_stop_loss(self, symbol: str, entry_price: float, quantity: int, stop_loss_pct: float):
        """
        Set stop loss for a position.
        
        Args:
            symbol: Trading symbol
            entry_price: Entry price
            quantity: Position quantity
            stop_loss_pct: Stop loss percentage (e.g., 2.0 for 2%)
        """
        # Calculate stop loss price
        if quantity > 0:  # Long position
            sl_price = entry_price * (1 - stop_loss_pct / 100)
        else:  # Short position
            sl_price = entry_price * (1 + stop_loss_pct / 100)
        
        self.stop_losses[symbol] = {
            "price": sl_price,
            "quantity": abs(quantity),
            "entry_price": entry_price,
            "stop_loss_pct": stop_loss_pct
        }
    
    def check_stop_loss(self, symbol: str, current_price: float) -> Dict:
        """
        Check if stop loss is triggered.
        
        Returns:
            {
                "triggered": bool,
                "sl_price": float,
                "current_price": float,
                "loss_pct": float
            }
        """
        if symbol not in self.stop_losses:
            return {"triggered": False}
        
        sl = self.stop_losses[symbol]
        
        # For long positions
        if current_price <= sl["price"]:
            loss_pct = ((current_price - sl["entry_price"]) / sl["entry_price"]) * 100
            return {
                "triggered": True,
                "sl_price": sl["price"],
                "current_price": current_price,
                "loss_pct": loss_pct,
                "quantity": sl["quantity"]
            }
        
        return {"triggered": False}
    
    def remove_stop_loss(self, symbol: str):
        """Remove stop loss after position is closed."""
        if symbol in self.stop_losses:
            del self.stop_losses[symbol]
```

### 2. Daily Loss Limit

```python
class DailyLossLimiter:
    """
    Enforces daily loss limits.
    """
    
    def __init__(self, max_daily_loss: float = 5000):
        self.max_daily_loss = max_daily_loss
        self.daily_pnl = 0
        self.last_reset_date = datetime.now().date()
    
    def reset_if_new_day(self):
        """Reset daily P&L if it's a new day."""
        today = datetime.now().date()
        if today != self.last_reset_date:
            self.daily_pnl = 0
            self.last_reset_date = today
    
    def update_pnl(self, pnl: float):
        """Update daily P&L."""
        self.reset_if_new_day()
        self.daily_pnl += pnl
    
    def can_trade(self) -> Dict:
        """
        Check if trading is allowed based on daily loss.
        
        Returns:
            {
                "allowed": bool,
                "reason": str (if not allowed),
                "current_loss": float,
                "max_loss": float
            }
        """
        self.reset_if_new_day()
        
        if self.daily_pnl < -self.max_daily_loss:
            return {
                "allowed": False,
                "reason": f"Daily loss limit reached: ₹{abs(self.daily_pnl):,.2f} (max ₹{self.max_daily_loss:,.2f})",
                "current_loss": self.daily_pnl,
                "max_loss": self.max_daily_loss
            }
        
        return {
            "allowed": True,
            "current_loss": self.daily_pnl,
            "max_loss": self.max_daily_loss,
            "remaining": self.max_daily_loss + self.daily_pnl
        }
```

### 3. Drawdown Limit

```python
class DrawdownLimiter:
    """
    Monitors and limits maximum drawdown.
    """
    
    def __init__(self, max_drawdown_pct: float = 15):
        self.max_drawdown_pct = max_drawdown_pct
        self.peak_portfolio_value = 0
        self.current_drawdown_pct = 0
    
    def update(self, current_portfolio_value: float) -> Dict:
        """
        Update peak and calculate current drawdown.
        
        Returns:
            {
                "breached": bool,
                "current_drawdown_pct": float,
                "peak_value": float,
                "current_value": float
            }
        """
        # Update peak
        if current_portfolio_value > self.peak_portfolio_value:
            self.peak_portfolio_value = current_portfolio_value
        
        # Calculate drawdown
        if self.peak_portfolio_value > 0:
            self.current_drawdown_pct = (
                (self.peak_portfolio_value - current_portfolio_value) / 
                self.peak_portfolio_value * 100
            )
        
        # Check if breached
        breached = self.current_drawdown_pct > self.max_drawdown_pct
        
        return {
            "breached": breached,
            "current_drawdown_pct": self.current_drawdown_pct,
            "max_drawdown_pct": self.max_drawdown_pct,
            "peak_value": self.peak_portfolio_value,
            "current_value": current_portfolio_value
        }
```

---

## Layer 5: Strategy-Level Controls

### Strategy Performance Monitor

```python
class StrategyPerformanceMonitor:
    """
    Monitors strategy performance and auto-pauses underperforming strategies.
    """
    
    def __init__(self):
        self.min_trades_for_evaluation = 20
        self.min_win_rate = 45  # 45%
        self.max_consecutive_losses = 5
    
    def evaluate_strategy(self, strategy_id: int) -> Dict:
        """
        Evaluate strategy performance.
        
        Returns:
            {
                "should_pause": bool,
                "reason": str,
                "metrics": Dict
            }
        """
        # Fetch strategy trades from database
        trades = self.get_strategy_trades(strategy_id)
        
        if len(trades) < self.min_trades_for_evaluation:
            return {"should_pause": False, "reason": "Insufficient trades for evaluation"}
        
        # Calculate metrics
        winning_trades = sum(1 for t in trades if t['pnl'] > 0)
        win_rate = (winning_trades / len(trades)) * 100
        
        # Check consecutive losses
        consecutive_losses = 0
        for trade in reversed(trades):
            if trade['pnl'] < 0:
                consecutive_losses += 1
            else:
                break
        
        metrics = {
            "total_trades": len(trades),
            "win_rate": win_rate,
            "consecutive_losses": consecutive_losses
        }
        
        # Check if should pause
        if win_rate < self.min_win_rate:
            return {
                "should_pause": True,
                "reason": f"Win rate {win_rate:.1f}% below minimum {self.min_win_rate}%",
                "metrics": metrics
            }
        
        if consecutive_losses >= self.max_consecutive_losses:
            return {
                "should_pause": True,
                "reason": f"{consecutive_losses} consecutive losses (max {self.max_consecutive_losses})",
                "metrics": metrics
            }
        
        return {
            "should_pause": False,
            "metrics": metrics
        }
```

---

## Layer 6: System-Level Controls

### 1. Emergency Kill Switch

```python
class EmergencyKillSwitch:
    """
    Emergency mechanism to stop all trading immediately.
    """
    
    def __init__(self):
        self.is_activated = False
        self.activation_reason = None
        self.activated_at = None
        self.activated_by = None
    
    def activate(self, reason: str, user_id: int):
        """
        Activate emergency kill switch.
        
        Actions:
        1. Stop all active strategies
        2. Cancel all pending orders
        3. Optionally close all positions (configurable)
        4. Block new orders
        5. Send emergency alerts
        """
        self.is_activated = True
        self.activation_reason = reason
        self.activated_at = datetime.now()
        self.activated_by = user_id
        
        logging.critical(f"EMERGENCY KILL SWITCH ACTIVATED: {reason}")
        
        # Stop all strategies
        self.stop_all_strategies()
        
        # Cancel all pending orders
        self.cancel_all_pending_orders()
        
        # Send alerts
        self.send_emergency_alerts()
        
        # Audit log
        self.log_kill_switch_activation()
    
    def deactivate(self, user_id: int):
        """Deactivate kill switch (requires manual action)."""
        logging.info(f"Kill switch deactivated by user {user_id}")
        self.is_activated = False
        self.activation_reason = None
    
    def is_trading_allowed(self) -> bool:
        """Check if trading is allowed."""
        return not self.is_activated
```

### 2. Circuit Breakers

```python
class CircuitBreaker:
    """
    Automatic circuit breakers for abnormal market conditions.
    """
    
    def __init__(self):
        self.triggers = {
            "high_volatility": {"threshold": 5.0, "enabled": True},  # 5% move in 5 mins
            "rapid_losses": {"threshold": 3000, "window": 300, "enabled": True},  # ₹3K loss in 5 mins
            "api_errors": {"threshold": 10, "window": 60, "enabled": True},  # 10 errors in 1 min
            "order_rejections": {"threshold": 5, "window": 60, "enabled": True}  # 5 rejections in 1 min
        }
        
        self.breakers_tripped = {}
    
    def check_high_volatility(self, symbol: str, price_change_pct: float) -> bool:
        """Check if volatility circuit breaker should trip."""
        if not self.triggers["high_volatility"]["enabled"]:
            return False
        
        threshold = self.triggers["high_volatility"]["threshold"]
        if abs(price_change_pct) >= threshold:
            self.trip_breaker("high_volatility", f"{symbol} moved {price_change_pct:.2f}% rapidly")
            return True
        
        return False
    
    def check_rapid_losses(self, recent_pnl: float) -> bool:
        """Check if rapid loss circuit breaker should trip."""
        if not self.triggers["rapid_losses"]["enabled"]:
            return False
        
        threshold = self.triggers["rapid_losses"]["threshold"]
        if recent_pnl < -threshold:
            self.trip_breaker("rapid_losses", f"Lost ₹{abs(recent_pnl):,.2f} rapidly")
            return True
        
        return False
    
    def trip_breaker(self, breaker_type: str, reason: str):
        """Trip a circuit breaker."""
        logging.warning(f"CIRCUIT BREAKER TRIPPED: {breaker_type} - {reason}")
        
        self.breakers_tripped[breaker_type] = {
            "reason": reason,
            "tripped_at": datetime.now()
        }
        
        # Take action based on breaker type
        self.handle_tripped_breaker(breaker_type)
    
    def handle_tripped_breaker(self, breaker_type: str):
        """Handle tripped circuit breaker."""
        actions = {
            "high_volatility": self.pause_affected_strategies,
            "rapid_losses": self.pause_all_strategies,
            "api_errors": self.switch_to_backup_broker,
            "order_rejections": self.pause_new_orders
        }
        
        action = actions.get(breaker_type)
        if action:
            action()
    
    def reset_breaker(self, breaker_type: str):
        """Reset a circuit breaker (manual action)."""
        if breaker_type in self.breakers_tripped:
            del self.breakers_tripped[breaker_type]
            logging.info(f"Circuit breaker reset: {breaker_type}")
```

---

## ðŸš¦ Risk Check Workflow

### Order Placement Flow with Risk Checks

```
Order Request
      │
      ▼
┌─────────────────────────────────────────┐
│ 1. Pre-Trade Risk Checks                │
│    - Position size validation            │
│    - Margin availability                 │
│    - Max positions limit                 │
│    - Trading hours check                 │
└─────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────┐
│ 2. Order-Level Controls                 │
│    - OPS limit check                     │
│    - Price sanity check                  │
│    - Duplicate order check               │
└─────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────┐
│ 3. Position-Level Controls              │
│    - Instrument position limit           │
│    - Sector exposure limit               │
│    - Portfolio concentration             │
└─────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────┐
│ 4. Loss Controls                        │
│    - Daily loss limit check              │
│    - Drawdown limit check                │
└─────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────┐
│ 5. System Controls                      │
│    - Kill switch check                   │
│    - Circuit breaker check               │
│    - Market volatility check             │
└─────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────┐
│ All Checks Passed?                      │
│    YES → Place Order                     │
│    NO  → Reject with Reason              │
└─────────────────────────────────────────┘
```

### Implementation

```python
class RiskManager:
    """
    Central risk management system.
    All orders must pass through risk checks.
    """
    
    def __init__(self, config: Dict):
        self.config = config
        
        # Initialize all risk components
        self.position_size_validator = PositionSizeValidator(config)
        self.ops_monitor = OPSMonitor(config.get("ops_limit", 10))
        self.price_sanity_checker = PriceSanityChecker()
        self.duplicate_preventer = DuplicateOrderPreventer()
        self.position_limiter = InstrumentPositionLimiter()
        self.sector_limiter = SectorExposureLimiter()
        self.daily_loss_limiter = DailyLossLimiter(config.get("max_daily_loss", 5000))
        self.drawdown_limiter = DrawdownLimiter(config.get("max_drawdown_pct", 15))
        self.stop_loss_manager = StopLossManager()
        self.kill_switch = EmergencyKillSwitch()
        self.circuit_breaker = CircuitBreaker()
    
    def validate_order(self, order: Dict, context: Dict) -> Dict:
        """
        Validate order against all risk checks.
        
        Args:
            order: Order details
            context: Current portfolio/market context
        
        Returns:
            {
                "valid": bool,
                "checks": List[Dict],  # Results of each check
                "reason": str (if invalid)
            }
        """
        checks = []
        
        # Layer 1: Pre-Trade Checks
        position_size_check = self.position_size_validator.validate(
            order['symbol'],
            order['quantity'],
            order.get('price', context['ltp']),
            context['portfolio_value']
        )
        checks.append({"name": "Position Size", "result": position_size_check})
        if not position_size_check['valid']:
            return {"valid": False, "checks": checks, "reason": position_size_check['reason']}
        
        # Check margin
        if not check_margin_availability(context['broker'], order['value'], order['product']):
            checks.append({"name": "Margin", "result": {"valid": False}})
            return {"valid": False, "checks": checks, "reason": "Insufficient margin"}
        checks.append({"name": "Margin", "result": {"valid": True}})
        
        # Layer 2: Order-Level Controls
        ops_check = self.ops_monitor.can_place_order()
        checks.append({"name": "OPS Limit", "result": ops_check})
        if not ops_check['allowed']:
            return {"valid": False, "checks": checks, "reason": "OPS limit exceeded"}
        
        price_check = self.price_sanity_checker.validate_price(
            order.get('price', 0),
            order['order_type'],
            context['ltp'],
            order['transaction_type']
        )
        checks.append({"name": "Price Sanity", "result": price_check})
        if not price_check['valid']:
            return {"valid": False, "checks": checks, "reason": price_check['reason']}
        
        duplicate_check = self.duplicate_preventer.check_duplicate(order)
        checks.append({"name": "Duplicate Check", "result": duplicate_check})
        if duplicate_check['is_duplicate']:
            return {"valid": False, "checks": checks, "reason": duplicate_check['reason']}
        
        # Layer 3: Position-Level Controls
        # ... (similar pattern for other checks)
        
        # Layer 4: Loss Controls
        daily_loss_check = self.daily_loss_limiter.can_trade()
        checks.append({"name": "Daily Loss Limit", "result": daily_loss_check})
        if not daily_loss_check['allowed']:
            return {"valid": False, "checks": checks, "reason": daily_loss_check['reason']}
        
        # Layer 6: System Controls
        if not self.kill_switch.is_trading_allowed():
            checks.append({"name": "Kill Switch", "result": {"valid": False}})
            return {"valid": False, "checks": checks, "reason": "Emergency kill switch activated"}
        checks.append({"name": "Kill Switch", "result": {"valid": True}})
        
        # All checks passed
        return {"valid": True, "checks": checks}
```

---

## 📊 Risk Dashboard

### Real-time Risk Monitoring

```
┌─────────────────────────────────────────────────────────────────┐
│ Risk Monitor                                    Status: ✅ OK    │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│ ┌─ Daily Limits ────────────────────────────────────────────┐   │
│ │ Loss Limit:     ₹3,500 / ₹5,000  (70% used) ⚠️           │   │
│ │ Max Trades:     35 / 50                                    │   │
│ │ OPS:            5.2 / 10.0                                 │   │
│ └──────────────────────────────────────────────────────────────┘│
│                                                                   │
│ ┌─ Position Limits ─────────────────────────────────────────┐   │
│ │ Open Positions: 3 / 5                                      │   │
│ │ Max Position:   ₹45,000 / ₹50,000                         │   │
│ │ Sector Exp:     35% (IT) / 40% max                        │   │
│ └──────────────────────────────────────────────────────────────┘│
│                                                                   │
│ ┌─ Drawdown Monitor ────────────────────────────────────────┐   │
│ │ Peak Value:     ₹2,15,000                                  │   │
│ │ Current Value:  ₹2,08,500                                  │   │
│ │ Drawdown:       3.02% / 15% max   ✅                       │   │
│ │                                                             │   │
│ │ [━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━] 20% of max        │   │
│ └──────────────────────────────────────────────────────────────┘│
│                                                                   │
│ ┌─ Circuit Breakers ────────────────────────────────────────┐   │
│ │ High Volatility:     ✅ OK                                 │   │
│ │ Rapid Losses:        ✅ OK                                 │   │
│ │ API Errors:          ✅ OK                                 │   │
│ │ Order Rejections:    ✅ OK                                 │   │
│ └──────────────────────────────────────────────────────────────┘│
│                                                                   │
│ ┌─ Emergency Controls ──────────────────────────────────────┐   │
│ │ Kill Switch:         ✅ Inactive                           │   │
│ │ [🚨 ACTIVATE KILL SWITCH]                                 │   │
│ └──────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

---

**Next:** Review [Implementation Plan →](07_IMPLEMENTATION_PLAN.md)

---

*Last Updated: November 11, 2025*
