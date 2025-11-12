# 04 - Feature Specifications

[← Back to Master PRD](MASTER_PRD.md)

---

## 🎯 Feature Overview

This document details all features of the algorithmic trading platform, organized by priority and implementation phase.

---

## ðŸ§© Strategy Plugin System

### Overview
A flexible, hot-reloadable strategy plugin system that allows users to implement trading strategies in Python by inheriting from a base Strategy class.

### Priority: 🔴 P0 (Critical)

### Base Strategy Class

```python
# strategies/base_strategy.py

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from enum import Enum
import pandas as pd

class Signal(Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"

class BaseStrategy(ABC):
    """
    Base class for all trading strategies.
    All custom strategies must inherit from this class.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize strategy with configuration.
        
        Args:
            config: Dictionary containing strategy parameters
                   {
                       "instruments": ["NSE:INFY", "NSE:SBIN"],
                       "timeframe": "5min",
                       "max_position_size": 100,
                       "stop_loss_pct": 2.0,
                       "target_profit_pct": 4.0,
                       # ... custom parameters
                   }
        """
        self.config = config
        self.name = self.__class__.__name__
        self.positions = {}  # Current positions
        self.orders = []     # Pending orders
        
    @abstractmethod
    def on_data(self, data: pd.DataFrame) -> List[Dict]:
        """
        Called when new market data is available.
        
        Args:
            data: DataFrame with OHLCV data
                  Columns: ['timestamp', 'open', 'high', 'low', 'close', 'volume']
                  Index: DatetimeIndex
        
        Returns:
            List of order dictionaries:
            [{
                "signal": Signal.BUY,
                "symbol": "NSE:INFY",
                "quantity": 10,
                "order_type": "LIMIT",
                "price": 1450.50,
                "reason": "EMA crossover bullish"
            }]
        """
        pass
    
    @abstractmethod
    def on_order_update(self, order: Dict) -> None:
        """
        Called when order status changes.
        
        Args:
            order: Order dictionary with current status
        """
        pass
    
    @abstractmethod
    def on_trade(self, trade: Dict) -> None:
        """
        Called when a trade is executed.
        
        Args:
            trade: Trade dictionary with execution details
        """
        pass
    
    def calculate_position_size(self, symbol: str, price: float) -> int:
        """
        Calculate position size based on risk management rules.
        Can be overridden by child classes.
        """
        max_position_value = self.config.get("max_position_value", 100000)
        return int(max_position_value / price)
    
    def should_exit(self, symbol: str, current_price: float) -> bool:
        """
        Check if position should be exited based on stop loss/target.
        Can be overridden by child classes.
        """
        if symbol not in self.positions:
            return False
            
        position = self.positions[symbol]
        entry_price = position['average_price']
        quantity = position['quantity']
        
        # Calculate P&L percentage
        if quantity > 0:  # Long position
            pnl_pct = ((current_price - entry_price) / entry_price) * 100
        else:  # Short position
            pnl_pct = ((entry_price - current_price) / entry_price) * 100
        
        stop_loss_pct = self.config.get("stop_loss_pct", 2.0)
        target_profit_pct = self.config.get("target_profit_pct", 4.0)
        
        if pnl_pct <= -stop_loss_pct:
            return True  # Hit stop loss
        if pnl_pct >= target_profit_pct:
            return True  # Hit target
        
        return False
    
    def get_metadata(self) -> Dict:
        """
        Return strategy metadata.
        """
        return {
            "name": self.name,
            "version": getattr(self, "version", "1.0.0"),
            "description": getattr(self, "description", ""),
            "author": getattr(self, "author", "Unknown"),
            "parameters": self.config,
            "instruments": self.config.get("instruments", []),
            "timeframe": self.config.get("timeframe", ""),
        }
```

### Example Strategy: EMA Crossover

