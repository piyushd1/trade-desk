# TradeDesk — Pi Deployment: Overall Plan of Action (v2)

## Context

TradeDesk (FastAPI backend + Next.js frontend + SQLite + Zerodha Kite API) runs only on a **borrowed MacBook that must be returned**. Target: **always-on Raspberry Pi 4B (4GB)** at home, **Tailscale-only remote access** (no public ports), plus a **data pipeline** that snapshots portfolio state every 15 min into SQLite. This is Roadmap Phase 1 (paper trading + data pipeline); later phases add MCP agents, live trading, metrics.

> **Note**: Pi first-boot troubleshooting is being handled separately by the user and is not part of this plan. This plan assumes SSH access to the Pi is already working before Stage 1 begins.

**Uncommitted local fixes on the Mac** (must commit + push before Pi can `git clone`):
- `backend/requirements.txt` — `pytest==9.0.0`/`pytest-asyncio==1.3.0` → `8.4.2`/`1.2.0`
- `frontend/package.json` + `package-lock.json` — Next.js 14.2.18 → 15.5.15 (0 vulns)
- `frontend/app/dashboard/page.tsx` — dead `health` query removed

**v2 changes from feedback**: Caddy removed in favor of `tailscale serve`; APScheduler replaces asyncio loop; SQLite `.backup` replaces rsync; WAL mode + explicit migration service; Pi→GitHub SSH key. Pi first-boot troubleshooting moved out of scope (handled separately).

---

## Storage Choice (cross-cutting decision)

| Role | Phase 1 (now) | Phase 1.5 (soon) | Phase 3 (later) |
|---|---|---|---|
| OS + Docker volumes | A2 microSD | UASP-supported USB SSD | unchanged |
| Backup target | Spinning HDD on **powered USB hub** (or external PSU) | unchanged | unchanged |

