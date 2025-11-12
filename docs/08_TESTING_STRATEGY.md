# 08 - Testing Strategy

[← Back to Master PRD](MASTER_PRD.md)

---

## 🧪 Overview

This document outlines the comprehensive testing strategy for the algorithmic trading platform, ensuring reliability, security, compliance, and performance before live deployment.

---

## 🎯 Testing Objectives

### Primary Goals
1. **Reliability:** Zero unintended trades in production
2. **Compliance:** 100% SEBI guideline adherence
3. **Performance:** Meet all latency and throughput targets
4. **Security:** Zero unauthorized access or data breaches
5. **Accuracy:** Financial calculations 100% accurate

### Testing Pyramid

```
                    ╱╲
                   ╱  ╲
                  ╱ E2E╲              10% - 5 critical flows
                 ╱──────╲
                ╱ Integ. ╲            30% - API & service integration
               ╱──────────╲
              ╱    Unit    ╲          60% - Functions & business logic
             ╱──────────────╲
            ────────────────────
```

---

## 🧩 Unit Testing

### Scope
Individual functions, classes, and modules in isolation

### Framework & Tools
- **Backend:** pytest, pytest-asyncio, pytest-cov
- **Frontend:** Jest, React Testing Library
- **Coverage Target:** >80% for critical paths, >60% overall

### Priority Areas

#### P0 (Critical)
1. **Strategy Logic**
   ```python
   # tests/strategies/test_base_strategy.py
   
   def test_strategy_initialization():
       """Test strategy initializes with correct config"""
       config = {
           "instruments": ["NSE:INFY"],
           "timeframe": "5min",
           "stop_loss_pct": 2.0
       }
       strategy = TestStrategy(config)
       assert strategy.config == config
       assert strategy.name == "TestStrategy"
   
   def test_signal_generation():
       """Test strategy generates correct signals"""
       strategy = TestStrategy(config)
       data = pd.DataFrame({
           'close': [100, 102, 105, 103, 108]
       })
       
       signals = strategy.on_data(data)
       
       assert len(signals) > 0
       assert signals[0]['signal'] in [Signal.BUY, Signal.SELL, Signal.HOLD]
       assert 'reason' in signals[0]
   
   def test_position_sizing():
       """Test position size calculation"""
       strategy = TestStrategy(config)
       position_size = strategy.calculate_position_size(
           capital=100000,
           price=1000,
           risk_per_trade=1000
       )
       
       assert position_size > 0
       assert position_size * 1000 <= 100000  # Max capital
   ```

2. **Risk Management**
   ```python
   # tests/services/test_risk_manager.py
   
   def test_position_limit_check():
       """Test position limit validation"""
       risk_manager = RiskManager(config)
       
       # Should allow within limit
       order = {"symbol": "NSE:INFY", "quantity": 10}
       assert risk_manager.validate_position_limit(order) == True
       
       # Should reject over limit
       order = {"symbol": "NSE:INFY", "quantity": 10000}
       assert risk_manager.validate_position_limit(order) == False
   
   def test_daily_loss_limit():
       """Test daily loss limit enforcement"""
       risk_manager = RiskManager(config)
       risk_manager.daily_loss = -9500  # Near limit
       
       order = {"expected_loss": 600}
       assert risk_manager.check_daily_loss(order) == False
   
   def test_stop_loss_trigger():
       """Test stop loss triggers correctly"""
       risk_manager = RiskManager(config)
       
       position = {
           "symbol": "NSE:INFY",
           "entry_price": 1000,
           "quantity": 10,
           "stop_loss": 980
       }
       
       current_price = 975
       assert risk_manager.should_trigger_stop_loss(position, current_price) == True
       
       current_price = 990
       assert risk_manager.should_trigger_stop_loss(position, current_price) == False
   ```

