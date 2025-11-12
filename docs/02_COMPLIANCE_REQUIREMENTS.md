# 02 - SEBI Compliance Requirements

[← Back to Master PRD](MASTER_PRD.md)

---

## 📜 Regulatory Framework Overview

### Primary Regulations

| Circular | Date | Title | Status |
|----------|------|-------|--------|
| **SEBI/HO/MIRSD/MIRSD-PoD/P/CIR/2025/0000013** | Feb 4, 2025 | Safer participation of retail investors in Algorithmic trading | **🔴 MANDATORY** - Effective Aug 1, 2025 |
| **SEBI/HO/CDMRD/CDMRD_DRM/P/CIR/2022/30** | Mar 17, 2022 | Revision in Orders Per Second limit | **Active** - Commodities |
| **CIR/MRD/DP/09/2012** | Mar 30, 2012 | Broad guidelines on Algorithmic Trading | **Active** - Base framework |

---

## 🔴 Critical Compliance Requirements (P0)

### 1. Authentication & Authorization

#### 🔴 P0: OAuth-Based Authentication
**SEBI Requirement:** "Have OAuth (Open Authentication) based authentication only and all other authentication mechanisms shall be discontinued"

**Implementation Requirements:**
```python
# OAuth Flow
1. User initiates login via broker portal
2. User authorizes our app
3. Broker returns OAuth token
4. Store token securely (encrypted at rest)
5. Use token for all API calls
6. Refresh token before expiry
```

**Acceptance Criteria:**
- [ ] Zero storage of user passwords
- [ ] OAuth 2.0 compliant flow
- [ ] Token encryption at rest (AES-256)
- [ ] Token refresh automation
- [ ] Fallback for token expiry handling

**Zerodha Implementation:**
```python
# Zerodha OAuth Flow
GET https://kite.zerodha.com/connect/login?v=3&api_key={api_key}
# After user login, redirect to:
redirect_url?request_token={request_token}&action=login&status=success
# Exchange request_token for access_token
POST /session/token
  api_key, request_token, checksum (SHA256 of api_key+request_token+api_secret)
```

**Groww Implementation:**
```python
# Option 1: Access Token (Daily expiry at 6 AM)
- Generate from Groww portal
- No expiry management needed daily

# Option 2: TOTP Flow (Recommended)
- API Key + Secret
- TOTP generation via pyotp
- No expiry
```

#### 🔴 P0: Two-Factor Authentication
**SEBI Requirement:** "Authenticate access to API through two factor authentication"

**Implementation:**
- **Factor 1:** OAuth token (what you have)
- **Factor 2:** TOTP (Time-based OTP) (what you know/generate)

**Technical Implementation:**
```python
# For Zerodha
- User must enable TOTP in Zerodha settings
- Our system validates OAuth token + active session

# For Groww  
import pyotp
totp = pyotp.TOTP('user_secret_key')
otp_code = totp.now()
# Send OTP with each critical API call
```

**Acceptance Criteria:**
- [ ] TOTP setup workflow for new users
- [ ] OTP validation on every critical operation
- [ ] Grace period handling for OTP expiry
- [ ] Backup codes for account recovery

#### 🔴 P0: Static IP Whitelisting
**SEBI Requirement:** "Allow access only through a unique vendor client specific API key and static IP whitelisted by the broker"

**Implementation:**
```bash
# GCP Setup
1. Reserve static external IP in GCP Mumbai region
2. Attach to VM instance
3. Register with Zerodha/Groww
4. All API calls originate from this IP only

# Infrastructure
resource "google_compute_address" "static_ip" {
  name   = "algo-trading-static-ip"
  region = "asia-south1"
}
```

**Acceptance Criteria:**
- [ ] Static IP reserved and documented
- [ ] IP whitelisted with both brokers
- [ ] No API calls from any other IP
- [ ] Monitoring for IP change attempts
- [ ] Automated alerts for whitelist failures

---

### 2. Order Tagging & Identification

#### 🔴 P0: Unique Algo Identifier
**SEBI Requirement:** "All algo orders originating/flowing through API shall be tagged with a unique identifier provided by Stock Exchange"

**Implementation:**
```python
class Order:
    exchange_algo_id: str  # Provided by Exchange after registration
    internal_strategy_id: str  # Our internal strategy tracking
    order_id: str  # Broker's order ID
    timestamp: datetime
    
# Every order payload must include
order_params = {
    "tradingsymbol": "INFY",
    "quantity": 10,
    "tag": f"ALGO_{exchange_algo_id}_{internal_strategy_id}"  # Mandatory
}
```

**Registration Process:**
1. **Strategy Development** → Create strategy logic
2. **Strategy Testing** → Backtest and paper trade
3. **Exchange Registration** → Submit strategy to Exchange via broker
4. **Receive Algo ID** → Exchange provides unique identifier
5. **Tag All Orders** → Include ID in every order

