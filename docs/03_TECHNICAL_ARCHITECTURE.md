# 03 - Technical Architecture

[← Back to Master PRD](MASTER_PRD.md)

---

## 🏗️ System Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interface Layer                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Web App    │  │  Admin Panel │  │ Strategy IDE │         │
│  │  (Next.js)   │  │  (React)     │  │   (Monaco)   │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │ HTTPS/WSS
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        API Gateway Layer                          │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │          FastAPI Application Server                       │   │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐          │   │
│  │  │  Auth API  │ │ Trade API  │ │ Strategy   │          │   │
│  │  │            │ │            │ │ Mgmt API   │          │   │
│  │  └────────────┘ └────────────┘ └────────────┘          │   │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐          │   │
│  │  │ Data API   │ │ Risk API   │ │ WebSocket  │          │   │
│  │  │            │ │            │ │ Server     │          │   │
│  │  └────────────┘ └────────────┘ └────────────┘          │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Business Logic Layer                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Strategy   │  │  Backtesting │  │     Risk     │         │
│  │    Engine    │  │    Engine    │  │  Management  │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Order      │  │  Portfolio   │  │   Audit      │         │
│  │ Management   │  │  Manager     │  │   Logger     │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Task Processing Layer                        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Celery Distributed Task Queue                │   │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐          │   │
│  │  │  Strategy  │ │ Backtest   │ │   Data     │          │   │
│  │  │  Worker    │ │  Worker    │ │   Worker   │          │   │
│  │  └────────────┘ └────────────┘ └────────────┘          │   │
│  │  ┌────────────┐ ┌────────────┐                          │   │
│  │  │   Order    │ │ Monitoring │                          │   │
│  │  │  Worker    │ │  Worker    │                          │   │
│  │  └────────────┘ └────────────┘                          │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Data Storage Layer                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ PostgreSQL/  │  │     Redis    │  │  File System │         │
│  │ TimescaleDB  │  │   (Cache +   │  │  (Strategy   │         │
│  │ (Primary DB) │  │    Broker)   │  │   Plugins)   │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     External Integration Layer                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Zerodha    │  │     Groww    │  │   Exchanges  │         │
│  │ Kite Connect │  │   Trade API  │  │  (NSE/BSE)   │         │
│  │  WebSocket   │  │  WebSocket   │  │              │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Technology Stack

### Backend Stack

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Web Framework** | FastAPI | 0.104+ | RESTful API server, async support |
| **Task Queue** | Celery | 5.3+ | Async task processing, scheduled jobs |
| **Message Broker** | Redis | 7.2+ | Celery broker + caching + real-time data |
| **Primary Database** | PostgreSQL | 16+ | User data, orders, strategies |
| **Time-Series DB** | TimescaleDB | 2.13+ | Extension on PostgreSQL for market data |
| **ORM** | SQLAlchemy | 2.0+ | Database abstraction layer |
| **Migration Tool** | Alembic | 1.12+ | Database schema migrations |
| **WebSocket** | python-socketio | 5.10+ | Real-time updates to frontend |
| **Auth** | python-jose | 3.3+ | JWT token handling |
| **HTTP Client** | httpx | 0.25+ | Async HTTP requests to broker APIs |
| **Data Processing** | Pandas | 2.1+ | Data manipulation and analysis |
| **Numerical Compute** | NumPy | 1.26+ | Fast numerical operations |
| **Technical Analysis** | TA-Lib | 0.4+ | Technical indicators library |

### Frontend Stack

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Framework** | Next.js | 14+ | React framework with SSR |
| **UI Library** | React | 18+ | Component-based UI |
| **State Management** | Zustand | 4.4+ | Lightweight state management |
| **UI Components** | shadcn/ui | Latest | Pre-built accessible components |
| **Styling** | Tailwind CSS | 3.4+ | Utility-first CSS framework |
| **Charts** | TradingView Lightweight Charts | 4.1+ | Financial charts |
| **Data Grid** | AG Grid | 31+ | Advanced data tables |
| **WebSocket Client** | socket.io-client | 4.6+ | Real-time communication |
| **Forms** | React Hook Form | 7.48+ | Form handling and validation |
| **API Client** | Axios | 1.6+ | HTTP client |