3. **Order Management**
   ```python
   # tests/services/test_order_manager.py
   
   def test_order_validation():
       """Test order validates correctly"""
       order_manager = OrderManager()
       
       valid_order = {
           "symbol": "NSE:INFY",
           "quantity": 10,
           "order_type": "LIMIT",
           "price": 1000
       }
       assert order_manager.validate_order(valid_order) == True
       
       invalid_order = {
           "symbol": "NSE:INFY",
           "quantity": -10,  # Invalid
           "order_type": "LIMIT",
           "price": 1000
       }
       assert order_manager.validate_order(invalid_order) == False
   
   def test_order_tagging():
       """Test SEBI algo identifier tagging"""
       order_manager = OrderManager()
       
       order = {"symbol": "NSE:INFY", "quantity": 10}
       tagged_order = order_manager.add_algo_tag(order, strategy_id="STR_001")
       
       assert 'tag' in tagged_order
       assert tagged_order['tag'].startswith('algo_')
   ```

4. **Financial Calculations**
   ```python
   # tests/utils/test_financial_calculations.py
   
   def test_pnl_calculation():
       """Test P&L calculation accuracy"""
       pnl = calculate_pnl(
           entry_price=1000,
           exit_price=1050,
           quantity=10,
           transaction_type="BUY"
       )
       assert pnl == 500  # (1050-1000) * 10
       
       pnl = calculate_pnl(
           entry_price=1000,
           exit_price=950,
           quantity=10,
           transaction_type="SELL"
       )
       assert pnl == 500  # (1000-950) * 10
   
   def test_returns_calculation():
       """Test returns calculation"""
       returns = calculate_returns(
           initial_capital=100000,
           final_capital=110000
       )
       assert returns == 10.0  # 10% return
   
   def test_sharpe_ratio():
       """Test Sharpe ratio calculation"""
       returns = [0.01, 0.02, -0.01, 0.015, 0.03]
       sharpe = calculate_sharpe_ratio(returns, risk_free_rate=0.05)
       
       assert isinstance(sharpe, float)
       assert sharpe > 0
   ```

#### P1 (High)
- Backtesting engine logic
- Historical data processing
- WebSocket message handling
- Authentication & authorization
- Data validation

#### P2 (Medium)
- UI components
- API response formatting
- Logging utilities
- Cache management

### Test Naming Convention
```python
def test_<function_name>_<scenario>_<expected_result>():
    """
    Test description
    """
    # Arrange
    # Act
    # Assert
```

### Running Unit Tests
```bash
# Backend
cd backend
pytest tests/unit/ -v --cov=app --cov-report=html

# Frontend
cd frontend
npm test -- --coverage
```

---

## 🔗 Integration Testing

### Scope
Testing interactions between components, services, and external APIs

### Priority Areas

#### P0 (Critical)

1. **Broker API Integration**
   ```python
   # tests/integration/test_broker_integration.py
   
   @pytest.mark.integration
   async def test_zerodha_oauth_flow():
       """Test complete Zerodha OAuth flow"""
       broker = ZerodhaBroker(config)
       
       # Mock request token
       broker.request_token = "test_token"
       
       # Should authenticate successfully
       success = await broker.authenticate()
       assert success == True
       assert broker.access_token is not None
   
   @pytest.mark.integration
   async def test_order_placement_zerodha():
       """Test order placement with Zerodha"""
       broker = ZerodhaBroker(config)
       await broker.authenticate()
       
       order = {
           "tradingsymbol": "INFY",
           "exchange": "NSE",
           "transaction_type": "BUY",
           "quantity": 1,
           "order_type": "MARKET",
           "product": "MIS"
       }
       
       result = await broker.place_order(order)
       
       assert result['status'] == 'success'
       assert 'order_id' in result
       
       # Clean up - cancel order
       await broker.cancel_order(result['order_id'])
   
   @pytest.mark.integration
   async def test_historical_data_fetch():
       """Test historical data fetching"""
       broker = ZerodhaBroker(config)
       await broker.authenticate()
       
       data = await broker.get_historical_data(
           instrument_token="408065",  # INFY
           from_date="2025-01-01",
           to_date="2025-01-31",
           interval="day"
       )
       
       assert not data.empty
       assert 'open' in data.columns
       assert 'high' in data.columns
       assert 'low' in data.columns
       assert 'close' in data.columns
       assert 'volume' in data.columns
   ```