**Acceptance Criteria:**
- [ ] Algo ID registration workflow
- [ ] Algo ID storage in database
- [ ] Automatic tagging of all algo orders
- [ ] 100% tagging accuracy validation
- [ ] Reject orders without valid algo ID

#### 🔴 P0: Order Per Second Tracking
**SEBI Requirement:** "Algos developed by tech-savvy retail investors themselves shall be registered with the Exchange only if they cross the specified order per second threshold"

**Current Limits (as of Mar 2022):**
- **Commodity Derivatives:** Max 120 OPS
- **Measured over:** Rolling 5-second window (5X orders)
- **Our Target:** 10 OPS (12x safety margin)

**Implementation:**
```python
from collections import deque
from datetime import datetime, timedelta

class OPSTracker:
    def __init__(self, window_seconds=5, max_ops=10):
        self.window = window_seconds
        self.max_ops = max_ops
        self.order_timestamps = deque()
    
    def track_order(self):
        now = datetime.now()
        cutoff = now - timedelta(seconds=self.window)
        
        # Remove old orders outside window
        while self.order_timestamps and self.order_timestamps[0] < cutoff:
            self.order_timestamps.popleft()
        
        # Check if within limit
        if len(self.order_timestamps) >= (self.max_ops * self.window):
            raise OPSLimitExceeded(f"Exceeded {self.max_ops} OPS limit")
        
        self.order_timestamps.append(now)
        
    def get_current_ops(self):
        now = datetime.now()
        cutoff = now - timedelta(seconds=self.window)
        recent = [ts for ts in self.order_timestamps if ts > cutoff]
        return len(recent) / self.window
```

**Acceptance Criteria:**
- [ ] Real-time OPS calculation
- [ ] OPS limit enforcement (10 OPS)
- [ ] Warning at 70% threshold (7 OPS)
- [ ] Dashboard display of current OPS
- [ ] Historical OPS logging
- [ ] Alert when approaching limits

---

### 3. Audit Trail & Logging

#### 🔴 P0: Complete Audit Trail
**SEBI Requirement:** "All algo orders shall be tagged with a unique identifier provided by the Exchange in order to establish audit trail"

**Required Logging:**
```python
class AuditLog:
    # Order Lifecycle
    order_id: str
    algo_id: str
    strategy_id: str
    
    # Timing
    signal_generated_at: datetime  # When strategy triggered
    order_placed_at: datetime      # When sent to broker
    order_ack_at: datetime          # Broker acknowledgment
    order_filled_at: datetime       # Execution completion
    
    # Details
    order_type: str  # BUY/SELL
    quantity: int
    price: float
    trigger_price: Optional[float]
    
    # Context
    market_data_snapshot: dict  # OHLCV at signal time
    strategy_state: dict        # Strategy variables
    risk_checks: dict           # Risk validations passed
    
    # Result
    status: str  # PLACED, FILLED, CANCELLED, REJECTED
    rejection_reason: Optional[str]
    execution_price: Optional[float]
    
    # Compliance
    user_id: str
    ip_address: str
    api_key_used: str
```

**Storage Requirements:**
- **Retention:** 7 years (SEBI requirement)
- **Format:** Immutable, timestamped records
- **Access:** Read-only after creation
- **Export:** CSV/JSON format for audits

**Implementation:**
```sql
-- PostgreSQL with TimescaleDB
CREATE TABLE audit_orders (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL,
    order_id VARCHAR(50) NOT NULL,
    algo_id VARCHAR(50) NOT NULL,
    user_id VARCHAR(50) NOT NULL,
    event_type VARCHAR(20) NOT NULL,
    event_data JSONB NOT NULL,
    ip_address INET NOT NULL,
    CONSTRAINT immutable_record CHECK (false) -- Prevent updates
);

-- Convert to hypertable for time-series optimization
SELECT create_hypertable('audit_orders', 'created_at');

-- Indexes
CREATE INDEX idx_order_id ON audit_orders(order_id);
CREATE INDEX idx_algo_id ON audit_orders(algo_id);
CREATE INDEX idx_user_id ON audit_orders(user_id);
CREATE INDEX idx_created_at ON audit_orders(created_at DESC);
```

**Acceptance Criteria:**
- [ ] Every order logged before execution
- [ ] Immutable logs (no updates/deletes)
- [ ] Sub-second logging latency
- [ ] 100% logging success rate
- [ ] Export functionality for audits
- [ ] 7-year retention policy

---

### 4. Broker Responsibilities

#### 🔴 P0: Broker Compliance
**SEBI Requirement:** "Brokers shall be solely responsible for handling investor grievances related to algo trading and the monitoring of APIs for prohibited activities"

