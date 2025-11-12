"""
Risk Manager Service
Centralized risk management and pre-trade checks
"""

import logging
from datetime import datetime, timedelta, timezone, time as dt_time
from typing import Dict, Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
import asyncio
from collections import deque

from app.database import AsyncSessionLocal
from app.models import RiskConfig, DailyRiskMetrics, Position, Order
from app.models.audit import RiskBreachLog
from app.services.audit_service import audit_service
from app.config import settings

logger = logging.getLogger(__name__)


class RiskCheckResult:
    """Result of a risk check"""
    
    def __init__(self, passed: bool, reason: str = "", breach_type: str = "", details: Dict = None):
        self.passed = passed
        self.reason = reason
        self.breach_type = breach_type
        self.details = details or {}
    
    def __bool__(self):
        return self.passed
    
    def __repr__(self):
        status = "PASS" if self.passed else "FAIL"
        return f"<RiskCheckResult({status}: {self.reason})>"


class RiskManager:
    """
    Centralized risk management service
    
    Implements multiple layers of risk controls:
    - Pre-trade risk checks
    - Position limits
    - Loss limits
    - OPS (Orders Per Second) limits
    - Kill switch
    """
    
    def __init__(self):
        self.ops_tracker = {}  # Track orders per second per user
        self.ops_window = 1  # 1 second window
        self._lock = asyncio.Lock()
    
    async def get_risk_config(self, user_id: Optional[int] = None, db: Optional[AsyncSession] = None) -> RiskConfig:
        """
        Get risk configuration for user or system-wide defaults
        
        Args:
            user_id: User ID (None for system-wide)
            db: Database session
        
        Returns:
            RiskConfig: Risk configuration
        """
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True
        
        try:
            # Try to get user-specific config
            if user_id:
                result = await db.execute(
                    select(RiskConfig).where(RiskConfig.user_id == user_id)
                )
                config = result.scalar_one_or_none()
                if config:
                    return config
            
            # Fall back to system-wide config
            result = await db.execute(
                select(RiskConfig).where(RiskConfig.user_id.is_(None))
            )
            config = result.scalar_one_or_none()
            
            if config:
                return config
            
            # Create default system-wide config if none exists
            config = RiskConfig(
                user_id=None,
                max_position_value=settings.MAX_POSITION_VALUE,
                max_positions=settings.MAX_POSITIONS,
                max_daily_loss=settings.MAX_DAILY_LOSS,
                max_drawdown_pct=settings.MAX_DRAWDOWN_PCT,
                default_stop_loss_pct=settings.DEFAULT_STOP_LOSS_PCT,
                default_target_profit_pct=settings.DEFAULT_TARGET_PROFIT_PCT,
            )
            db.add(config)
            await db.commit()
            await db.refresh(config)
            
            logger.info("Created default system-wide risk configuration")
            return config
        
        finally:
            if should_close:
                await db.close()
    
    async def check_kill_switch(self, user_id: Optional[int] = None, db: Optional[AsyncSession] = None) -> RiskCheckResult:
        """
        Check if trading is enabled (kill switch)
        
        Args:
            user_id: User ID
            db: Database session
        
        Returns:
            RiskCheckResult: Check result
        """
        config = await self.get_risk_config(user_id, db)
        
        if not config.trading_enabled:
            return RiskCheckResult(
                passed=False,
                reason="Trading is disabled (kill switch activated)",
                breach_type="kill_switch",
                details={"user_id": user_id, "trading_enabled": False}
            )
        
        return RiskCheckResult(passed=True, reason="Kill switch check passed")
    
    async def check_position_limits(
        self,
        user_id: int,
        symbol: str,
        quantity: int,
        price: float,
        db: Optional[AsyncSession] = None
    ) -> RiskCheckResult:
        """
        Check position size and count limits
        
        Args:
            user_id: User ID
            symbol: Trading symbol
            quantity: Order quantity
            price: Order price
            db: Database session
        
        Returns:
            RiskCheckResult: Check result
        """
        config = await self.get_risk_config(user_id, db)
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True
        
        try:
            position_value = quantity * price
            
            # Check max position value
            if position_value > config.max_position_value:
                return RiskCheckResult(
                    passed=False,
                    reason=f"Position value ₹{position_value:,.2f} exceeds max ₹{config.max_position_value:,.2f}",
                    breach_type="max_position_value",
                    details={
                        "user_id": user_id,
                        "symbol": symbol,
                        "position_value": position_value,
                        "max_position_value": config.max_position_value
                    }
                )
            
            # Check max positions count
            result = await db.execute(
                select(func.count(Position.id)).where(
                    and_(
                        Position.user_id == user_id,
                        Position.quantity != 0  # Open positions
                    )
                )
            )
            current_positions = result.scalar() or 0
            
            if current_positions >= config.max_positions:
                return RiskCheckResult(
                    passed=False,
                    reason=f"Max positions limit reached ({current_positions}/{config.max_positions})",
                    breach_type="max_positions",
                    details={
                        "user_id": user_id,
                        "current_positions": current_positions,
                        "max_positions": config.max_positions
                    }
                )
            
            return RiskCheckResult(passed=True, reason="Position limits check passed")
        
        finally:
            if should_close:
                await db.close()
    
    async def check_order_limits(
        self,
        user_id: int,
        order_value: float,
        db: Optional[AsyncSession] = None
    ) -> RiskCheckResult:
        """
        Check order value and daily order count limits
        
        Args:
            user_id: User ID
            order_value: Order value
            db: Database session
        
        Returns:
            RiskCheckResult: Check result
        """
        config = await self.get_risk_config(user_id, db)
        
        # Check max order value
        if order_value > config.max_order_value:
            return RiskCheckResult(
                passed=False,
                reason=f"Order value ₹{order_value:,.2f} exceeds max ₹{config.max_order_value:,.2f}",
                breach_type="max_order_value",
                details={
                    "user_id": user_id,
                    "order_value": order_value,
                    "max_order_value": config.max_order_value
                }
            )
        
        # Check daily order count
        metrics = await self.get_daily_metrics(user_id, db)
        if metrics.orders_placed >= config.max_orders_per_day:
            return RiskCheckResult(
                passed=False,
                reason=f"Daily order limit reached ({metrics.orders_placed}/{config.max_orders_per_day})",
                breach_type="max_orders_per_day",
                details={
                    "user_id": user_id,
                    "orders_placed": metrics.orders_placed,
                    "max_orders_per_day": config.max_orders_per_day
                }
            )
        
        return RiskCheckResult(passed=True, reason="Order limits check passed")
    
    async def check_ops_limit(self, user_id: int, db: Optional[AsyncSession] = None) -> RiskCheckResult:
        """
        Check Orders Per Second (OPS) limit
        
        Args:
            user_id: User ID
            db: Database session
        
        Returns:
            RiskCheckResult: Check result
        """
        config = await self.get_risk_config(user_id, db)
        
        async with self._lock:
            now = datetime.now(timezone.utc)
            
            # Initialize tracker for user if not exists
            if user_id not in self.ops_tracker:
                self.ops_tracker[user_id] = deque()
            
            # Remove timestamps older than 1 second
            cutoff = now - timedelta(seconds=self.ops_window)
            while self.ops_tracker[user_id] and self.ops_tracker[user_id][0] < cutoff:
                self.ops_tracker[user_id].popleft()
            
            # Check if limit exceeded
            current_ops = len(self.ops_tracker[user_id])
            if current_ops >= config.ops_limit:
                return RiskCheckResult(
                    passed=False,
                    reason=f"OPS limit exceeded ({current_ops}/{config.ops_limit} orders/sec)",
                    breach_type="ops_limit",
                    details={
                        "user_id": user_id,
                        "current_ops": current_ops,
                        "ops_limit": config.ops_limit
                    }
                )
            
            # Add current timestamp
            self.ops_tracker[user_id].append(now)
        
        return RiskCheckResult(passed=True, reason="OPS limit check passed")
    
    async def check_loss_limits(self, user_id: int, db: Optional[AsyncSession] = None) -> RiskCheckResult:
        """
        Check daily loss limits
        
        Args:
            user_id: User ID
            db: Database session
        
        Returns:
            RiskCheckResult: Check result
        """
        config = await self.get_risk_config(user_id, db)
        metrics = await self.get_daily_metrics(user_id, db)
        
        # Check if daily loss limit already breached
        if metrics.loss_limit_breached:
            return RiskCheckResult(
                passed=False,
                reason=f"Daily loss limit already breached (P&L: ₹{metrics.total_pnl:,.2f})",
                breach_type="daily_loss_limit",
                details={
                    "user_id": user_id,
                    "total_pnl": metrics.total_pnl,
                    "max_daily_loss": config.max_daily_loss
                }
            )
        
        # Check current P&L against limit
        if metrics.total_pnl < -config.max_daily_loss:
            # Mark as breached
            metrics.loss_limit_breached = True
            
            should_close = False
            if db is None:
                db = AsyncSessionLocal()
                should_close = True
            
            try:
                await db.commit()
            finally:
                if should_close:
                    await db.close()
            
            return RiskCheckResult(
                passed=False,
                reason=f"Daily loss limit breached (P&L: ₹{metrics.total_pnl:,.2f}, Limit: ₹{config.max_daily_loss:,.2f})",
                breach_type="daily_loss_limit",
                details={
                    "user_id": user_id,
                    "total_pnl": metrics.total_pnl,
                    "max_daily_loss": config.max_daily_loss
                }
            )
        
        return RiskCheckResult(passed=True, reason="Loss limits check passed")
    
    async def check_trading_hours(self, db: Optional[AsyncSession] = None) -> RiskCheckResult:
        """
        Check if current time is within trading hours
        
        Args:
            db: Database session
        
        Returns:
            RiskCheckResult: Check result
        """
        config = await self.get_risk_config(None, db)
        
        # Get current IST time
        ist = timezone(timedelta(hours=5, minutes=30))
        now_ist = datetime.now(ist)
        current_time = now_ist.time()
        
        # Market hours: 9:15 AM to 3:30 PM IST
        market_open = dt_time(9, 15)
        market_close = dt_time(15, 30)
        
        # Pre-market: 9:00 AM to 9:15 AM
        pre_market_start = dt_time(9, 0)
        
        # After-market: 3:30 PM to 4:00 PM
        after_market_end = dt_time(16, 0)
        
        # Check if in regular market hours
        if market_open <= current_time <= market_close:
            return RiskCheckResult(passed=True, reason="Within regular trading hours")
        
        # Check pre-market
        if pre_market_start <= current_time < market_open:
            if config.allow_pre_market:
                return RiskCheckResult(passed=True, reason="Pre-market trading allowed")
            else:
                return RiskCheckResult(
                    passed=False,
                    reason="Pre-market trading not allowed",
                    breach_type="trading_hours",
                    details={"current_time": current_time.isoformat(), "allow_pre_market": False}
                )
        
        # Check after-market
        if market_close < current_time <= after_market_end:
            if config.allow_after_market:
                return RiskCheckResult(passed=True, reason="After-market trading allowed")
            else:
                return RiskCheckResult(
                    passed=False,
                    reason="After-market trading not allowed",
                    breach_type="trading_hours",
                    details={"current_time": current_time.isoformat(), "allow_after_market": False}
                )
        
        # Outside all trading hours
        return RiskCheckResult(
            passed=False,
            reason=f"Outside trading hours (current time: {current_time.strftime('%H:%M:%S')} IST)",
            breach_type="trading_hours",
            details={"current_time": current_time.isoformat()}
        )
    
    async def pre_trade_check(
        self,
        user_id: int,
        symbol: str,
        quantity: int,
        price: float,
        db: Optional[AsyncSession] = None
    ) -> Tuple[bool, List[RiskCheckResult]]:
        """
        Comprehensive pre-trade risk check
        
        Runs all risk checks and returns aggregated result.
        
        Args:
            user_id: User ID
            symbol: Trading symbol
            quantity: Order quantity
            price: Order price
            db: Database session
        
        Returns:
            Tuple[bool, List[RiskCheckResult]]: (all_passed, list_of_results)
        """
        results = []
        order_value = quantity * price
        
        # Run all checks
        results.append(await self.check_kill_switch(user_id, db))
        results.append(await self.check_trading_hours(db))
        results.append(await self.check_position_limits(user_id, symbol, quantity, price, db))
        results.append(await self.check_order_limits(user_id, order_value, db))
        results.append(await self.check_ops_limit(user_id, db))
        results.append(await self.check_loss_limits(user_id, db))
        
        # Check if all passed
        all_passed = all(result.passed for result in results)
        
        # Log failed checks
        failed_checks = [r for r in results if not r.passed]
        if failed_checks:
            logger.warning(
                f"Pre-trade check failed for user {user_id}, symbol {symbol}: "
                f"{', '.join(r.reason for r in failed_checks)}"
            )
            
            # Log risk breach
            for check in failed_checks:
                await self.log_risk_breach(
                    user_id=user_id,
                    breach_type=check.breach_type,
                    breach_details={
                        "symbol": symbol,
                        "quantity": quantity,
                        "price": price,
                        "order_value": order_value,
                        **check.details
                    },
                    action_taken="order_rejected",
                    db=db
                )
        
        return all_passed, results
    
    async def get_daily_metrics(self, user_id: int, db: Optional[AsyncSession] = None) -> DailyRiskMetrics:
        """
        Get or create daily risk metrics for user
        
        Args:
            user_id: User ID
            db: Database session
        
        Returns:
            DailyRiskMetrics: Daily metrics
        """
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True
        
        try:
            # Get today's date (IST)
            ist = timezone(timedelta(hours=5, minutes=30))
            today = datetime.now(ist).replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Try to get existing metrics
            result = await db.execute(
                select(DailyRiskMetrics).where(
                    and_(
                        DailyRiskMetrics.user_id == user_id,
                        DailyRiskMetrics.trading_date >= today,
                        DailyRiskMetrics.trading_date < today + timedelta(days=1)
                    )
                )
            )
            metrics = result.scalar_one_or_none()
            
            if metrics:
                return metrics
            
            # Create new metrics for today
            metrics = DailyRiskMetrics(
                user_id=user_id,
                trading_date=today
            )
            db.add(metrics)
            await db.commit()
            await db.refresh(metrics)
            
            return metrics
        
        finally:
            if should_close:
                await db.close()
    
    async def log_risk_breach(
        self,
        user_id: int,
        breach_type: str,
        breach_details: Dict,
        action_taken: str,
        strategy_instance_id: Optional[int] = None,
        db: Optional[AsyncSession] = None
    ):
        """
        Log a risk breach to database and audit log
        
        Args:
            user_id: User ID
            breach_type: Type of breach
            breach_details: Breach details
            action_taken: Action taken
            strategy_instance_id: Strategy instance ID (if applicable)
            db: Database session
        """
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True
        
        try:
            # Create risk breach log
            breach_log = RiskBreachLog(
                user_id=user_id,
                strategy_instance_id=strategy_instance_id,
                breach_type=breach_type,
                breach_details=breach_details,
                action_taken=action_taken,
                created_at=datetime.now(timezone.utc)
            )
            db.add(breach_log)
            await db.commit()
            
            # Update daily metrics
            metrics = await self.get_daily_metrics(user_id, db)
            metrics.risk_breaches += 1
            await db.commit()
            
            logger.warning(
                f"Risk breach logged: user={user_id}, type={breach_type}, action={action_taken}"
            )
        
        finally:
            if should_close:
                await db.close()


# Global instance
risk_manager = RiskManager()