```python
# strategies/examples/ema_crossover.py

import pandas as pd
from strategies.base_strategy import BaseStrategy, Signal

class EMACrossoverStrategy(BaseStrategy):
    """
    Simple EMA crossover strategy.
    Buy when fast EMA crosses above slow EMA.
    Sell when fast EMA crosses below slow EMA.
    """
    
    version = "1.0.0"
    description = "EMA crossover momentum strategy"
    author = "Piyush"
    
    def __init__(self, config):
        super().__init__(config)
        
        # Strategy-specific parameters
        self.fast_period = config.get("fast_ema_period", 9)
        self.slow_period = config.get("slow_ema_period", 21)
        
        # State tracking
        self.previous_signal = {}
        
    def on_data(self, data: pd.DataFrame) -> List[Dict]:
        """
        Generate trading signals based on EMA crossover.
        """
        orders = []
        
        for symbol in self.config["instruments"]:
            # Filter data for this symbol
            symbol_data = data[data['symbol'] == symbol].copy()
            
            if len(symbol_data) < self.slow_period:
                continue  # Not enough data
            
            # Calculate EMAs
            symbol_data['ema_fast'] = symbol_data['close'].ewm(
                span=self.fast_period, adjust=False
            ).mean()
            symbol_data['ema_slow'] = symbol_data['close'].ewm(
                span=self.slow_period, adjust=False
            ).mean()
            
            # Get latest values
            latest = symbol_data.iloc[-1]
            previous = symbol_data.iloc[-2] if len(symbol_data) > 1 else None
            
            if previous is None:
                continue
            
            current_price = latest['close']
            
            # Detect crossover
            bullish_cross = (
                previous['ema_fast'] <= previous['ema_slow'] and
                latest['ema_fast'] > latest['ema_slow']
            )
            
            bearish_cross = (
                previous['ema_fast'] >= previous['ema_slow'] and
                latest['ema_fast'] < latest['ema_slow']
            )
            
            # Check if we should exit current position
            if self.should_exit(symbol, current_price):
                if symbol in self.positions and self.positions[symbol]['quantity'] != 0:
                    # Exit position
                    orders.append({
                        "signal": Signal.SELL if self.positions[symbol]['quantity'] > 0 else Signal.BUY,
                        "symbol": symbol,
                        "quantity": abs(self.positions[symbol]['quantity']),
                        "order_type": "MARKET",
                        "reason": "Stop loss or target hit"
                    })
            
            # Entry signals
            elif bullish_cross:
                # Only enter if we don't have a position
                if symbol not in self.positions or self.positions[symbol]['quantity'] == 0:
                    quantity = self.calculate_position_size(symbol, current_price)
                    orders.append({
                        "signal": Signal.BUY,
                        "symbol": symbol,
                        "quantity": quantity,
                        "order_type": "MARKET",
                        "reason": f"Bullish EMA crossover: Fast={latest['ema_fast']:.2f}, Slow={latest['ema_slow']:.2f}"
                    })
            
            elif bearish_cross:
                # Exit long position or enter short (if enabled)
                if symbol in self.positions and self.positions[symbol]['quantity'] > 0:
                    orders.append({
                        "signal": Signal.SELL,
                        "symbol": symbol,
                        "quantity": self.positions[symbol]['quantity'],
                        "order_type": "MARKET",
                        "reason": f"Bearish EMA crossover: Fast={latest['ema_fast']:.2f}, Slow={latest['ema_slow']:.2f}"
                    })
        
        return orders
    
    def on_order_update(self, order: Dict) -> None:
        """Handle order updates."""
        print(f"Order update: {order['order_id']} - {order['status']}")
    
    def on_trade(self, trade: Dict) -> None:
        """Handle trade executions."""
        symbol = trade['symbol']
        quantity = trade['quantity']
        price = trade['price']
        
        # Update positions
        if symbol not in self.positions:
            self.positions[symbol] = {
                'quantity': 0,
                'average_price': 0
            }
        
        if trade['transaction_type'] == 'BUY':
            self.positions[symbol]['quantity'] += quantity
        else:
            self.positions[symbol]['quantity'] -= quantity
        
        # Update average price
        if self.positions[symbol]['quantity'] != 0:
            self.positions[symbol]['average_price'] = price
```

### Strategy Management Features