**Our Responsibilities as User:**
- Register algos through broker
- Maintain proper documentation
- Report issues to broker
- Cooperate with audits

**Broker API Compliance Check:**
```python
class BrokerComplianceCheck:
    def verify_zerodha_compliance():
        # Check OAuth is enabled
        # Check 2FA is active
        # Check IP is whitelisted
        # Check API key is active
        # Check algo IDs are registered
        
    def verify_groww_compliance():
        # Similar checks for Groww
```

---

## 🟡 Registration Requirements (P1)

### Algo Registration Process

#### When Registration Required
**SEBI:** "Only if they cross the specified order per second threshold"

**Current Understanding:**
- Threshold to be defined by **Broker's Industry Standards Forum**
- Deadline: **April 1, 2025**
- Until then: Monitor OPS, prepare for registration

#### Registration Workflow

```
1. Strategy Development
   ↓
2. Backtesting (1000+ combinations)
   ↓
3. Paper Trading (30+ days)
   ↓
4. [IF OPS > Threshold] → Exchange Registration
   ├── Submit strategy logic (White box)
   ├── Provide backtesting results
   ├── Risk management details
   └── Receive Algo ID
   ↓
5. Live Trading with Algo ID tagging
```

#### Registration Data Requirements

**Strategy Documentation:**
```markdown
# Strategy Registration Document

## 1. Strategy Identification
- Name: [e.g., "VWAP Momentum Crossover"]
- Type: White Box (Logic Disclosed)
- Category: Execution Algo
- Developer: [Personal/Family Use]

## 2. Strategy Logic
- Entry Conditions: [Detailed logic]
- Exit Conditions: [Detailed logic]
- Technical Indicators Used: [List all]
- Timeframe: [1min, 5min, etc.]

## 3. Risk Parameters
- Max Position Size: [INR/Units]
- Stop Loss: [% or absolute]
- Take Profit: [% or absolute]
- Max Daily Loss: [INR]

## 4. Backtesting Results
- Period: [Date range]
- No. of Trades: [Count]
- Win Rate: [%]
- Sharpe Ratio: [Value]
- Max Drawdown: [%]

## 5. Expected OPS
- Average: [X OPS]
- Peak: [Y OPS]
- Measurement Period: [5 seconds rolling]

## 6. Compliance Declaration
- Confirm: White Box Algo
- Confirm: Personal/Family Use Only
- Confirm: Risk Controls Implemented
```

**Acceptance Criteria:**
- [ ] Template for strategy documentation
- [ ] Automated generation from strategy code
- [ ] Validation before submission
- [ ] Tracking of registration status
- [ ] Notification on approval/rejection

---

## 🟡 Algo Categorization (P1)

### White Box vs Black Box

#### Our Classification: White Box (Execution Algos)
**SEBI Definition:** "Algos where logic is disclosed and replicable"

**Why We're White Box:**
- Strategy logic in Python files (human-readable)
- All indicators and conditions documented
- Backtesting methodology transparent
- Personal use (not selling strategies)

**Requirements for White Box:**
- ✅ Disclose complete strategy logic
- ✅ Provide indicator formulas
- ✅ Share backtesting methodology
- ❌ NO Research Analyst registration needed

**If We Were Black Box:**
- ❌ Would need Research Analyst registration
- ❌ Would need detailed research reports
- ❌ Higher regulatory burden
- ❌ More complex compliance

---

## 🟢 Data Privacy & Confidentiality (P2)

### Strategy Confidentiality

**SEBI Consideration:** "Measures to enhance the confidentiality of retail algo strategies including confidentiality clauses, non-disclosure agreements, encrypted submissions etc."

**Implementation:**
```python
# Encrypted Strategy Storage
from cryptography.fernet import Fernet

class StrategyVault:
    def encrypt_strategy(strategy_code: str, key: bytes):
        f = Fernet(key)
        encrypted = f.encrypt(strategy_code.encode())
        return encrypted
    
    def decrypt_strategy(encrypted_code: bytes, key: bytes):
        f = Fernet(key)
        decrypted = f.decrypt(encrypted_code)
        return decrypted.decode()
```

**Protection Measures:**
- [ ] Encrypted strategy files at rest
- [ ] No strategy code in logs
- [ ] Access control on strategy directory
- [ ] Git repository is private
- [ ] No strategy sharing with third parties

---

## 📊 Compliance Monitoring Dashboard

### Real-time Compliance Metrics

```python
class ComplianceMonitor:
    def get_compliance_score():
        return {
            "oauth_active": check_oauth_status(),
            "2fa_enabled": check_2fa_status(),
            "ip_whitelisted": check_ip_whitelist(),
            "algo_registered": check_algo_registration(),
            "ops_within_limit": check_ops_compliance(),
            "audit_logs_complete": check_audit_completeness(),
            "token_valid": check_token_validity(),
            "overall_score": calculate_overall_score()
        }
```