2. **Database Operations**
   ```python
   # tests/integration/test_database.py
   
   @pytest.mark.integration
   async def test_user_crud():
       """Test user CRUD operations"""
       # Create
       user = await create_user({
           "email": "test@example.com",
           "name": "Test User",
           "role": "trader"
       })
       assert user.id is not None
       
       # Read
       fetched_user = await get_user(user.id)
       assert fetched_user.email == "test@example.com"
       
       # Update
       updated_user = await update_user(user.id, {"name": "Updated Name"})
       assert updated_user.name == "Updated Name"
       
       # Delete
       deleted = await delete_user(user.id)
       assert deleted == True
   
   @pytest.mark.integration
   async def test_order_persistence():
       """Test order storage and retrieval"""
       order = {
           "user_id": 1,
           "symbol": "NSE:INFY",
           "quantity": 10,
           "order_type": "LIMIT",
           "price": 1450.50
       }
       
       # Store order
       stored_order = await store_order(order)
       assert stored_order.id is not None
       
       # Retrieve order
       fetched_order = await get_order(stored_order.id)
       assert fetched_order.symbol == "NSE:INFY"
       assert float(fetched_order.price) == 1450.50
   
   @pytest.mark.integration
   async def test_audit_trail_logging():
       """Test audit trail is logged correctly"""
       event = {
           "user_id": 1,
           "action": "ORDER_PLACED",
           "details": {"order_id": "ORD123"}
       }
       
       await log_audit_event(event)
       
       # Verify logged
       logs = await get_audit_logs(user_id=1, limit=1)
       assert len(logs) > 0
       assert logs[0].action == "ORDER_PLACED"
   ```

3. **Rate Limiting**
   ```python
   # tests/integration/test_rate_limiting.py
   
   @pytest.mark.integration
   async def test_rate_limiter():
       """Test rate limiter enforces limits"""
       rate_limiter = RateLimiter()
       
       # Should allow up to limit
       for i in range(10):
           await rate_limiter.acquire('zerodha', 'global')
       
       # Should block when limit exceeded
       start_time = time.time()
       await rate_limiter.acquire('zerodha', 'global')
       elapsed = time.time() - start_time
       
       assert elapsed > 1.0  # Should wait ~1 second
   
   @pytest.mark.integration
   async def test_rate_limit_backoff():
       """Test rate limit backoff strategy"""
       broker = ZerodhaBroker(config)
       
       # Trigger rate limit
       with pytest.raises(RateLimitError):
           for i in range(100):
               await broker.get_quote(["NSE:INFY"])
       
       # Should implement exponential backoff
       # Verify retries with backoff
   ```

4. **WebSocket Streaming**
   ```python
   # tests/integration/test_websocket.py
   
   @pytest.mark.integration
   async def test_websocket_connection():
       """Test WebSocket connection and reconnection"""
       ws = ZerodhaWebSocket(api_key, access_token)
       
       # Should connect successfully
       ws.start()
       await asyncio.sleep(2)
       assert ws.is_connected() == True
       
       # Should handle disconnection
       ws.kws.close()
       await asyncio.sleep(2)
       
       # Should reconnect
       assert ws.is_connected() == True
   
   @pytest.mark.integration
   async def test_websocket_data_flow():
       """Test WebSocket receives and processes ticks"""
       ws = ZerodhaWebSocket(api_key, access_token)
       
       ticks_received = []
       
       def on_tick(ticks):
           ticks_received.extend(ticks)
       
       ws.on_ticks = on_tick
       ws.start()
       ws.subscribe([408065])  # INFY
       
       await asyncio.sleep(10)
       
       assert len(ticks_received) > 0
       assert 'last_price' in ticks_received[0]
   ```

