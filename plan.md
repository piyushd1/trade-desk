# TradeDesk — Plan A: Decision Dashboard for Current Portfolio

## How We Got Here

### Starting Point

The repository contains an institutional-grade algorithmic trading platform with:
- Zerodha OAuth, encrypted tokens, auto-refresh
- Risk management (position limits, kill switch, daily loss tracking)
- Technical analysis (60+ indicators via `ta` library)
- Fundamentals via Yahoo Finance
- SEBI-compliant audit logging
- Order preview/place/modify/cancel with 6-layer pre-trade checks
- WebSocket tick streaming via KiteTicker
- Next.js 14 frontend with dashboard, risk, audit, and settings pages

But the platform feels incomplete. The backend is feature-rich but not connected to a practical user workflow. The frontend is thin and risk/session-centric rather than decision-centric.

### The Planning Conversation

Three candidate plans were evaluated:

**Plan A — Decision Dashboard for Current Portfolio**
Build a dashboard that answers: "what do I hold, how is each position doing, which look technically weak/strong, what deserves review today?"

*Verdict: Best first step.* Low execution risk, leverages existing backend strengths, immediate daily utility.

**Plan B — Daily Nifty 50 / Watchlist Screener**
A daily shortlist of stocks worth attention using existing TA + fundamentals.

*Verdict: Also excellent.* High insight-per-effort, backend-first, less UI work. Best for pure insight focus.

**Plan C — Assisted Trade Terminal**
Semi-automated order entry: you find the stock, the app sizes and places it safely.

*Verdict: Phase 2 only.* Execution multiplies complexity. Auth/session reliability must be proven first. The "bracket order" flow is not as close to done as it sounds.

### Decision: Plan A First

Plan A gives the most immediate daily utility and the lowest risk. The backend APIs for holdings, positions, and margins already exist (`GET /api/v1/data/zerodha/holdings`, `GET /api/v1/data/zerodha/positions`, `GET /api/v1/data/zerodha/margins`). The frontend just doesn't use them.

---

## Verification Findings (Critical Issues Found)

Before building Plan A, a thorough verification pass revealed several critical issues blocking even basic startup and testing.

### 🔴 Critical Blocker 1: Backend Cannot Start Without a `.env` File

`app/config.py` declares 8 fields as **required** (no defaults):
- `SECRET_KEY` — *genuinely security-critical, keep required*
- `DATABASE_URL` — *genuinely required, keep required*
- `JWT_SECRET_KEY` — *genuinely security-critical, keep required*
- `ENCRYPTION_KEY` — *genuinely security-critical, keep required*
- `REDIS_URL` — **not actually used in the API path** (health check stubs it as "unknown"), but required
- `CELERY_BROKER_URL` — **Celery is not imported anywhere in the running app**
- `CELERY_RESULT_BACKEND` — **same as above**
- `STATIC_IP` — **only used for SEBI compliance display**, not functionally critical

**Fix applied**: Give `REDIS_URL`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`, and `STATIC_IP` sensible development defaults so the backend can start without Redis/Celery in development.

### 🔴 Critical Blocker 2: `extra = "forbid"` Crashes Startup

`config.py` uses `extra = "forbid"` which means **any unknown environment variable** in `.env` causes an immediate crash at startup. This is extremely fragile.

**Fix applied**: Changed to `extra = "ignore"`.

### 🟠 Bug: Hardcoded User ID 1 in Dashboard

`frontend/app/dashboard/page.tsx` calls `riskApi.getStatus(1)` with a hardcoded user ID of `1`. This works for a single-user setup but is wrong — it should use the authenticated user's actual ID from `useAuth()`.

**Fix applied**: Use `user?.id` from `useAuth()` hook.

### 🟡 Missing: Portfolio/Holdings Page

There is no frontend page for holdings, positions, or margins. This is Plan A's core feature. The backend APIs exist; the frontend just doesn't call them.

**Fix applied**: Created `/dashboard/portfolio` page with holdings, positions, and margins.

### 🟡 Missing: Portfolio API Methods in `lib/api.ts`

The frontend API client has no methods for the Zerodha portfolio endpoints.

**Fix applied**: Added `portfolioApi` to `lib/api.ts` with `getHoldings()`, `getPositions()`, `getMargins()`.

---

## Plan A — Implementation Scope

### Minimal viable scope (this PR)
1. Fix backend startup blockers (config defaults, `extra` setting)
2. Fix hardcoded user ID
3. Add portfolio API methods
4. Create Portfolio page showing holdings + day positions + margins
5. Add Portfolio to sidebar navigation
6. Document findings in this file

### Out of scope for this PR (future work)
- Technical indicator overlay on portfolio (needs historical data populated)
- Live streaming price updates (complex, needs WebSocket integration)
- Stock screener (Plan B)
- Order placement UI (Plan C)

---

## Architecture Notes for Future Work

### Backend data flow for TA on portfolio
To show RSI/MACD/DMA signals per holding, the data flow is:
1. Get holdings → extract instrument tokens
2. For each token, check if historical OHLCV data exists in local DB
3. If yes, call `TechnicalAnalysisService.compute_indicators(token)`
4. Display the resulting signals

This is realistic but requires step 2 to be populated. The `zerodha_data_management.py` API has endpoints for syncing instruments and historical data, but it requires the instruments to be synced first.

### Frontend auth flow clarification
There are two distinct auth identifiers in play:
- **TradeDesk user** (`user.id`, stored in localStorage after login) — used for risk/audit APIs
- **Zerodha user identifier** (`user_identifier`, stored after OAuth) — used for portfolio/broker APIs

Both must be present for the full portfolio dashboard to work. This is a legitimate design choice but the frontend must handle cases where one or both are missing.

---

## Phased Roadmap

### Phase 1 (this PR) — Verifiable baseline ✅
- Backend starts without manual `.env` wrestling
- Tests can run
- Dashboard shows real user data, not hardcoded IDs
- Portfolio page shows holdings + positions

### Phase 2 — TA signals on portfolio
- Sync instruments + historical data for held stocks
- Add RSI / MACD / DMA snapshot columns to portfolio table
- Add simple "Bullish / Neutral / Weak" badge per holding

### Phase 3 — Daily Screener (Plan B)
- Fixed Nifty 50 universe
- Scoring: SMA trend + MACD crossover + RSI zone + volume
- Output: top 5 names with reasoning
- Delivery: API endpoint → frontend page or Telegram

### Phase 4 — Assisted Execution (Plan C)
- Symbol search
- Order preview with risk check display
- Suggested quantity calculation
- Confirm + place