**Dashboard Display:**
```
╔══════════════════════════════════════════╗
║   SEBI COMPLIANCE DASHBOARD              ║
╠══════════════════════════════════════════╣
║ ✅ OAuth Authentication     [ACTIVE]     ║
║ ✅ Two-Factor Auth          [ENABLED]    ║
║ ✅ IP Whitelisting          [VERIFIED]   ║
║ ⏳ Algo Registration        [PENDING]    ║
║ ✅ OPS Monitoring           [2.3 / 10]   ║
║ ✅ Audit Logging            [100%]       ║
║ ✅ Token Status             [VALID]      ║
╠══════════════════════════════════════════╣
║ Overall Compliance: 95%                  ║
║ Last Audit: 2025-11-11 10:30 IST        ║
║ Next Review: 2025-12-01                  ║
╚══════════════════════════════════════════╝
```

---

## ⚠️ Non-Compliance Risks

### Penalties & Consequences

| Violation | Penalty | Impact |
|-----------|---------|--------|
| **Untagged Orders** | Trading suspension | Cannot trade |
| **IP Violation** | API access revoked | Platform unusable |
| **OPS Breach** | Economic disincentives | Additional charges |
| **Missing Audit Trail** | Legal action | Personal liability |
| **Registration Failure** | Order rejection | Strategy blocked |

### Mitigation Strategy

```python
class ComplianceGuard:
    def pre_order_check(order):
        validations = [
            validate_oauth_active(),
            validate_algo_id_present(order),
            validate_ops_limit(),
            validate_ip_whitelist(),
            validate_risk_limits(order)
        ]
        
        if not all(validations):
            raise ComplianceViolation("Order blocked: Compliance check failed")
        
        # Log check passed
        log_audit("COMPLIANCE_CHECK_PASSED", order)
        return True
```

---

## 📅 Compliance Timeline

### Key Dates

| Date | Milestone | Action Required |
|------|-----------|-----------------|
| **Nov 2025** | PRD Complete | Document requirements |
| **Dec 2025** | Foundation Built | Implement OAuth, 2FA, Audit |
| **Jan 2026** | Testing Phase | Validate compliance in staging |
| **Apr 1, 2025** | ISF Threshold Defined | Review if registration needed |
| **Jul 2026** | Pre-launch Audit | Final compliance check |
| **Aug 1, 2025** | SEBI Deadline | Full compliance mandatory |

### Ongoing Compliance

**Daily:**
- [ ] OAuth token validity check
- [ ] OPS monitoring
- [ ] Audit log verification

**Weekly:**
- [ ] Compliance score review
- [ ] Risk limit validation
- [ ] System health check

**Monthly:**
- [ ] Full compliance audit
- [ ] Documentation update
- [ ] Regulatory update check

**Quarterly:**
- [ ] Strategy re-registration (if modified)
- [ ] Compliance report generation
- [ ] External audit preparation

---

## 📚 Regulatory Resources

### Official Documents
1. [SEBI Feb 2025 Circular - Retail Algo Trading](https://www.sebi.gov.in/legal/circulars/feb-2025/)
2. [SEBI Mar 2022 Circular - OPS Limits](https://www.sebi.gov.in/legal/circulars/mar-2022/)
3. [NSE Algo Trading Guidelines](https://www.nseindia.com/regulations/algo-trading)
4. [BSE Algo Trading Framework](https://www.bseindia.com/static/about/regulatory.aspx)

### Industry Forums
- Broker's Industry Standards Forum (ISF)
- SEBI Technical Advisory Committee
- Zerodha Algo Trading Community Forum

### Legal Consultation
**When to Consult:**
- Algo registration interpretation
- Compliance ambiguity
- Penalty disputes
- Strategy classification questions

---

## ✅ Compliance Checklist

### Pre-Launch (P0)
- [ ] OAuth implementation complete
- [ ] 2FA enabled and tested
- [ ] Static IP obtained and whitelisted
- [ ] Audit logging operational
- [ ] OPS tracking implemented
- [ ] Compliance dashboard built
- [ ] Pre-order validation active

### Post-Launch (P1)
- [ ] Algo registration completed (if needed)
- [ ] Exchange algo IDs obtained
- [ ] All orders tagged correctly
- [ ] Audit trail validated
- [ ] Compliance monitoring active

### Ongoing (P2)
- [ ] Weekly compliance reviews
- [ ] Monthly audit reports
- [ ] Quarterly strategy reviews
- [ ] Annual regulatory updates

---

**Next:** Review [Technical Architecture →](03_TECHNICAL_ARCHITECTURE.md)

---

*Last Updated: November 11, 2025*
*Compliance Status: Design Phase*
*Next Review: December 1, 2025*