#### P1 (High)
- Strategy execution pipeline
- Paper trading simulation
- Backtest data flow
- Cache invalidation
- API authentication flow

### Running Integration Tests
```bash
# Requires test database and test broker credentials
cd backend
pytest tests/integration/ -v -m integration
```

---

## 🌐 End-to-End Testing

### Scope
Complete user workflows from UI to database

### Framework & Tools
- **Playwright** for browser automation
- **Pytest** for test orchestration

### Critical User Flows

#### P0 (Critical)

1. **User Registration & Login**
   ```python
   # tests/e2e/test_auth_flow.py
   
   async def test_complete_auth_flow(page):
       """Test user registration and login flow"""
       
       # Navigate to registration
       await page.goto("https://algo-trading.example.com/register")
       
       # Fill registration form
       await page.fill("#email", "test@example.com")
       await page.fill("#password", "TestPassword123!")
       await page.fill("#name", "Test User")
       await page.click("#register-button")
       
       # Should redirect to login
       await page.wait_for_url("**/login")
       
       # Login
       await page.fill("#email", "test@example.com")
       await page.fill("#password", "TestPassword123!")
       await page.click("#login-button")
       
       # Should redirect to dashboard
       await page.wait_for_url("**/dashboard")
       
       # Verify logged in
       assert await page.locator("#user-menu").is_visible()
   ```

2. **Broker Connection**
   ```python
   # tests/e2e/test_broker_connection.py
   
   async def test_zerodha_connection_flow(page):
       """Test Zerodha broker connection"""
       
       # Login first
       await login_user(page)
       
       # Navigate to broker settings
       await page.goto("/settings/brokers")
       
       # Click connect Zerodha
       await page.click("#connect-zerodha")
       
       # Should redirect to Zerodha OAuth
       await page.wait_for_url("**/kite.zerodha.com/**")
       
       # Login to Zerodha (mock)
       await page.fill("#user_id", "TEST001")
       await page.fill("#password", "test_pass")
       await page.click("#login")
       
       # Authorize
       await page.click("#authorize")
       
       # Should redirect back to app
       await page.wait_for_url("**/settings/brokers")
       
       # Verify connected
       assert await page.locator("#zerodha-status").text_content() == "Connected"
   ```

3. **Strategy Upload & Backtest**
   ```python
   # tests/e2e/test_strategy_backtest.py
   
   async def test_strategy_upload_and_backtest(page):
       """Test uploading strategy and running backtest"""
       
       await login_user(page)
       
       # Navigate to strategies
       await page.goto("/strategies")
       
       # Click upload strategy
       await page.click("#upload-strategy")
       
       # Upload Python file
       await page.set_input_files(
           "#strategy-file",
           "tests/fixtures/sample_strategy.py"
       )
       
       # Fill strategy details
       await page.fill("#strategy-name", "Test SMA Crossover")
       await page.click("#save-strategy")
       
       # Should show in list
       await page.wait_for_selector(":text('Test SMA Crossover')")
       
       # Click backtest
       await page.click("#backtest-button")
       
       # Fill backtest config
       await page.fill("#start-date", "2024-01-01")
       await page.fill("#end-date", "2024-12-31")
       await page.fill("#capital", "100000")
       await page.click("#run-backtest")
       
       # Wait for results
       await page.wait_for_selector("#backtest-results")
       
       # Verify results displayed
       assert await page.locator("#total-return").is_visible()
       assert await page.locator("#sharpe-ratio").is_visible()
       assert await page.locator("#equity-curve").is_visible()
   ```