### Infrastructure Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Cloud Provider** | Google Cloud Platform (GCP) | Infrastructure hosting |
| **Compute** | Compute Engine (e2-standard-4) | Single VM instance |
| **Region** | asia-south1 (Mumbai) | Low latency to NSE/BSE |
| **Operating System** | Ubuntu 22.04 LTS | Server OS |
| **Web Server** | Nginx | Reverse proxy, static file serving |
| **Process Manager** | Supervisor | Service management |
| **SSL/TLS** | Let's Encrypt | HTTPS certificates |
| **Monitoring** | Prometheus + Grafana | Metrics and visualization |
| **Logging** | ELK Stack (Lightweight) | Centralized logging |
| **Backup** | GCP Snapshots | Automated backups |

---

## 🗄️ Database Schema Design

### Core Tables

#### 1. Users Table
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(20) NOT NULL CHECK (role IN ('admin', 'trader', 'viewer')),
    is_active BOOLEAN DEFAULT true,
    totp_secret VARCHAR(32),  -- For 2FA
    static_ip VARCHAR(45),  -- SEBI requirement
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
```

#### 2. Broker Connections Table
```sql
CREATE TABLE broker_connections (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    broker VARCHAR(20) NOT NULL CHECK (broker IN ('zerodha', 'groww')),
    api_key VARCHAR(255) NOT NULL,
    api_secret_encrypted TEXT NOT NULL,  -- Encrypted at rest
    access_token TEXT,
    access_token_expires_at TIMESTAMP,
    refresh_token TEXT,
    is_active BOOLEAN DEFAULT true,
    algo_identifier VARCHAR(50) UNIQUE,  -- SEBI algo ID
    algo_registered_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, broker)
);

CREATE INDEX idx_broker_connections_user ON broker_connections(user_id);
CREATE INDEX idx_broker_connections_algo_id ON broker_connections(algo_identifier);
```

#### 3. Strategies Table
```sql
CREATE TABLE strategies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    description TEXT,
    file_path VARCHAR(500) NOT NULL,  -- Path to Python file
    file_hash VARCHAR(64),  -- SHA-256 hash for change detection
    version VARCHAR(20) DEFAULT '1.0.0',
    is_active BOOLEAN DEFAULT true,
    is_system_strategy BOOLEAN DEFAULT false,
    
    -- Strategy Parameters (JSON)
    parameters JSONB,  -- Default parameters
    
    -- Strategy Configuration
    strategy_type VARCHAR(50),  -- 'momentum', 'mean_reversion', 'arbitrage', etc.
    timeframe VARCHAR(20),  -- '1min', '5min', '15min', 'daily', etc.
    instruments JSONB,  -- List of instruments this strategy can trade
    
    -- Risk Parameters
    max_position_size INTEGER,
    max_loss_per_trade DECIMAL(10, 2),
    max_daily_trades INTEGER,
    
    -- Performance Tracking
    total_trades INTEGER DEFAULT 0,
    winning_trades INTEGER DEFAULT 0,
    total_pnl DECIMAL(15, 2) DEFAULT 0,
    
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_modified_by INTEGER REFERENCES users(id)
);