#### 1. Strategy Registration
```python
# API endpoint to register new strategy
POST /api/strategies/register
{
    "name": "ema_crossover",
    "display_name": "EMA Crossover Strategy",
    "file_path": "/strategies/ema_crossover.py",
    "description": "Simple EMA crossover momentum strategy",
    "parameters": {
        "fast_ema_period": 9,
        "slow_ema_period": 21,
        "max_position_size": 100,
        "stop_loss_pct": 2.0,
        "target_profit_pct": 4.0
    }
}
```

#### 2. Strategy Hot-Reload
- File system watcher monitors strategy directory
- When strategy file changes, system:
  1. Validates new code syntax
  2. Tests strategy instantiation
  3. If successful, reloads strategy without server restart
  4. If validation fails, keeps old version and logs error

#### 3. Strategy Validation
```python
def validate_strategy(file_path: str) -> Dict:
    """
    Validate strategy file before loading.
    
    Returns:
        {
            "valid": bool,
            "errors": List[str],
            "warnings": List[str]
        }
    """
    checks = []
    
    # 1. Check if file exists
    # 2. Check if it's valid Python syntax
    # 3. Check if it inherits from BaseStrategy
    # 4. Check if all abstract methods are implemented
    # 5. Check for security issues (no file system access, no network calls)
    # 6. Check for infinite loops or blocking operations
    
    return validation_result
```

#### 4. Strategy Parameters UI
- Web interface to configure strategy parameters
- Parameter validation based on type hints
- Real-time parameter updates
- Parameter history tracking

---

## ðŸ"Š Backtesting Engine

### Overview
Advanced backtesting system to test strategies on historical data before live deployment.

### Priority: 🔴 P0 (Critical)

### Features

#### 1. Historical Data Backtesting
```python
# Backtest configuration
POST /api/backtest/run
{
    "strategy_id": 1,
    "parameters": {
        "fast_ema_period": 9,
        "slow_ema_period": 21
    },
    "instruments": ["NSE:INFY", "NSE:SBIN"],
    "start_date": "2024-01-01",
    "end_date": "2024-12-31",
    "initial_capital": 200000,
    "commission": 0.03,  // percentage
    "slippage": 0.05     // percentage
}
```

#### 2. Backtest Metrics

| Metric | Formula | Interpretation |
|--------|---------|----------------|
| **Total Return** | (Final - Initial) / Initial * 100 | Overall return % |
| **CAGR** | (Final/Initial)^(1/years) - 1 | Annualized return |
| **Sharpe Ratio** | (Return - RiskFree) / StdDev | Risk-adjusted return |
| **Sortino Ratio** | (Return - RiskFree) / Downside StdDev | Downside risk focus |
| **Max Drawdown** | Max % drop from peak | Worst case scenario |
| **Win Rate** | Winning trades / Total trades | Probability of success |
| **Profit Factor** | Gross Profit / Gross Loss | Profitability measure |
| **Avg Win/Loss Ratio** | Avg Win / Avg Loss | Risk/reward ratio |
| **Total Trades** | Count | Trading frequency |
| **Avg Trade Duration** | Time held per trade | Holding period |

#### 3. Visual Reports
- Equity curve chart
- Drawdown chart
- Trade distribution
- Monthly returns heatmap
- Win/loss histogram
- Rolling Sharpe ratio

#### 4. Walk-Forward Analysis
- Split data into training and testing periods
- Optimize on training, validate on testing
- Prevent overfitting

#### 5. Monte Carlo Simulation
- Simulate 1000+ random scenarios
- Calculate probability of outcomes
- Assess strategy robustness

---

## ðŸ" Paper Trading

### Overview
Simulate live trading without real money to validate strategies in real market conditions.

### Priority: 🔴 P0 (Critical)

### Features

#### 1. Simulated Order Execution
- Match real market prices
- Simulate order fill latency (100-500ms)
- Partial fills based on market depth
- Slippage simulation

#### 2. Real-time Market Data
- Connect to broker WebSocket
- Process live market data
- Generate signals in real-time
- Track simulated positions