4. **Paper Trading Flow**
   ```python
   # tests/e2e/test_paper_trading.py
   
   async def test_start_paper_trading(page):
       """Test starting paper trading"""
       
       await login_user(page)
       
       # Navigate to paper trading
       await page.goto("/paper-trading")
       
       # Select strategy
       await page.select_option("#strategy-select", "Test SMA Crossover")
       
       # Set capital
       await page.fill("#initial-capital", "100000")
       
       # Start paper trading
       await page.click("#start-paper-trading")
       
       # Should show running status
       await page.wait_for_selector(":text('Running')")
       
       # Wait for first update
       await page.wait_for_timeout(5000)
       
       # Verify dashboard updates
       assert await page.locator("#current-pnl").is_visible()
       assert await page.locator("#positions-table").is_visible()
   ```

5. **Live Trading Flow**
   ```python
   # tests/e2e/test_live_trading.py
   
   async def test_place_live_order(page):
       """Test placing live order (CAREFUL - uses real API)"""
       
       await login_user(page)
       
       # Navigate to live trading
       await page.goto("/live-trading")
       
       # Manual order entry
       await page.click("#manual-order")
       
       # Fill order details
       await page.fill("#symbol", "INFY")
       await page.select_option("#exchange", "NSE")
       await page.select_option("#transaction-type", "BUY")
       await page.fill("#quantity", "1")
       await page.select_option("#order-type", "MARKET")
       
       # Confirm order
       await page.click("#place-order")
       
       # Verify confirmation dialog
       await page.wait_for_selector("#order-confirmation")
       
       # Confirm
       await page.click("#confirm-order")
       
       # Should show in order book
       await page.wait_for_selector(":text('Order placed successfully')")
       
       # Verify order in order book
       await page.goto("/orders")
       assert await page.locator(":text('INFY')").is_visible()
   ```

#### P1 (High)
- Risk limit configuration
- Historical data download
- Portfolio view
- Settings management

### Running E2E Tests
```bash
# Requires running application
cd tests
pytest e2e/ -v --headed  # Run with visible browser
pytest e2e/ -v            # Headless mode
```

---

## ⚡ Performance Testing

### Scope
Load testing, stress testing, and latency benchmarking

### Tools
- **Locust** for load testing
- **pytest-benchmark** for microbenchmarks

### Performance Targets

| Metric | Target | Measured |
|--------|--------|----------|
| API Response Time (p50) | <200ms | ___ |
| API Response Time (p95) | <500ms | ___ |
| API Response Time (p99) | <1000ms | ___ |
| Order Placement Latency | <500ms | ___ |
| WebSocket Latency | <100ms | ___ |
| Backtest Throughput | 1000+ combinations/hour | ___ |
| Database Query Time | <50ms | ___ |
| Strategy Evaluation | <100ms | ___ |

### Load Tests

#### 1. API Load Test
```python
# tests/performance/locustfile.py

from locust import HttpUser, task, between

class TradingPlatformUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Login before tests"""
        response = self.client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "test_password"
        })
        self.token = response.json()['access_token']
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    @task(3)
    def get_quotes(self):
        """Most frequent operation"""
        self.client.get(
            "/api/v1/data/quote?symbols=NSE:INFY,NSE:SBIN",
            headers=self.headers
        )
    
    @task(2)
    def get_positions(self):
        """Check positions"""
        self.client.get(
            "/api/v1/positions",
            headers=self.headers
        )
    
    @task(1)
    def get_orders(self):
        """Check orders"""
        self.client.get(
            "/api/v1/orders",
            headers=self.headers
        )
    
    @task(1)
    def place_order(self):
        """Place order (paper trading mode)"""
        self.client.post(
            "/api/v1/orders/place",
            json={
                "symbol": "NSE:INFY",
                "quantity": 1,
                "order_type": "MARKET",
                "transaction_type": "BUY",
                "product": "MIS"
            },
            headers=self.headers
        )
```