SD cards will wear out under constant DB writes within ~12 months. Moving the DB and Docker volumes to a proper USB SSD is a **Phase 1.5 task** — not a blocker for Phase 1, but must be tracked. The spinning HDD is suitable only as a backup target, and only when powered externally (a Pi 4 USB bus cannot reliably drive an unpowered 3.5" HDD).

---

## STAGE 1 — Mac-Side Prep (Before the Mac Is Returned)

- [x] Create SSH keypair on Mac if missing
- [x] Commit uncommitted fixes (commit 3eb4159)
- [x] Push to GitHub (master)
- [x] Back up secrets to password manager (user's responsibility — not tracked in git)

---

## STAGE 2 — Pi Base Setup

- [x] `sudo apt update && sudo apt upgrade -y && sudo reboot`
- [x] Install Tailscale native on host: `curl -fsSL https://tailscale.com/install.sh | sh && sudo tailscale up --ssh`
- [x] Enable HTTPS in Tailscale admin console (https://login.tailscale.com/admin/dns)
- [x] Note tailnet hostname: `tradedesk.tail1ad4b2.ts.net`
- [x] Install Docker: `curl -fsSL https://get.docker.com | sh && sudo usermod -aG docker $USER && newgrp docker`
- [x] Generate Pi→GitHub SSH key and add as Deploy Key on repo
- [x] Clone: `git clone git@github.com:piyushd1/trade-desk.git ~/trade-desk`
- [x] Place secrets: `~/trade-desk/backend/.env` and `~/trade-desk/frontend/.env.production` populated

---

## STAGE 3 — Docker Stack + Tailscale Serve (TLS)

**Goal**: `docker compose up -d` runs backend + frontend; `tailscale serve` fronts them with valid HTTPS; systemd brings it all back on reboot.

### Key architectural choice: `tailscale serve`, not Caddy

Caddy's auto-TLS is designed for public ACME, not `.ts.net` hostnames. Tailscale's own `serve` subcommand does TLS termination for tailnet hostnames using Let's Encrypt certs for `*.ts.net`, and can path-route to different local services. This removes Caddy from Phase 1 entirely — fewer moving parts.

```
sudo tailscale serve --bg --https=443 --set-path=/api http://localhost:8000  # backend API
sudo tailscale serve --bg --https=443 http://localhost:3001                  # frontend (root)
sudo tailscale serve status                                                  # verify
```

Caddy can still be added in Phase 1.5/2 if we need headers, rate limiting, or basic-auth gates — not before.

### Files created/modified in Stage 3

| Action | Path | Commit |
|---|---|---|
| MODIFY | `deployment/docker/Dockerfile.frontend` — `node:18-alpine` → `node:20-alpine` | 5ebde78 |
| MODIFY | `deployment/docker/Dockerfile.backend` — CMD pinned `--workers 1` | 5ebde78 |
| MODIFY | `backend/app/database.py` — SQLite PRAGMA event listener (WAL, busy_timeout, synchronous=NORMAL, foreign_keys=ON) | 5ebde78 |
| MODIFY | `frontend/next.config.js` — added `output: 'standalone'`, removed deprecated `swcMinify` | d02c3d3 |
| CREATE | `deployment/docker/docker-compose.prod.yml` — Pi-specific compose | 5ebde78 |
| CREATE | `deployment/systemd/trade-desk-migrate.service.template` — oneshot for Alembic migrations | 5ebde78 |
| CREATE | `deployment/systemd/trade-desk.service.template` — main Docker Compose wrapper | 5ebde78 |
| CREATE | `deployment/systemd/trade-desk-tailscale-serve.service.template` — TLS + path routing | 5ebde78 |
| CREATE | `deployment/scripts/setup-pi.sh` — idempotent installer | 5ebde78 |
| CREATE | `frontend/public/.gitkeep` — fixes Dockerfile COPY failure | d02c3d3 |

### SQLite hardening (backend/app/database.py)

```python
if settings.DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine.sync_engine, "connect")
    def _set_sqlite_pragmas(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
```
WAL lets reads and writes coexist without blocking. Busy timeout absorbs brief lock contention. `synchronous=NORMAL` is safe with WAL and gives a big perf bump.

### Deploy commands on Pi (after `setup-pi.sh` has run once)

```bash
cd ~/trade-desk
docker compose -f deployment/docker/docker-compose.prod.yml build

# Run migrations via oneshot systemd
sudo systemctl enable --now trade-desk-migrate.service
systemctl status trade-desk-migrate.service --no-pager

# Start main stack
sudo systemctl enable --now trade-desk.service
sleep 10
docker compose -f deployment/docker/docker-compose.prod.yml ps

# Local smoke test
curl -f http://localhost:8000/health
curl -f http://localhost:3001/

# Enable tailscale serve for TLS + path routing
sudo systemctl enable --now trade-desk-tailscale-serve.service
tailscale serve status

# External smoke test (from another tailnet device)
curl -f https://tradedesk.tail1ad4b2.ts.net/api/v1/health
```

### Reboot test (critical, do not skip)

`sudo reboot` → verify all three systemd units come back `active` and the UI loads over Tailscale. Don't declare Stage 3 done until this passes.

---

## STAGE 4 — Data Pipeline (Roadmap Phase 1 features)

### Database

New Alembic migration `add_portfolio_snapshots.py`:
```
portfolio_snapshots
  id                INTEGER PK
  user_id           INTEGER FK users.id
  captured_at_bucket DATETIME NOT NULL   -- UTC, floored to 15-min boundary
  captured_at       DATETIME NOT NULL   -- actual capture time (may differ slightly)
  total_value       NUMERIC  NOT NULL
  total_pnl         NUMERIC  NOT NULL
  realized_pnl      NUMERIC  NOT NULL
  unrealized_pnl    NUMERIC  NOT NULL
  holdings_json     TEXT     NOT NULL   -- raw payload for future re-analysis
  UNIQUE (user_id, captured_at_bucket)  -- idempotency: one row per 15-min slot per user
  INDEX (user_id, captured_at_bucket DESC)
```

The `UNIQUE` constraint is the **final defense against duplicate writes**. Even if two processes try to insert for the same slot, one wins and the other gets an integrity error we can ignore.

### Scheduler

Use **APScheduler `AsyncIOScheduler`** in the FastAPI lifespan, not a raw asyncio task loop. Combined with three safety layers:

1. **`--workers 1` pinned** in Dockerfile.backend (so only one scheduler instance can exist in the container)
2. **File-based lock** at `/app/data/scheduler.lock` using `fcntl.flock` — if another process is holding the lock (unlikely, given --workers 1, but defensive), we skip startup
3. **DB UNIQUE constraint** as last line of defense

New: `backend/app/services/snapshot_scheduler.py`
- Registered in FastAPI `lifespan` (not `@app.on_event`, which is deprecated in recent FastAPI)
- `AsyncIOScheduler` with a `CronTrigger` for `*/15 * * * 1-5` (every 15 min, Mon-Fri)
- Inside the job: check if market is open (09:15–15:30 IST, not a holiday); if not, return silently
- **Retry policy**: 3 attempts with exponential backoff (30s, 60s, 120s) on Zerodha API failure
- **Backfill on startup**: query the most recent bucket; if the expected slot for "now" is missing and market is open, capture it immediately
- Writes one row per successful fetch; on `IntegrityError` (duplicate bucket), log info and continue

### Holiday calendar

Hardcoded list in git — no external service dependency for Phase 1:
- `backend/config/nse_holidays.yaml` — YAML file with 2026 + 2027 NSE holidays (manually updated yearly, tracked in git)
- Loader in `backend/app/utils/market_calendar.py` with functions `is_market_open(dt: datetime) -> bool` and `next_market_open(dt: datetime) -> datetime`
- Covers: weekends, gazetted holidays, trading holidays published by NSE annually

### Broker code location

Recommendation: create `backend/app/brokers/zerodha/` (not `services/`). This isolates vendor-specific code from business logic, making a future Upstox / Angel One addition a drop-in rather than a rewrite. **Stage 4 should include an Explore pass before implementation** to locate whatever exists today and migrate it only if cheap to do so.

### API contract

`GET /api/v1/portfolio/history`

Query params:
- `days` (optional int, default 30, max 365)
- `from` (optional ISO 8601 datetime) — overrides `days`
- `to` (optional ISO 8601 datetime, default now)

Response:
```json
{
  "snapshots": [
    {
      "captured_at": "2026-04-14T09:15:00Z",
      "total_value": 1234567.89,
      "total_pnl": 12345.67,
      "realized_pnl": 6789.00,
      "unrealized_pnl": 5556.67
    }
  ],
  "window": { "from": "...", "to": "..." },
  "count": 42
}
```
Empty state: `{"snapshots": [], "window": {...}, "count": 0}` — chart shows "No data yet — first snapshot captures during next market window".

Timezone: UTC in DB, UTC in API payload, IST in UI rendering.

### Frontend

- **Assume `frontend/app/portfolio/page.tsx` does not exist and create it from scratch** (Explore-verify before implementation).
- Reuse pattern from `frontend/app/dashboard/page.tsx` lines 32–37 (`useQuery` + API client).
- Reuse `Card`/`CardHeader`/`CardContent` from `@/components/ui/card`.
- Reuse `LoadingSpinner` from `@/components/shared/LoadingSpinner`.
- Chart: recharts `LineChart` (already a dep at `recharts ^2.15.4`) — total_value over selected window (7d/30d/90d toggle).
- Add `portfolioApi.getHistory(days)` in `frontend/lib/api.ts`.

---

## STAGE 5 — Backup, Restore, & Ops

**Moved earlier in priority**: backup must be proven working before Stage 4 starts accumulating data we care about.

### SQLite backup (the right way)

Never rsync a live SQLite DB — **use the native `.backup` command**, which is safe under concurrent writes and WAL mode:

```bash
# nightly cron: /etc/cron.d/tradedesk-backup
0 2 * * * piyush /home/piyush/trade-desk/deployment/scripts/backup-sqlite.sh
```

`deployment/scripts/backup-sqlite.sh` (to be created in Stage 5):
```bash
#!/bin/bash
set -euo pipefail
BACKUP_DIR="/mnt/backup/tradedesk/$(date +%Y-%m-%d)"
mkdir -p "$BACKUP_DIR"

# Native SQLite backup (safe, atomic, WAL-aware)
docker compose -f /home/piyush/trade-desk/deployment/docker/docker-compose.prod.yml \
  exec -T backend sqlite3 /app/data/tradedesk.db \
  ".backup '/app/data/backup-$(date +%H%M).db'"

# Copy to spinning HDD
docker cp $(docker compose -f /home/piyush/trade-desk/deployment/docker/docker-compose.prod.yml ps -q backend):/app/data/backup-*.db "$BACKUP_DIR/tradedesk.db"

# Integrity check on the copy
sqlite3 "$BACKUP_DIR/tradedesk.db" "PRAGMA integrity_check;" | grep -q ok || exit 1

# rsync .env + config (these are static, safe to rsync)
rsync -a /home/piyush/trade-desk/backend/.env "$BACKUP_DIR/"
rsync -a /home/piyush/trade-desk/frontend/.env.production "$BACKUP_DIR/"

# Rotate: keep 30 days
find /mnt/backup/tradedesk/ -maxdepth 1 -type d -mtime +30 -exec rm -rf {} +
```

### Restore drill (required, not optional)

Monthly cron that:
1. Picks the most recent backup
2. Copies to a scratch location
3. Runs `sqlite3 scratch.db "PRAGMA integrity_check; SELECT COUNT(*) FROM portfolio_snapshots;"`
4. Alerts (log + mail local root) if integrity check fails

Don't declare Phase 1 "done" until one successful end-to-end restore drill has run.

### HDD mount

- Powered USB hub OR external PSU (non-negotiable for a spinning HDD on a Pi 4)
- Format ext4, mount at `/mnt/backup` via `/etc/fstab` with `nofail` option (so Pi still boots if HDD disconnected)
- `chown piyush:piyush /mnt/backup`

### Other ops

- Weekly `docker image prune -f`
- Tailscale MagicDNS confirmed on
- Log rotation: already handled by Docker driver, capped at 10MB × 3 files per container in compose.prod.yml

---

## STAGE 6 — Context Portability (Survive the Mac Return)

Once this Mac is gone, any new machine resumes via git:

1. Plan file committed at `docs/plans/2026-04-15-pi-deployment-plan.md` ← you're reading it
2. Handoff state at `docs/plans/HANDOFF-2026-04-15.md` ← read this first
3. All fixes + config in `master`

### Resume workflow on any new machine
```bash
# Install Tailscale, join tailnet
ssh piyush@tradedesk.local   # or tailnet hostname
cd ~/trade-desk && git pull
# Start Claude Code (on the Pi or on the new machine)
```
Then prompt: *"Read `docs/plans/HANDOFF-2026-04-15.md` and then `docs/plans/2026-04-15-pi-deployment-plan.md` — we're continuing a prior session."*

---

## Verification

### After Stage 3
1. `docker compose ps` → backend + frontend `healthy`
2. `systemctl status trade-desk-migrate trade-desk trade-desk-tailscale-serve` → all green
3. On Pi: `curl -f http://localhost:8000/health`, `curl -f http://localhost:3001/`
4. `sqlite3 data/tradedesk.db "PRAGMA journal_mode;"` → returns `wal`
5. From tailnet laptop: `https://tradedesk.tail1ad4b2.ts.net/dashboard` — login + UI works
6. From non-tailnet phone: hostname does not resolve (correct)
7. `sudo reboot` → everything comes back healthy

### After Stage 5 (backup before Stage 4 data)
8. Run backup script manually → verify backup file exists + integrity check passes
9. Run restore drill manually → verify it reads the backup and returns a row count

### After Stage 4
10. Wait 30 min past market open, then:
    ```bash
    docker compose exec backend sqlite3 /app/data/tradedesk.db \
      "SELECT COUNT(*), MIN(captured_at), MAX(captured_at) FROM portfolio_snapshots"
    ```
    → count ≥ 1, recent timestamps
11. Restart the backend container mid-window → verify no duplicate row for the same bucket (UNIQUE constraint doing its job)
12. `curl https://tradedesk.tail1ad4b2.ts.net/api/v1/portfolio/history?days=1` → non-empty JSON
13. Portfolio page renders chart with ≥ 1 data point

---

## Explicit Non-Goals for Phase 1

- **Live (real-money) trading** — Phase 2
- **MCP server for Claude** — Phase 1.5
- **Celery + Redis workers** — Phase 1.5 (only if APScheduler becomes insufficient)
- **Caddy / reverse proxy** — deferred until we actually need headers/rate limits/basic-auth
- **Multi-worker uvicorn** — Phase 1.5 (would require moving scheduler out of process)
- **Prometheus + Grafana** — Phase 3
- **Public internet exposure** — **never**
- **Auto-migrations inside the backend container on every start** — explicit separate `trade-desk-migrate.service` is the only path
- **USB SSD migration** — Phase 1.5 (A2 microSD is fine for Phase 1)
- **CI/CD to Pi** — out of scope; manual `git pull && systemctl restart trade-desk` is fine
- **Multi-user** — Phase 3
