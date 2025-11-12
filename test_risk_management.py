"""
Test script for Risk Management functionality
Tests RiskManager service and risk checks
"""

import asyncio
import sys
sys.path.insert(0, '/home/trade-desk/backend')

from app.services.risk_manager import risk_manager, RiskCheckResult
from app.database import AsyncSessionLocal
from app.models import RiskConfig, DailyRiskMetrics
from sqlalchemy import select


async def test_risk_config():
    """Test risk configuration creation and retrieval"""
    print("\n" + "="*60)
    print("TEST 1: Risk Configuration")
    print("="*60)
    
    async with AsyncSessionLocal() as db:
        # Get or create system-wide config
        config = await risk_manager.get_risk_config(user_id=None, db=db)
        
        print(f"✓ System-wide risk config retrieved")
        print(f"  - Max Position Value: ₹{config.max_position_value:,.2f}")
        print(f"  - Max Positions: {config.max_positions}")
        print(f"  - Max Daily Loss: ₹{config.max_daily_loss:,.2f}")
        print(f"  - OPS Limit: {config.ops_limit} orders/sec")
        print(f"  - Trading Enabled: {config.trading_enabled}")
        print(f"  - Enforce Stop Loss: {config.enforce_stop_loss}")
        
        return config


async def test_kill_switch():
    """Test kill switch functionality"""
    print("\n" + "="*60)
    print("TEST 2: Kill Switch")
    print("="*60)
    
    # Test with trading enabled
    result = await risk_manager.check_kill_switch(user_id=None)
    print(f"✓ Kill switch check (enabled): {result.passed}")
    print(f"  Reason: {result.reason}")
    
    # Disable trading temporarily
    async with AsyncSessionLocal() as db:
        config = await risk_manager.get_risk_config(user_id=None, db=db)
        config.trading_enabled = False
        await db.commit()
    
    result = await risk_manager.check_kill_switch(user_id=None)
    print(f"✓ Kill switch check (disabled): {result.passed}")
    print(f"  Reason: {result.reason}")
    print(f"  Breach Type: {result.breach_type}")
    
    # Re-enable trading
    async with AsyncSessionLocal() as db:
        config = await risk_manager.get_risk_config(user_id=None, db=db)
        config.trading_enabled = True
        await db.commit()
    
    print("✓ Trading re-enabled")


async def test_position_limits():
    """Test position limit checks"""
    print("\n" + "="*60)
    print("TEST 3: Position Limits")
    print("="*60)
    
    user_id = 1  # Test user
    
    # Test 1: Valid position
    result = await risk_manager.check_position_limits(
        user_id=user_id,
        symbol="RELIANCE",
        quantity=10,
        price=2500.0,
        db=None
    )
    print(f"✓ Position check (₹25,000): {result.passed}")
    print(f"  Reason: {result.reason}")
    
    # Test 2: Position exceeds value limit
    result = await risk_manager.check_position_limits(
        user_id=user_id,
        symbol="RELIANCE",
        quantity=100,
        price=2500.0,  # ₹2,50,000 > ₹50,000 limit
        db=None
    )
    print(f"✓ Position check (₹2,50,000): {result.passed}")
    print(f"  Reason: {result.reason}")
    print(f"  Breach Type: {result.breach_type}")


async def test_order_limits():
    """Test order limit checks"""
    print("\n" + "="*60)
    print("TEST 4: Order Limits")
    print("="*60)
    
    user_id = 1
    
    # Test 1: Valid order
    result = await risk_manager.check_order_limits(
        user_id=user_id,
        order_value=25000.0,
        db=None
    )
    print(f"✓ Order check (₹25,000): {result.passed}")
    print(f"  Reason: {result.reason}")
    
    # Test 2: Order exceeds value limit
    result = await risk_manager.check_order_limits(
        user_id=user_id,
        order_value=150000.0,  # > ₹100,000 limit
        db=None
    )
    print(f"✓ Order check (₹1,50,000): {result.passed}")
    print(f"  Reason: {result.reason}")
    print(f"  Breach Type: {result.breach_type}")


async def test_ops_limit():
    """Test Orders Per Second (OPS) limit"""
    print("\n" + "="*60)
    print("TEST 5: OPS Limit")
    print("="*60)
    
    user_id = 1
    
    # Test multiple orders in quick succession
    passed_count = 0
    failed_count = 0
    
    for i in range(15):  # Try 15 orders (limit is 10)
        result = await risk_manager.check_ops_limit(user_id=user_id, db=None)
        if result.passed:
            passed_count += 1
        else:
            failed_count += 1
            if failed_count == 1:  # Print first failure
                print(f"✓ OPS limit triggered after {passed_count} orders")
                print(f"  Reason: {result.reason}")
                print(f"  Breach Type: {result.breach_type}")
    
    print(f"✓ Total: {passed_count} passed, {failed_count} failed")
    
    # Wait and try again
    print("  Waiting 1 second...")
    await asyncio.sleep(1.1)
    
    result = await risk_manager.check_ops_limit(user_id=user_id, db=None)
    print(f"✓ After waiting: {result.passed}")
    print(f"  Reason: {result.reason}")