#### Running Load Tests
```bash
# Test with 100 concurrent users
locust -f tests/performance/locustfile.py --users 100 --spawn-rate 10

# Headless mode with report
locust -f tests/performance/locustfile.py --headless \
       --users 100 --spawn-rate 10 --run-time 5m \
       --html report.html
```

#### 2. Backtest Performance
```python
# tests/performance/test_backtest_performance.py

@pytest.mark.benchmark
def test_backtest_performance(benchmark):
    """Benchmark backtesting speed"""
    
    strategy = SampleStrategy(config)
    data = generate_sample_data(days=365)  # 1 year daily data
    engine = BacktestEngine(strategy, data)
    
    result = benchmark(engine.run)
    
    assert result['total_trades'] > 0
    # Should complete in <1 second for 365 days
    assert benchmark.stats['mean'] < 1.0
```

#### 3. Strategy Evaluation Performance
```python
# tests/performance/test_strategy_performance.py

@pytest.mark.benchmark
def test_strategy_evaluation_speed(benchmark):
    """Benchmark strategy signal generation"""
    
    strategy = SampleStrategy(config)
    data = generate_sample_data(days=30)
    
    result = benchmark(strategy.on_data, data)
    
    # Should generate signals in <100ms
    assert benchmark.stats['mean'] < 0.1
```

---

## 🔒 Security Testing

### Scope
Authentication, authorization, encryption, and vulnerability scanning

### Priority Areas

#### P0 (Critical)

1. **Authentication Testing**
   ```python
   # tests/security/test_authentication.py
   
   async def test_unauthorized_access():
       """Test unauthorized access is blocked"""
       response = await client.get("/api/v1/strategies")
       assert response.status_code == 401
   
   async def test_expired_token():
       """Test expired tokens are rejected"""
       expired_token = generate_expired_token()
       response = await client.get(
           "/api/v1/strategies",
           headers={"Authorization": f"Bearer {expired_token}"}
       )
       assert response.status_code == 401
   
   async def test_invalid_token():
       """Test invalid tokens are rejected"""
       response = await client.get(
           "/api/v1/strategies",
           headers={"Authorization": "Bearer invalid_token"}
       )
       assert response.status_code == 401
   ```

2. **Authorization Testing**
   ```python
   # tests/security/test_authorization.py
   
   async def test_trader_cannot_access_admin():
       """Test trader role cannot access admin endpoints"""
       trader_token = get_trader_token()
       
       response = await client.get(
           "/api/v1/admin/users",
           headers={"Authorization": f"Bearer {trader_token}"}
       )
       assert response.status_code == 403
   
   async def test_user_cannot_access_other_user_data():
       """Test users cannot access other users' data"""
       user1_token = get_user_token(user_id=1)
       
       response = await client.get(
           "/api/v1/users/2/strategies",
           headers={"Authorization": f"Bearer {user1_token}"}
       )
       assert response.status_code == 403
   ```

3. **Input Validation**
   ```python
   # tests/security/test_input_validation.py
   
   async def test_sql_injection_prevention():
       """Test SQL injection is prevented"""
       malicious_input = "'; DROP TABLE users; --"
       
       response = await client.get(
           f"/api/v1/strategies?name={malicious_input}",
           headers=auth_headers
       )
       # Should not error, should sanitize input
       assert response.status_code in [200, 400]
   
   async def test_xss_prevention():
       """Test XSS attacks are prevented"""
       xss_payload = "<script>alert('XSS')</script>"
       
       response = await client.post(
           "/api/v1/strategies",
           json={"name": xss_payload, "code": "..."},
           headers=auth_headers
       )
       # Should sanitize or reject
       assert response.status_code in [201, 400]
   ```