#### 3. Paper Trading Dashboard
```
┌─────────────────────────────────────────────────────────────────┐
│ Paper Trading Dashboard                          Status: ACTIVE  │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│ Portfolio Value: ₹2,10,000  (+5.0%)                             │
│ Available Cash: ₹1,80,000                                        │
│ Invested:       ₹30,000                                          │
│ Today's P&L:    ₹+2,500     (+1.25%)                            │
│                                                                   │
├─────────────────────────────────────────────────────────────────┤
│ Active Positions                                                  │
├─────────────────────────────────────────────────────────────────┤
│ Symbol  │ Qty │ Avg Price │ LTP      │ P&L      │ P&L%  │      │
├─────────┼─────┼───────────┼──────────┼──────────┼───────┼──────┤
│ INFY    │  10 │ 1,450.00  │ 1,480.00 │ +300.00  │ +2.07%│ EXIT │
│ SBIN    │  20 │   580.00  │   595.00 │ +300.00  │ +2.59%│ EXIT │
└─────────────────────────────────────────────────────────────────┘
```

#### 4. Paper Trading vs Live Trading Toggle
- Easy switch between paper and live
- All features identical except actual execution
- Compare paper vs live performance

---

## ðŸš€ Live Trading System

### Overview
Production trading system with order execution, position management, and risk controls.

### Priority: 🔴 P0 (Critical)

### Features

#### 1. Order Management

##### Order Types Supported
- **Market Order**: Execute at best available price
- **Limit Order**: Execute at specified price or better
- **Stop Loss (SL)**: Trigger market order when price hits level
- **Stop Loss Market (SL-M)**: Trigger limit order when price hits level

##### Order Varieties
- **Regular**: Standard order
- **Cover Order (CO)**: Order with mandatory stop loss
- **After Market Order (AMO)**: Place orders after market hours
- **Iceberg**: Large orders split into smaller chunks
- **Auction**: Orders for auction sessions

##### Order Placement Flow
```
User/Strategy → Validate Order → Risk Checks → Place with Broker → 
Monitor Status → Update Database → Notify User
```

#### 2. Position Management

##### Features
- Real-time position tracking
- Automatic P&L calculation
- Position limits enforcement
- Auto-square-off capability
- Position reporting

##### Position States
- **OPEN**: Active position
- **CLOSED**: Position fully exited
- **PARTIALLY_CLOSED**: Some quantity exited

#### 3. Execution Modes

##### Fully Automated
- Orders execute automatically based on strategy signals
- No human intervention required
- Fastest execution

##### Semi-Automated (with Approval)
- Strategy generates signals
- User receives notification
- User approves/rejects within timeout (default: 60 seconds)
- Auto-reject after timeout

##### Manual
- User places orders manually
- Strategy provides recommendations
- Full human control

#### 4. Order Routing

```python
# Smart order routing
class OrderRouter:
    def route_order(self, order: Dict) -> Dict:
        """
        Route order to best broker based on:
        - Broker availability
        - Rate limits
        - Order type support
        - Historical performance
        """
        # 1. Check broker API status
        # 2. Check rate limits
        # 3. Select best broker
        # 4. Place order
        # 5. Monitor execution
        return execution_result
```

---

## ðŸ"± Dashboard & UI Components

### Overview
Web-based dashboard for monitoring, control, and analysis.

### Priority: 🟡 P1 (High)

### Key Screens

#### 1. Login & Authentication
```
┌─────────────────────────────────────────────────────────────────┐
│                      Algo Trading Platform                        │
│                                                                   │
│                    ┌───────────────────────┐                    │
│                    │  Email                │                    │
│                    │  [________________]    │                    │
│                    │                        │                    │
│                    │  Password             │                    │
│                    │  [________________]    │                    │
│                    │                        │                    │
│                    │  2FA Code             │                    │
│                    │  [______]              │                    │
│                    │                        │                    │
│                    │  [     LOGIN     ]     │                    │
│                    └───────────────────────┘                    │
│                                                                   │
│                    Forgot Password?  |  Setup 2FA                │
└─────────────────────────────────────────────────────────────────┘
```