async def test_loss_limits():
    """Test daily loss limit checks"""
    print("\n" + "="*60)
    print("TEST 6: Loss Limits")
    print("="*60)
    
    user_id = 1
    
    # Get or create daily metrics
    metrics = await risk_manager.get_daily_metrics(user_id=user_id, db=None)
    print(f"✓ Daily metrics retrieved for user {user_id}")
    print(f"  Trading Date: {metrics.trading_date}")
    print(f"  Total P&L: ₹{metrics.total_pnl:,.2f}")
    print(f"  Loss Limit Breached: {metrics.loss_limit_breached}")
    
    # Test 1: No loss
    result = await risk_manager.check_loss_limits(user_id=user_id, db=None)
    print(f"✓ Loss check (no loss): {result.passed}")
    print(f"  Reason: {result.reason}")
    
    # Test 2: Simulate loss exceeding limit
    async with AsyncSessionLocal() as db:
        metrics = await risk_manager.get_daily_metrics(user_id=user_id, db=db)
        metrics.total_pnl = -6000.0  # Exceeds -5000 limit
        await db.commit()
    
    result = await risk_manager.check_loss_limits(user_id=user_id, db=None)
    print(f"✓ Loss check (₹-6,000): {result.passed}")
    print(f"  Reason: {result.reason}")
    print(f"  Breach Type: {result.breach_type}")
    
    # Reset metrics
    async with AsyncSessionLocal() as db:
        metrics = await risk_manager.get_daily_metrics(user_id=user_id, db=db)
        metrics.total_pnl = 0.0
        metrics.loss_limit_breached = False
        await db.commit()
    
    print("✓ Metrics reset")


async def test_trading_hours():
    """Test trading hours check"""
    print("\n" + "="*60)
    print("TEST 7: Trading Hours")
    print("="*60)
    
    result = await risk_manager.check_trading_hours(db=None)
    print(f"✓ Trading hours check: {result.passed}")
    print(f"  Reason: {result.reason}")
    if not result.passed:
        print(f"  Breach Type: {result.breach_type}")
        print(f"  Details: {result.details}")


async def test_pre_trade_check():
    """Test comprehensive pre-trade check"""
    print("\n" + "="*60)
    print("TEST 8: Pre-Trade Check (Comprehensive)")
    print("="*60)
    
    user_id = 1
    
    # Test valid order
    all_passed, results = await risk_manager.pre_trade_check(
        user_id=user_id,
        symbol="RELIANCE",
        quantity=10,
        price=2500.0,
        db=None
    )
    
    print(f"✓ Pre-trade check result: {all_passed}")
    print(f"  Total checks: {len(results)}")
    
    for i, result in enumerate(results, 1):
        status = "✓ PASS" if result.passed else "✗ FAIL"
        print(f"  {i}. {status}: {result.reason}")
    
    # Test invalid order (exceeds position value)
    print("\n  Testing with invalid order (exceeds limits)...")
    all_passed, results = await risk_manager.pre_trade_check(
        user_id=user_id,
        symbol="RELIANCE",
        quantity=100,
        price=2500.0,  # ₹2,50,000
        db=None
    )
    
    print(f"✓ Pre-trade check result: {all_passed}")
    failed_checks = [r for r in results if not r.passed]
    print(f"  Failed checks: {len(failed_checks)}")
    
    for result in failed_checks:
        print(f"  ✗ {result.breach_type}: {result.reason}")


async def test_daily_metrics():
    """Test daily metrics tracking"""
    print("\n" + "="*60)
    print("TEST 9: Daily Metrics Tracking")
    print("="*60)
    
    user_id = 1
    
    async with AsyncSessionLocal() as db:
        metrics = await risk_manager.get_daily_metrics(user_id=user_id, db=db)
        
        # Update metrics
        metrics.orders_placed += 5
        metrics.orders_executed += 4
        metrics.orders_rejected += 1
        metrics.realized_pnl = 1500.0
        metrics.unrealized_pnl = -200.0
        metrics.total_pnl = 1300.0
        
        await db.commit()
        await db.refresh(metrics)
        
        print(f"✓ Daily metrics updated for user {user_id}")
        print(f"  Orders Placed: {metrics.orders_placed}")
        print(f"  Orders Executed: {metrics.orders_executed}")
        print(f"  Orders Rejected: {metrics.orders_rejected}")
        print(f"  Realized P&L: ₹{metrics.realized_pnl:,.2f}")
        print(f"  Unrealized P&L: ₹{metrics.unrealized_pnl:,.2f}")
        print(f"  Total P&L: ₹{metrics.total_pnl:,.2f}")
        print(f"  Risk Breaches: {metrics.risk_breaches}")


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("RISK MANAGEMENT TEST SUITE")
    print("="*60)
    
    try:
        await test_risk_config()
        await test_kill_switch()
        await test_position_limits()
        await test_order_limits()
        await test_ops_limit()
        await test_loss_limits()
        await test_trading_hours()
        await test_pre_trade_check()
        await test_daily_metrics()
        
        print("\n" + "="*60)
        print("✓ ALL TESTS COMPLETED SUCCESSFULLY")
        print("="*60)
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