4. **Encryption Testing**
   ```python
   # tests/security/test_encryption.py
   
   async def test_password_hashing():
       """Test passwords are hashed correctly"""
       password = "MySecurePassword123!"
       
       hashed = hash_password(password)
       
       # Should not store plain text
       assert hashed != password
       # Should be verifiable
       assert verify_password(password, hashed) == True
   
   async def test_api_key_encryption():
       """Test API keys are encrypted at rest"""
       api_key = "test_api_key_123"
       
       # Store encrypted
       encrypted = encrypt_api_key(api_key)
       assert encrypted != api_key
       
       # Retrieve and decrypt
       decrypted = decrypt_api_key(encrypted)
       assert decrypted == api_key
   ```

#### P1 (High)
- Rate limiting bypass attempts
- Session hijacking
- CSRF protection
- API key exposure

### Security Tools
```bash
# Dependency vulnerability scan
pip-audit

# Static code analysis
bandit -r app/

# HTTPS/TLS verification
openssl s_client -connect algo-trading.example.com:443
```

---

## ✅ Compliance Testing

### Scope
SEBI guideline adherence verification

### Critical Compliance Tests

#### 1. OAuth Authentication
```python
# tests/compliance/test_sebi_auth.py

async def test_oauth_only_authentication():
    """Verify only OAuth authentication is used"""
    
    # Should not allow password-based login for broker
    response = await client.post("/api/v1/brokers/login", json={
        "username": "test",
        "password": "test123"
    })
    assert response.status_code == 405  # Method not allowed
    
    # Should only allow OAuth
    assert broker.auth_method == "OAuth"
```

#### 2. Two-Factor Authentication
```python
async def test_2fa_required_for_critical_operations():
    """Verify 2FA is required for critical operations"""
    
    # Place order without 2FA
    response = await client.post(
        "/api/v1/orders/place",
        json=order_data,
        headers=auth_headers
    )
    assert response.status_code == 403
    assert "2FA required" in response.json()['message']
    
    # Place order with 2FA
    response = await client.post(
        "/api/v1/orders/place",
        json=order_data,
        headers={**auth_headers, "X-2FA-Token": generate_totp()}
    )
    assert response.status_code == 200
```

#### 3. Algo Identifier Tagging
```python
async def test_algo_identifier_tagging():
    """Verify all orders have algo identifier"""
    
    # Place order
    response = await client.post(
        "/api/v1/orders/place",
        json=order_data,
        headers=auth_headers_with_2fa
    )
    
    order_id = response.json()['order_id']
    
    # Verify order has algo tag
    order = await get_order_from_db(order_id)
    assert order.algo_identifier is not None
    assert order.algo_identifier.startswith('algo_')
```

#### 4. Audit Trail
```python
async def test_audit_trail_completeness():
    """Verify all algo orders are logged in audit trail"""
    
    # Place order
    response = await client.post(
        "/api/v1/orders/place",
        json=order_data,
        headers=auth_headers_with_2fa
    )
    
    order_id = response.json()['order_id']
    
    # Verify audit log entry
    audit_logs = await get_audit_logs(
        action="ORDER_PLACED",
        order_id=order_id
    )
    
    assert len(audit_logs) > 0
    log = audit_logs[0]
    
    # Verify required fields
    assert log.user_id is not None
    assert log.order_id == order_id
    assert log.timestamp is not None
    assert log.details is not None
```

#### 5. Orders Per Second (OPS)
```python
async def test_ops_tracking():
    """Verify OPS is tracked correctly"""
    
    ops_tracker = OPSTracker()
    
    # Simulate orders
    for i in range(10):
        await ops_tracker.record_order(
            timestamp=datetime.now(),
            order_id=f"ORD_{i}"
        )
        await asyncio.sleep(0.1)
    
    # Check OPS in 5-second window
    current_ops = await ops_tracker.get_current_ops()
    
    assert current_ops <= 10
    assert current_ops > 0
    
    # Verify OPS doesn't exceed 120 (commodity limit)
    assert ops_tracker.max_ops_5sec <= 120
```