CREATE INDEX idx_strategies_name ON strategies(name);
CREATE INDEX idx_strategies_active ON strategies(is_active);
```

#### 4. Strategy Instances Table
```sql
CREATE TABLE strategy_instances (
    id SERIAL PRIMARY KEY,
    strategy_id INTEGER REFERENCES strategies(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    broker_connection_id INTEGER REFERENCES broker_connections(id) ON DELETE CASCADE,
    
    instance_name VARCHAR(255) NOT NULL,
    mode VARCHAR(20) NOT NULL CHECK (mode IN ('backtest', 'paper', 'live')),
    
    -- Instance-specific parameters (override defaults)
    parameters JSONB,
    
    -- State
    is_running BOOLEAN DEFAULT false,
    started_at TIMESTAMP,
    stopped_at TIMESTAMP,
    
    -- Performance
    total_trades INTEGER DEFAULT 0,
    winning_trades INTEGER DEFAULT 0,
    total_pnl DECIMAL(15, 2) DEFAULT 0,
    current_drawdown DECIMAL(10, 2) DEFAULT 0,
    max_drawdown DECIMAL(10, 2) DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(strategy_id, user_id, instance_name)
);

CREATE INDEX idx_strategy_instances_user ON strategy_instances(user_id);
CREATE INDEX idx_strategy_instances_running ON strategy_instances(is_running);
```

#### 5. Orders Table
```sql
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    
    -- Identity
    order_id VARCHAR(50) UNIQUE NOT NULL,  -- Broker's order ID
    parent_order_id VARCHAR(50),  -- For bracket/cover orders
    
    -- Associations
    user_id INTEGER REFERENCES users(id),
    broker_connection_id INTEGER REFERENCES broker_connections(id),
    strategy_instance_id INTEGER REFERENCES strategy_instances(id),
    
    -- SEBI Compliance
    algo_identifier VARCHAR(50) NOT NULL,  -- SEBI algo tag
    
    -- Order Details
    exchange VARCHAR(10) NOT NULL CHECK (exchange IN ('NSE', 'BSE', 'NFO', 'BFO', 'MCX')),
    tradingsymbol VARCHAR(50) NOT NULL,
    instrument_token BIGINT,
    
    transaction_type VARCHAR(10) NOT NULL CHECK (transaction_type IN ('BUY', 'SELL')),
    order_type VARCHAR(10) NOT NULL CHECK (order_type IN ('MARKET', 'LIMIT', 'SL', 'SL-M')),
    product VARCHAR(10) NOT NULL CHECK (product IN ('CNC', 'MIS', 'NRML', 'MTF')),
    variety VARCHAR(20) NOT NULL CHECK (variety IN ('regular', 'co', 'amo', 'iceberg', 'auction')),
    
    quantity INTEGER NOT NULL,
    price DECIMAL(12, 2),
    trigger_price DECIMAL(12, 2),
    disclosed_quantity INTEGER,
    
    -- Status
    status VARCHAR(20) NOT NULL,  -- 'PENDING', 'OPEN', 'COMPLETE', 'REJECTED', 'CANCELLED'
    status_message TEXT,
    
    -- Execution
    filled_quantity INTEGER DEFAULT 0,
    pending_quantity INTEGER,
    cancelled_quantity INTEGER DEFAULT 0,
    average_price DECIMAL(12, 2),
    
    -- Timestamps
    placed_at TIMESTAMP NOT NULL,
    exchange_timestamp TIMESTAMP,
    last_modified_at TIMESTAMP,
    
    -- Audit
    placed_by VARCHAR(50),  -- 'system', 'manual', 'strategy_name'
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_orders_order_id ON orders(order_id);
CREATE INDEX idx_orders_user ON orders(user_id);
CREATE INDEX idx_orders_strategy_instance ON orders(strategy_instance_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_placed_at ON orders(placed_at);
CREATE INDEX idx_orders_algo_identifier ON orders(algo_identifier);
```

#### 6. Trades Table
```sql
CREATE TABLE trades (
    id SERIAL PRIMARY KEY,
    
    -- Identity
    trade_id VARCHAR(50) UNIQUE NOT NULL,  -- Broker's trade ID
    order_id VARCHAR(50) REFERENCES orders(order_id),
    
    -- Trade Details
    exchange VARCHAR(10) NOT NULL,
    tradingsymbol VARCHAR(50) NOT NULL,
    instrument_token BIGINT,
    
    transaction_type VARCHAR(10) NOT NULL,
    quantity INTEGER NOT NULL,
    price DECIMAL(12, 2) NOT NULL,
    
    -- Timestamps
    exchange_timestamp TIMESTAMP NOT NULL,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_trades_trade_id ON trades(trade_id);
CREATE INDEX idx_trades_order_id ON trades(order_id);
CREATE INDEX idx_trades_exchange_timestamp ON trades(exchange_timestamp);
```

#### 7. Positions Table
```sql
CREATE TABLE positions (
    id SERIAL PRIMARY KEY,
    
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    broker_connection_id INTEGER REFERENCES broker_connections(id) ON DELETE CASCADE,
    strategy_instance_id INTEGER REFERENCES strategy_instances(id),
    
    exchange VARCHAR(10) NOT NULL,
    tradingsymbol VARCHAR(50) NOT NULL,
    instrument_token BIGINT,
    product VARCHAR(10) NOT NULL,
    
    quantity INTEGER NOT NULL,  -- Net quantity (positive for long, negative for short)
    average_price DECIMAL(12, 2) NOT NULL,
    
    -- P&L
    last_price DECIMAL(12, 2),
    pnl DECIMAL(15, 2),
    unrealised_pnl DECIMAL(15, 2),
    realised_pnl DECIMAL(15, 2),
    
    -- Timestamps
    snapshot_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(user_id, tradingsymbol, product, snapshot_date)
);

CREATE INDEX idx_positions_user ON positions(user_id);
CREATE INDEX idx_positions_date ON positions(snapshot_date);
```

### Time-Series Tables (TimescaleDB Hypertables)

#### 8. Market Data Table
```sql
CREATE TABLE market_data (
    time TIMESTAMP NOT NULL,
    instrument_token BIGINT NOT NULL,
    exchange VARCHAR(10) NOT NULL,
    tradingsymbol VARCHAR(50) NOT NULL,
    
    -- OHLCV
    open DECIMAL(12, 2),
    high DECIMAL(12, 2),
    low DECIMAL(12, 2),
    close DECIMAL(12, 2),
    volume BIGINT,
    
    -- Additional
    oi BIGINT,  -- Open Interest (for F&O)
    
    PRIMARY KEY (time, instrument_token)
);

-- Convert to hypertable
SELECT create_hypertable('market_data', 'time');

-- Create indexes
CREATE INDEX idx_market_data_instrument ON market_data(instrument_token, time DESC);
CREATE INDEX idx_market_data_symbol ON market_data(tradingsymbol, time DESC);
```

#### 9. Tick Data Table (Optional - for high-frequency strategies)
```sql
CREATE TABLE tick_data (
    time TIMESTAMP NOT NULL,
    instrument_token BIGINT NOT NULL,
    
    -- Last Traded Price
    ltp DECIMAL(12, 2),
    volume BIGINT,
    
    -- Best Bid/Ask
    bid DECIMAL(12, 2),
    ask DECIMAL(12, 2),
    bid_quantity INTEGER,
    ask_quantity INTEGER,
    
    PRIMARY KEY (time, instrument_token)
);

SELECT create_hypertable('tick_data', 'time', chunk_time_interval => INTERVAL '1 day');

CREATE INDEX idx_tick_data_instrument ON tick_data(instrument_token, time DESC);
```

#### 10. Order Per Second Tracking (SEBI Compliance)
```sql
CREATE TABLE ops_tracking (
    time TIMESTAMP NOT NULL,
    user_id INTEGER NOT NULL,
    broker_connection_id INTEGER NOT NULL,
    algo_identifier VARCHAR(50) NOT NULL,
    
    orders_count INTEGER DEFAULT 1,
    exchange VARCHAR(10),
    
    PRIMARY KEY (time, user_id, algo_identifier)
);

SELECT create_hypertable('ops_tracking', 'time', chunk_time_interval => INTERVAL '1 hour');

CREATE INDEX idx_ops_tracking_user ON ops_tracking(user_id, time DESC);
CREATE INDEX idx_ops_tracking_algo ON ops_tracking(algo_identifier, time DESC);
```

### Audit & Compliance Tables

#### 11. Audit Log Table
```sql
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    
    -- Who
    user_id INTEGER REFERENCES users(id),
    username VARCHAR(50),
    
    -- What
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50),  -- 'order', 'strategy', 'user', 'config', etc.
    entity_id VARCHAR(100),
    
    -- Details
    details JSONB,  -- Full audit trail
    
    -- Context
    ip_address VARCHAR(45),
    user_agent TEXT,
    
    -- When
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_logs_user ON audit_logs(user_id, created_at DESC);
CREATE INDEX idx_audit_logs_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action, created_at DESC);
```

#### 12. Risk Breach Log
```sql
CREATE TABLE risk_breach_logs (
    id SERIAL PRIMARY KEY,
    
    user_id INTEGER REFERENCES users(id),
    strategy_instance_id INTEGER REFERENCES strategy_instances(id),
    
    breach_type VARCHAR(50) NOT NULL,  -- 'position_limit', 'loss_limit', 'ops_limit', etc.
    breach_details JSONB NOT NULL,
    
    action_taken VARCHAR(100),  -- 'order_rejected', 'strategy_stopped', 'alert_sent', etc.
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_risk_breach_logs_user ON risk_breach_logs(user_id, created_at DESC);
CREATE INDEX idx_risk_breach_logs_type ON risk_breach_logs(breach_type, created_at DESC);
```

#### 13. System Events Log
```sql
CREATE TABLE system_events (
    id SERIAL PRIMARY KEY,
    
    event_type VARCHAR(50) NOT NULL,  -- 'startup', 'shutdown', 'error', 'warning', 'info'
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('critical', 'error', 'warning', 'info', 'debug')),
    
    component VARCHAR(100),  -- 'strategy_engine', 'order_manager', 'data_fetcher', etc.
    
    message TEXT NOT NULL,
    details JSONB,
    
    stack_trace TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_system_events_type ON system_events(event_type, created_at DESC);
CREATE INDEX idx_system_events_severity ON system_events(severity, created_at DESC);
CREATE INDEX idx_system_events_component ON system_events(component, created_at DESC);
```

---

## 🏛️ Infrastructure Setup

### GCP Compute Engine Configuration

#### VM Specifications
```yaml
Instance Name: algo-trading-prod
Machine Type: e2-standard-4
  - vCPUs: 4
  - Memory: 16 GB
  - Architecture: x86/64
Region: asia-south1 (Mumbai)
Zone: asia-south1-a
Boot Disk:
  - Type: SSD Persistent Disk
  - Size: 100 GB
  - Image: Ubuntu 22.04 LTS
Additional Disk:
  - Type: SSD Persistent Disk
  - Size: 200 GB (for databases and logs)
  - Mount: /data
Network:
  - VPC: default
  - Static External IP: Yes (for SEBI IP whitelisting)
  - Firewall: Allow HTTP (80), HTTPS (443), SSH (22)
```

### Directory Structure
```
/home/algo-trading/
├── app/                          # Application code
│   ├── api/                      # FastAPI routes
│   │   ├── auth.py
│   │   ├── strategies.py
│   │   ├── orders.py
│   │   ├── data.py
│   │   └── websocket.py
│   ├── core/                     # Core business logic
│   │   ├── strategy_engine.py
│   │   ├── order_manager.py
│   │   ├── risk_manager.py
│   │   ├── backtest_engine.py
│   │   └── portfolio_manager.py
│   ├── brokers/                  # Broker integrations
│   │   ├── base.py
│   │   ├── zerodha.py
│   │   └── groww.py
│   ├── models/                   # SQLAlchemy models
│   ├── schemas/                  # Pydantic schemas
│   ├── services/                 # Business services
│   ├── tasks/                    # Celery tasks
│   ├── strategies/               # User strategies
│   │   ├── base_strategy.py
│   │   └── examples/
│   ├── utils/                    # Utility functions
│   ├── config.py                 # Configuration
│   └── main.py                   # FastAPI app entry
├── frontend/                     # Next.js frontend
│   ├── app/
│   ├── components/
│   ├── lib/
│   └── public/
├── tests/                        # Test suites
├── scripts/                      # Utility scripts
├── logs/                         # Application logs
├── backups/                      # Database backups
└── docker/                       # Docker configs (optional)

/data/
├── postgresql/                   # PostgreSQL data
├── redis/                        # Redis persistence
├── strategies/                   # Strategy plugin files
└── market_data_cache/           # Cached market data
```

### Service Configuration

#### Nginx Configuration
```nginx
# /etc/nginx/sites-available/algo-trading

upstream fastapi {
    server 127.0.0.1:8000;
}

upstream frontend {
    server 127.0.0.1:3000;
}

server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # API routes
    location /api/ {
        proxy_pass http://fastapi;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket
    location /ws/ {
        proxy_pass http://fastapi;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Frontend
    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Static files
    location /_next/static/ {
        proxy_pass http://frontend;
        proxy_cache_valid 200 60m;
        add_header Cache-Control "public, immutable";
    }
}
```

#### Supervisor Configuration
```ini
# /etc/supervisor/conf.d/algo-trading.conf

[program:fastapi]
command=/home/algo-trading/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
directory=/home/algo-trading/app
user=algo-trading
autostart=true
autorestart=true
stderr_logfile=/var/log/algo-trading/fastapi.err.log
stdout_logfile=/var/log/algo-trading/fastapi.out.log

[program:celery-worker]
command=/home/algo-trading/venv/bin/celery -A app.tasks worker --loglevel=info --concurrency=4
directory=/home/algo-trading/app
user=algo-trading
autostart=true
autorestart=true
stderr_logfile=/var/log/algo-trading/celery.err.log
stdout_logfile=/var/log/algo-trading/celery.out.log

[program:celery-beat]
command=/home/algo-trading/venv/bin/celery -A app.tasks beat --loglevel=info
directory=/home/algo-trading/app
user=algo-trading
autostart=true
autorestart=true
stderr_logfile=/var/log/algo-trading/celery-beat.err.log
stdout_logfile=/var/log/algo-trading/celery-beat.out.log

[program:frontend]
command=/usr/bin/npm run start
directory=/home/algo-trading/frontend
user=algo-trading
autostart=true
autorestart=true
stderr_logfile=/var/log/algo-trading/frontend.err.log
stdout_logfile=/var/log/algo-trading/frontend.out.log
environment=NODE_ENV=production,PORT=3000
```

---

## 🔒 Security Architecture

### Authentication Flow

```
1. User Login
   ├─> Email/Password Validation
   ├─> 2FA (TOTP) Verification
   ├─> Generate JWT Access Token (15 min expiry)
   ├─> Generate JWT Refresh Token (7 days expiry)
   └─> Return tokens + user info

2. API Request
   ├─> Extract JWT from Authorization header
   ├─> Verify token signature
   ├─> Check token expiry
   ├─> Extract user_id from token
   ├─> Load user permissions
   └─> Allow/Deny request

3. Token Refresh
   ├─> Validate refresh token
   ├─> Generate new access token
   └─> Return new access token
```

### Encryption Strategy

| Data Type | Encryption Method | Key Storage |
|-----------|------------------|-------------|
| **Passwords** | Argon2 hash | N/A (one-way) |
| **API Keys** | AES-256-GCM | GCP Secret Manager |
| **API Secrets** | AES-256-GCM | GCP Secret Manager |
| **Access Tokens** | Stored encrypted | GCP Secret Manager |
| **TOTP Secrets** | AES-256-GCM | Database (encrypted field) |
| **Database Backups** | AES-256 | GCP KMS |
| **Logs (sensitive)** | AES-256-GCM | Application-level encryption |

### Network Security

```
┌─────────────────────────────────────────────────────────────────┐
│                      External Access Layer                        │
│                                                                   │
│  ┌──────────────┐         ┌──────────────┐                      │
│  │   Cloudflare │────────>│     Nginx    │                      │
│  │   (Optional) │         │ (Reverse     │                      │
│  │   DDoS       │         │  Proxy +     │                      │
│  │  Protection  │         │   SSL/TLS)   │                      │
│  └──────────────┘         └──────────────┘                      │
│                                   │                               │
└───────────────────────────────────┼───────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Application Security Layer                     │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              JWT Authentication Middleware               │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                   │                               │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │         Role-Based Access Control (RBAC)                 │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                   │                               │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Rate Limiting Middleware                    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                   │                               │
└───────────────────────────────────┼───────────────────────────────┘
                                    │
                                    ▼
                         Application Services
```

### RBAC Matrix

| Feature | Admin | Trader | Viewer |
|---------|-------|--------|--------|
| **User Management** | âœ… | ❌ | ❌ |
| **View All Strategies** | âœ… | âœ… | âœ… |
| **Create Strategy** | âœ… | ❌ | ❌ |
| **Modify Strategy** | âœ… | ❌ | ❌ |
| **Delete Strategy** | âœ… | ❌ | ❌ |
| **View Own Trades** | âœ… | âœ… | âœ… |
| **View All Trades** | âœ… | ❌ | ❌ |
| **Execute Trade** | âœ… | âœ… | ❌ |
| **Modify Risk Limits** | âœ… | ❌ | ❌ |
| **Emergency Stop** | âœ… | âœ… | ❌ |
| **View System Logs** | âœ… | ❌ | ❌ |
| **Export Data** | âœ… | âœ… | âœ… |
| **System Config** | âœ… | ❌ | ❌ |

---

## ðŸ"Š Monitoring & Observability

### Metrics to Track

#### System Metrics
- CPU utilization
- Memory utilization
- Disk I/O
- Network I/O
- Service uptime

#### Application Metrics
- API request latency (p50, p95, p99)
- API error rate
- WebSocket connection count
- Active strategy count
- Order processing time
- Database query time
- Celery task queue length
- Celery task processing time

#### Business Metrics
- Orders per second (SEBI compliance)
- Total orders today
- Order success rate
- Trade execution latency
- P&L (real-time)
- Active positions
- Portfolio value
- Strategy performance metrics

### Logging Strategy

#### Log Levels
- **DEBUG**: Development/troubleshooting
- **INFO**: Normal operations, state changes
- **WARNING**: Unusual but handled situations
- **ERROR**: Errors that need attention
- **CRITICAL**: System failures

#### Log Structure (JSON)
```json
{
  "timestamp": "2025-11-11T10:30:45.123Z",
  "level": "INFO",
  "component": "order_manager",
  "message": "Order placed successfully",
  "context": {
    "user_id": 1,
    "order_id": "251111000123456",
    "symbol": "INFY",
    "quantity": 10,
    "price": 1450.50
  },
  "trace_id": "abc-123-def-456"
}
```

---

## ðŸ"„ Backup & Disaster Recovery

### Backup Strategy

| Data | Frequency | Retention | Method |
|------|-----------|-----------|--------|
| **Database** | Every 6 hours | 30 days | GCP Snapshots |
| **Strategy Files** | Daily | 90 days | Git + Cloud Storage |
| **Logs** | Real-time | 90 days | Cloud Logging |
| **Configuration** | On change | 180 days | Git |
| **Trade Data** | Real-time | 7 years | Database + Archive |

### Disaster Recovery Plan

**RTO (Recovery Time Objective):** 4 hours  
**RPO (Recovery Point Objective):** 6 hours

**Recovery Procedure:**
1. Provision new VM from latest snapshot (30 mins)
2. Restore database from backup (1 hour)
3. Restore application code from Git (15 mins)
4. Restore Redis cache (if needed) (15 mins)
5. Verify all services (30 mins)
6. Resume trading (30 mins)

---

## ðŸš€ Performance Optimization

### Database Optimization
- Connection pooling (20 connections)
- Query optimization with EXPLAIN
- Proper indexing strategy
- TimescaleDB for time-series data
- Regular VACUUM and ANALYZE

### API Optimization
- Redis caching for frequently accessed data
- Async I/O for broker API calls
- Response compression (gzip)
- Query result pagination
- Lazy loading for heavy operations

### Frontend Optimization
- Server-side rendering (Next.js)
- Code splitting
- Image optimization
- CDN for static assets
- WebSocket for real-time updates

---

## 🔄 Scalability Considerations

### Horizontal Scaling (Future)
When moving beyond single VM:
1. Separate API server and workers
2. Load balancer for API servers
3. Distributed Redis cluster
4. Database read replicas
5. Separate monitoring infrastructure

### Vertical Scaling (Current)
- Start with e2-standard-4
- Monitor resource utilization
- Upgrade to e2-standard-8 if needed (8 vCPUs, 32 GB RAM)

---

**Next:** Review [Feature Specifications →](04_FEATURE_SPECIFICATIONS.md)

---

*Last Updated: November 11, 2025*