#### 2. Main Dashboard
```
┌─────────────────────────────────────────────────────────────────┐
│ [☰] Algo Trading  │ Dashboard │ Strategies │ Orders │ Settings  │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│ ┌─────────────────────┐  ┌─────────────────────┐               │
│ │ Portfolio Value     │  │ Today's P&L         │               │
│ │ ₹2,15,000          │  │ ₹+5,000 (+2.38%)   │               │
│ │ ▲ +7.5% All Time   │  │ ▲ Profit            │               │
│ └─────────────────────┘  └─────────────────────┘               │
│                                                                   │
│ ┌─────────────────────┐  ┌─────────────────────┐               │
│ │ Active Strategies   │  │ Orders Today        │               │
│ │ 3 Running          │  │ 15 / 120 OPS Limit │               │
│ │ 2 Paused           │  │ 13 Filled          │               │
│ └─────────────────────┘  └─────────────────────┘               │
│                                                                   │
│ Portfolio Chart (7 Days)                                         │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │                                            ╱──╲                ││
│ │                                    ╱──────╱    ╲              ││
│ │                          ╱────────╱              ╲            ││
│ │                ╱────────╱                          ╲────╮    ││
│ │ ───────────────╱                                         ╰───││
│ └─────────────────────────────────────────────────────────────┘│
│                                                                   │
│ Active Positions                          [Export] [Refresh]     │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │Symbol │Qty│ Avg Price│ LTP     │  P&L    │ P&L% │  Action ││
│ ├──────┼───┼──────────┼─────────┼─────────┼──────┼─────────┤│
│ │INFY  │ 10│ 1,450.00 │1,480.00 │ +300.00 │+2.07%│ [EXIT] ││
│ │SBIN  │ 20│   580.00 │  595.00 │ +300.00 │+2.59%│ [EXIT] ││
│ └─────────────────────────────────────────────────────────────┘│
│                                                                   │
│ Recent Orders                             [View All]             │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │Time    │Symbol│Type │Qty│Price   │Status  │ Strategy      ││
│ ├────────┼──────┼─────┼───┼────────┼────────┼───────────────┤│
│ │10:30:45│INFY  │BUY  │10 │1,450.00│COMPLETE│EMA Crossover  ││
│ │10:25:12│SBIN  │BUY  │20 │  580.00│COMPLETE│Momentum       ││
│ └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

#### 3. Strategy Management Screen
```
┌─────────────────────────────────────────────────────────────────┐
│ Strategies                                     [+ New Strategy]  │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│ My Strategies                                  [Import] [Export] │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ ╔═══════════════════════════════════════════════════════╗  ││
│ │ ║ EMA Crossover Strategy              [âœ… Running]      ║  ││
│ │ ║ 9/21 EMA crossover momentum                            ║  ││
│ │ ║                                                         ║  ││
│ │ ║ Performance: +15.2% | Win Rate: 62% | Trades: 45      ║  ││
│ │ ║                                                         ║  ││
│ │ ║ [⚙️ Configure] [ðŸ"Š Backtest] [⏸️ Pause] [🗑️ Delete]  ║  ││
│ │ ╚═══════════════════════════════════════════════════════╝  ││
│ │                                                             ││
│ │ ╔═══════════════════════════════════════════════════════╗  ││
│ │ ║ RSI Mean Reversion                  [⏸️ Paused]       ║  ││
│ │ ║ Buy oversold, sell overbought                          ║  ││
│ │ ║                                                         ║  ││
│ │ ║ Performance: +8.5% | Win Rate: 58% | Trades: 32       ║  ││
│ │ ║                                                         ║  ││
│ │ ║ [⚙️ Configure] [ðŸ"Š Backtest] [▶️ Start] [🗑️ Delete]  ║  ││
│ │ ╚═══════════════════════════════════════════════════════╝  ││
│ └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

#### 4. Backtesting Screen
```
┌─────────────────────────────────────────────────────────────────┐
│ Backtest: EMA Crossover Strategy                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│ Configuration                                                     │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ Strategy:     [EMA Crossover ▼]                             ││
│ │ Instruments:  [NSE:INFY, NSE:SBIN, NSE:TCS]                ││
│ │ Start Date:   [2024-01-01]                                  ││
│ │ End Date:     [2024-12-31]                                  ││
│ │ Capital:      [₹2,00,000]                                   ││
│ │ Commission:   [0.03%]                                       ││
│ │ Slippage:     [0.05%]                                       ││
│ │                                                              ││
│ │              [Run Backtest]                                 ││
│ └─────────────────────────────────────────────────────────────┘│
│                                                                   │
│ Results                                                           │
│ ┌───────────────────┐ ┌───────────────────┐ ┌─────────────────┐│
│ │ Total Return      │ │ Sharpe Ratio      │ │ Max Drawdown    ││
│ │ +42.5%           │ │ 1.85              │ │ -12.3%          ││
│ └───────────────────┘ └───────────────────┘ └─────────────────┘│
│                                                                   │
│ Equity Curve                                                      │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ 240k─                                            ╱────╮      ││
│ │      │                                     ╱─────╱     │      ││
│ │ 220k─                              ╱──────╱            │      ││
│ │      │                       ╱─────╱                   ╰──╮   ││
│ │ 200k─────────────────────────╱                            │   ││
│ │      │                                                      ╰─││
│ │ 180k─                                                        ││
│ │      └──────┬──────┬──────┬──────┬──────┬──────┬──────┬────││
│ │           Jan    Mar    May    Jul    Sep    Nov    Dec      ││
│ └─────────────────────────────────────────────────────────────┘│
│                                                                   │
│ Trade Statistics                                                  │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ Total Trades:        125                                    ││
│ │ Winning Trades:       78 (62.4%)                            ││
│ │ Losing Trades:        47 (37.6%)                            ││
│ │ Avg Win:          ₹1,850                                    ││
│ │ Avg Loss:         ₹-950                                     ││
│ │ Profit Factor:     2.15                                     ││
│ │ Avg Trade Duration: 2.3 days                                ││
│ └─────────────────────────────────────────────────────────────┘│
│                                                                   │
│ [Export Report] [Save Results] [Run Walk-Forward]               │
└─────────────────────────────────────────────────────────────────┘
```

#### 5. Order Management Screen
```
┌─────────────────────────────────────────────────────────────────┐
│ Orders                                         [Place Order]      │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│ Filters:  [Today ▼]  [All Status ▼]  [All Strategies ▼]        │
│                                                                   │
│ Orders (15 / 120 OPS Limit)              [Export] [Refresh]     │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │Time     │ID       │Symbol│Side│Qty│Type  │Price│Status    ││
│ ├─────────┼─────────┼──────┼────┼───┼──────┼─────┼──────────┤│
│ │10:30:45 │25111012 │INFY  │BUY │ 10│MARKET│1,450│âœ… COMPLETE││
│ │10:30:40 │25111011 │SBIN  │BUY │ 20│LIMIT │  580│âœ… COMPLETE││
│ │10:25:30 │25111010 │TCS  │SELL│ 15│MARKET│3,750│âœ… COMPLETE││
│ │10:20:15 │25111009 │INFY  │BUY │  5│LIMIT │1,445│⏳ OPEN    ││
│ │10:15:00 │25111008 │SBIN  │SELL│ 10│MARKET│  578│❌ REJECTED││
│ └─────────────────────────────────────────────────────────────┘│
│                                                                   │
│ Order Details: 25111012                          [View Trades]   │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ Order ID:          25111012345                              ││
│ │ Symbol:            NSE:INFY                                 ││
│ │ Transaction Type:  BUY                                      ││
│ │ Order Type:        MARKET                                   ││
│ │ Quantity:          10                                       ││
│ │ Filled:            10                                       ││
│ │ Average Price:     ₹1,450.25                                ││
│ │ Status:            COMPLETE                                 ││
│ │ Placed At:         2025-11-11 10:30:45                      ││
│ │ Exchange Time:     2025-11-11 10:30:46                      ││
│ │ Strategy:          EMA Crossover                            ││
│ │ Algo ID:           ZERODHA_ALGO_001                         ││
│ └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

#### 6. Settings & Configuration
```
┌─────────────────────────────────────────────────────────────────┐
│ Settings                                                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│ ┌─ Account Settings ────────────────────────────────────────┐   │
│ │ Username:       [piyush]                                   │   │
│ │ Email:          [piyush@email.com]                        │   │
│ │ Role:           Admin                                      │   │
│ │ 2FA Status:     âœ… Enabled                                │   │
│ │ Static IP:      [XX.XX.XX.XX]                             │   │
│ │                                                             │   │
│ │ [Change Password] [Update Email] [Manage 2FA]            │   │
│ └─────────────────────────────────────────────────────────────┘│
│                                                                   │
│ ┌─ Broker Connections ──────────────────────────────────────┐   │
│ │ Zerodha Kite Connect                    âœ… Connected       │   │
│ │ - API Key: ******************                              │   │
│ │ - Access Token: Valid until 2025-11-12                    │   │
│ │ - Algo ID: ZERODHA_ALGO_001                               │   │
│ │ - Registered: 2025-08-01                                  │   │
│ │ [Reconnect] [Revoke] [Update Keys]                        │   │
│ │                                                             │   │
│ │ Groww Trade API                         ❌ Disconnected    │   │
│ │ [Connect]                                                  │   │
│ └─────────────────────────────────────────────────────────────┘│
│                                                                   │
│ ┌─ Risk Management ─────────────────────────────────────────┐   │
│ │ Max Position Size:      [₹50,000]                         │   │
│ │ Max Daily Loss:         [₹5,000]                          │   │
│ │ Max Daily Trades:       [50]                              │   │
│ │ Max Open Positions:     [5]                               │   │
│ │ Default Stop Loss:      [2%]                              │   │
│ │ Default Target:         [4%]                              │   │
│ │                                                             │   │
│ │ [Update Limits]                                            │   │
│ └─────────────────────────────────────────────────────────────┘│
│                                                                   │
│ ┌─ Notifications ───────────────────────────────────────────┐   │
│ │ Order Fills:           âœ… Email  ⬜ SMS  ⬜ Telegram       │   │
│ │ Risk Breaches:         âœ… Email  âœ… SMS  ⬜ Telegram       │   │
│ │ Strategy Signals:      ⬜ Email  ⬜ SMS  ⬜ Telegram       │   │
│ │ System Alerts:         âœ… Email  ⬜ SMS  ⬜ Telegram       │   │
│ │                                                             │   │
│ │ [Save Preferences]                                         │   │
│ └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

### UI Components Library

#### Reusable Components
1. **DataTable**: Sortable, filterable data grid
2. **Chart**: TradingView charts for price data
3. **MetricCard**: Display key metrics
4. **OrderForm**: Place manual orders
5. **StrategyCard**: Strategy info display
6. **AlertBanner**: System-wide notifications
7. **ConfirmDialog**: User confirmations
8. **LoadingSpinner**: Loading states

---

## ðŸ"" Real-time Features

### Priority: 🟡 P1 (High)

#### 1. WebSocket Connections
- Real-time price updates
- Order status updates
- Position updates
- System alerts

#### 2. Live Dashboard Updates
- Auto-refresh every 1 second
- No page reload required
- Smooth animations

#### 3. Push Notifications
- Browser notifications for critical events
- Email notifications for important updates
- SMS for emergency situations (optional)

---

## ðŸ"‚ Data Export & Reporting

### Priority: 🟢 P2 (Medium)

#### Export Formats
- CSV
- Excel (XLSX)
- PDF (reports)
- JSON (for API integration)

#### Available Reports
1. **Trade Log**: All trades with details
2. **P&L Report**: Profit/loss by strategy, time period
3. **Tax Report**: Annual tax computation (FIFO/LIFO)
4. **Compliance Report**: SEBI audit trail
5. **Performance Report**: Strategy performance metrics

---

## 🔔 Alerting System

### Priority: 🟢 P2 (Medium)

#### Alert Types
1. **Trade Alerts**: Order fills, rejections
2. **Risk Alerts**: Limit breaches, stop losses
3. **System Alerts**: Errors, downtime
4. **Strategy Alerts**: Signals generated
5. **Market Alerts**: Circuit breaks, halts

#### Alert Channels
- In-app notifications
- Email
- SMS (via Twilio/SNS)
- Telegram bot (future)
- WhatsApp (future)

---

**Next:** Review [Broker Integration & Data Management →](05_DATA_MANAGEMENT.md)

---

*Last Updated: November 11, 2025*