#### 6. Static IP Verification
```python
async def test_static_ip_whitelisting():
    """Verify API access only from whitelisted IP"""
    
    # Request from whitelisted IP
    response = await client.get(
        "/api/v1/strategies",
        headers=auth_headers,
        client_ip="34.93.123.456"  # Whitelisted
    )
    assert response.status_code == 200
    
    # Request from non-whitelisted IP
    response = await client.get(
        "/api/v1/strategies",
        headers=auth_headers,
        client_ip="1.2.3.4"  # Not whitelisted
    )
    assert response.status_code == 403
```

---

## 📊 Test Coverage

### Coverage Targets

| Component | Target | Current |
|-----------|--------|---------|
| **Critical Business Logic** | >90% | ___ |
| **Risk Management** | 100% | ___ |
| **Order Management** | >95% | ___ |
| **Strategy Engine** | >85% | ___ |
| **API Endpoints** | >80% | ___ |
| **Overall Backend** | >80% | ___ |
| **Overall Frontend** | >70% | ___ |

### Measuring Coverage
```bash
# Backend coverage
pytest --cov=app --cov-report=html tests/

# Frontend coverage
npm test -- --coverage

# View HTML report
open htmlcov/index.html  # Backend
open coverage/lcov-report/index.html  # Frontend
```

---

## 🚨 Continuous Testing

### CI/CD Pipeline

```yaml
# .github/workflows/test.yml

name: Test Suite

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run unit tests
        run: pytest tests/unit/ -v --cov=app
      
  integration-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
      redis:
        image: redis:7
    steps:
      - uses: actions/checkout@v3
      - name: Run integration tests
        run: pytest tests/integration/ -v -m integration
      
  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Start application
        run: docker-compose up -d
      - name: Run E2E tests
        run: pytest tests/e2e/ -v
      
  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run security scan
        run: |
          pip install bandit pip-audit
          bandit -r app/
          pip-audit
```

---

## 📝 Test Documentation

### Test Case Template

```markdown
### Test Case: [Test Name]

**ID:** TC-[Component]-[Number]
**Priority:** P0/P1/P2
**Type:** Unit/Integration/E2E/Performance/Security/Compliance

**Objective:**
Brief description of what is being tested

**Preconditions:**
- List of prerequisites
- Test data requirements
- System state requirements

**Test Steps:**
1. Step 1
2. Step 2
3. Step 3

**Expected Results:**
- Expected outcome 1
- Expected outcome 2

**Actual Results:**
[To be filled during execution]

**Status:** Pass/Fail/Blocked
**Executed By:** [Name]
**Date:** [Date]
```

---

## ✅ Pre-Production Checklist

### Before Live Trading Launch

- [ ] All P0 unit tests passing
- [ ] All P0 integration tests passing
- [ ] All P0 E2E tests passing
- [ ] Performance benchmarks met
- [ ] Security scan passed
- [ ] All SEBI compliance tests passing
- [ ] Load testing completed (100+ concurrent users)
- [ ] Disaster recovery tested
- [ ] Monitoring and alerts configured
- [ ] Documentation updated
- [ ] Code review completed
- [ ] Stakeholder sign-off obtained

---

## 📊 Test Reporting

### Daily Test Report Template

```markdown
## Daily Test Report - [Date]

### Summary
- Tests Run: X
- Tests Passed: X
- Tests Failed: X
- Test Coverage: X%

### Failed Tests
1. [Test Name] - [Reason] - [Assignee]
2. [Test Name] - [Reason] - [Assignee]

### Performance
- API Response Time (p95): Xms
- Backtest Throughput: X combinations/hour

### Blockers
- [Blocker 1]
- [Blocker 2]

### Next Steps
- [Action item 1]
- [Action item 2]
```

---

**Previous:** [Implementation Plan ←](07_IMPLEMENTATION_PLAN.md)

---

*Last Updated: November 11, 2025*
