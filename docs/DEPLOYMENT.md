# TradeDesk Deployment Guide

Authoritative runbook for deploying TradeDesk onto a Raspberry Pi 4B with Tailscale-only remote access. Last verified: **2026-04-15** against the live Pi deployment.

If you're a new Claude Code session picking up TradeDesk work, read this file and then `docs/plans/HANDOFF-2026-04-15.md` (which has the latest state, discovered gotchas, and pointers to the active plan).

---

## Target architecture

```
Your laptop / phone (on tailnet)
        |
        | https://tradedesk.tail1ad4b2.ts.net/
        |   (Let's Encrypt via Tailscale — no public ports forwarded)
        v
Raspberry Pi 4B (4 GB)
├── tailscaled (host)         — native install, serves TLS + path routing
├── systemd
│   ├── trade-desk-migrate.service        (oneshot — alembic upgrade head)
│   ├── trade-desk.service                (main — docker compose up)
│   └── trade-desk-tailscale-serve.service (oneshot — tailscale serve config)
└── Docker Engine (arm64)
    ├── trade-desk-backend   (FastAPI + uvicorn --workers 1 + SQLite, port 8000)
    └── trade-desk-frontend  (Next.js standalone, port 3001)
```

**Routing**: `tailscale serve` on the host terminates TLS and fans out:
- `https://<tailnet-host>/`      → `http://localhost:3001` (frontend)
- `https://<tailnet-host>/api/*` → `http://localhost:8000/api/*` (backend; the `/api` prefix is re-added because tailscale serve strips the mount prefix — see Troubleshooting §3)

**Data**: SQLite file at `/app/data/tradedesk.db` inside the backend container, backed by the named volume `tradedesk-data` on the Pi host. WAL mode enforced via a SQLAlchemy event listener in `backend/app/database.py` (journal_mode=WAL, busy_timeout=5000, synchronous=NORMAL, foreign_keys=ON).

**Env mode**: `APP_ENV=production` is forced in `docker-compose.prod.yml` so that production middlewares (`TrustedHostMiddleware`, `GZipMiddleware`) are active. The `.env` file on the Pi can still say `APP_ENV=development` — the compose override wins inside the container.

---

## Prerequisites

- **Hardware**: Raspberry Pi 4B with 4 GB RAM minimum, A2-class microSD card (or USB SSD — see Phase 1.5 note in `docs/plans/2026-04-15-pi-deployment-plan.md`)
- **OS**: Raspberry Pi OS Bookworm (64-bit) — earlier Pi OS versions may work but aren't tested
- **Accounts**:
  - Tailscale account with HTTPS certificates enabled at https://login.tailscale.com/admin/dns
  - Zerodha Kite Connect developer app at https://developers.kite.trade (API key + secret issued, redirect URL configured — see §Zerodha OAuth below)
  - (Optional, for multi-broker) IndStocks/IndMoney developer credentials
- **Network**: Pi on the same Tailscale tailnet as the machines you want to access it from

---

## First-time setup

This is the order that was verified end-to-end during the 2026-04-15 deploy.

### 1. Base OS

```bash
sudo apt update && sudo apt upgrade -y && sudo reboot
```

### 2. Tailscale (native on the host, NOT in Docker)

```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up --ssh
```

Then enable HTTPS certificates in the Tailscale admin console:
https://login.tailscale.com/admin/dns → "HTTPS Certificates" → Enable.

Note your tailnet hostname (e.g. `tradedesk.tail1ad4b2.ts.net`) — you'll need it for env config and Kite's redirect URL.

> **Do not install the "Tailscale Docker" option** — we use native Tailscale on the host. A Docker Tailscale would conflict with `tailscale serve` and can't reach `localhost:8000` / `localhost:3001` the same way.

### 3. Docker Engine + Compose v2

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker
docker compose version   # verify v2 plugin is installed
```

### 4. Clone the repo

```bash
# Generate a deploy key on the Pi, add its .pub to GitHub as a Deploy Key
ssh-keygen -t ed25519 -C "pi@tradedesk" -f ~/.ssh/id_ed25519
cat ~/.ssh/id_ed25519.pub   # add this to GitHub Settings → Deploy Keys

git clone git@github.com:piyushd1/trade-desk.git ~/trade-desk
cd ~/trade-desk
```

### 5. Env files

Copy the examples and fill in real values. **Never commit the filled-in files** — they're gitignored.

```bash
cp backend/.env.example backend/.env
cp frontend/.env.local.example frontend/.env.production
chmod 600 backend/.env frontend/.env.production
nano backend/.env        # or your editor of choice
```

Critical backend values you must set:
- `APP_DOMAIN`, `APP_URL`, `API_BASE_URL`, `FRONTEND_URL` → all point at your tailnet hostname
- `SECRET_KEY`, `JWT_SECRET_KEY` → `openssl rand -hex 32` for each (two different values)
- `ENCRYPTION_KEY` → `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
- `ZERODHA_API_KEY`, `ZERODHA_API_SECRET` → from https://developers.kite.trade
- `ZERODHA_REDIRECT_URL` → `https://<tailnet-host>/api/v1/auth/zerodha/callback` — **must match the value registered in Kite's developer console exactly**
- `ZERODHA_USER_IDENTIFIER` → your Zerodha user ID (e.g. `ABC1234`)
- `ADMIN_USERNAME`, `ADMIN_EMAIL`, `ADMIN_PASSWORD` → credentials for the first admin user (seeded manually — see §Seed admin user below)
- `LOG_FILE=/app/logs/app.log` — points into the `tradedesk-logs` named volume

Frontend: `frontend/.env.production` just needs `NEXT_PUBLIC_API_URL=/api/v1` (the relative URL is correct — it resolves against the browser's origin, routed through tailscale serve).

### 6. Install systemd unit templates

```bash
bash ~/trade-desk/deployment/scripts/setup-pi.sh
```

This script is **idempotent** — safe to re-run after `git pull`. It substitutes `{{USER}}` / `{{GROUP}}` / `{{HOME}}` / `{{REPO_PATH}}` into the templates under `deployment/systemd/*.service.template` and installs them at `/etc/systemd/system/` via `sudo tee` (you'll be prompted for your password). Then `sudo systemctl daemon-reload`.

**Important**: if invoked as `sudo bash setup-pi.sh`, the script detects `SUDO_USER` automatically and resolves the real invoking user (not `root`). If you run it without sudo, it prompts internally for the two sudo calls it needs.

### 7. Install the td-sudo toggle (optional but recommended)

Creates `td-sudo-on` / `td-sudo-off` commands that toggle a scoped NOPASSWD sudoers drop-in for the three trade-desk systemd units. Lets you drive systemctl without retyping your password repeatedly, while still requiring a password to toggle on/off.

```bash
sudo bash ~/trade-desk/deployment/scripts/td-sudo-install.sh
```

Usage:
```bash
td-sudo-on           # enable indefinitely (until td-sudo-off)
td-sudo-on 60        # enable for 60 min, auto-disable via systemd transient timer
td-sudo-off          # disable immediately
```

Scope: only `systemctl {enable --now|disable --now|start|stop|restart|status}` on the three `trade-desk-*.service` units. **Nothing else** — `sudo reboot`, `sudo chown`, `sudo cp`, and every other command still require a password. See `deployment/sudoers/trade-desk` for the exact list.

### 8. Build Docker images

```bash
cd ~/trade-desk
docker compose -f deployment/docker/docker-compose.prod.yml build
```

~15 min on a Pi 4 for a cold build (backend has native arm64 compiles for numpy/pandas/cryptography). Subsequent builds are much faster thanks to cache layers. If you OOM mid-build, build sequentially:
```bash
docker compose -f deployment/docker/docker-compose.prod.yml build backend
docker compose -f deployment/docker/docker-compose.prod.yml build frontend
```

### 9. Run Alembic migrations

```bash
td-sudo-on
sudo systemctl enable --now trade-desk-migrate.service
systemctl status trade-desk-migrate.service --no-pager
```

Oneshot unit runs `alembic upgrade head` inside a disposable backend container and exits. Should show `active (exited)` on success. Applies all migrations to a fresh SQLite DB at `/app/data/tradedesk.db`.

### 10. Seed the admin user

Alembic does NOT seed data. The admin user comes from a separate script that reads `ADMIN_*` env vars:

```bash
docker compose -f ~/trade-desk/deployment/docker/docker-compose.prod.yml \
  exec -T backend python scripts/create_default_user.py
```

Expected output: `✅ Admin user created successfully!` with the username from `ADMIN_USERNAME`. If the user already exists, the script reports that and exits cleanly.

### 11. Start the main stack

```bash
sudo systemctl enable --now trade-desk.service
sleep 20
docker compose -f ~/trade-desk/deployment/docker/docker-compose.prod.yml ps
```

Both `trade-desk-backend` and `trade-desk-frontend` should show `Up ... (healthy)` within ~45 seconds (the healthcheck `start_period`). Watch logs with:

```bash
docker compose -f ~/trade-desk/deployment/docker/docker-compose.prod.yml logs backend | tail -60
```

### 12. Enable tailscale serve (TLS + path routing)

```bash
sudo systemctl enable --now trade-desk-tailscale-serve.service
tailscale serve status
```

Expected output:
```
https://tradedesk.tail1ad4b2.ts.net (tailnet only)
|-- /    proxy http://localhost:3001
|-- /api proxy http://localhost:8000/api
```

### 13. Local smoke tests

```bash
curl -sI http://localhost:8000/health              # expect HTTP/1.1 200 OK
curl -sI http://localhost:3001/                    # expect HTTP/1.1 200 OK
curl -sI https://tradedesk.tail1ad4b2.ts.net/      # expect HTTP/2 200
curl -s https://tradedesk.tail1ad4b2.ts.net/api/v1/auth/zerodha/connect | head -c 200
```

### 14. Log in from another tailnet device

Open `https://tradedesk.tail1ad4b2.ts.net/` in a browser on another tailnet device (laptop, phone). Log in with `ADMIN_USERNAME` + the plaintext `ADMIN_PASSWORD` from `backend/.env`.

### 15. Zerodha OAuth

From the Settings page in the TradeDesk UI, click **Connect to Zerodha**. You'll be redirected to Kite for authorization. After allowing, Kite redirects back to the backend callback which stores an encrypted access token in `broker_sessions` and redirects you to a success page on the frontend, which then calls `/api/v1/auth/zerodha/session/claim` to link the session to your authenticated user. You're then bounced to `/dashboard`.

Portfolio, Holdings, Margins pages should now load real data from Kite.

> **Token lifecycle**: Kite access tokens expire at **6:00 AM IST daily**. Standard retail Kite Connect apps do not receive `refresh_token`s, so daily re-authentication is required. The OAuth round-trip is ~10 seconds. This is a Kite contract, not a TradeDesk bug.

### 16. Reboot test (required before declaring deployment done)

```bash
sudo reboot
# Wait for the Pi to come back, then:
ssh piyushdev@tradedesk.tail1ad4b2.ts.net
systemctl is-active trade-desk-migrate trade-desk trade-desk-tailscale-serve
docker compose -f ~/trade-desk/deployment/docker/docker-compose.prod.yml ps
curl -sI https://tradedesk.tail1ad4b2.ts.net/
```

All three services should be `active`, both containers healthy, tailnet URL 200. **The deployment is not considered done until this passes** — until then you don't know whether the systemd wiring survives a power cycle.

---

## Daily operations

### Zerodha re-auth

Every morning after 6:00 AM IST, the access token expires. The first API call fails, you see "Could not load margins" on the portfolio page, you click **Connect to Zerodha** from Settings, OAuth round-trip completes, done. Ten seconds of friction.

Phase B of the active plan (see `~/.claude/plans/`) improves the UX — proactive expiry banner in the nav, one-click re-auth flow, audit-log entry on missed-snapshot events.

### Watching logs

```bash
docker compose -f ~/trade-desk/deployment/docker/docker-compose.prod.yml logs backend -f   # follow backend
docker compose -f ~/trade-desk/deployment/docker/docker-compose.prod.yml logs frontend -f  # follow frontend
journalctl -u trade-desk.service -f                                                         # follow systemd wrapper
journalctl -u trade-desk-migrate.service --no-pager                                         # migrate oneshot history
journalctl -u trade-desk-tailscale-serve.service --no-pager                                 # serve oneshot history
```

### Updating the app

```bash
cd ~/trade-desk
git pull origin master
docker compose -f deployment/docker/docker-compose.prod.yml build
td-sudo-on
sudo systemctl restart trade-desk-migrate.service   # apply any new migrations
sudo systemctl restart trade-desk.service           # pick up new images
td-sudo-off
```

### Backup & restore *(Phase B Stage 5 — not yet implemented)*

Once `deployment/scripts/backup-sqlite.sh` and the cron are in place (per the active plan), a nightly backup of the SQLite DB + env files will run automatically. Until then, manual backup is:

```bash
docker compose -f ~/trade-desk/deployment/docker/docker-compose.prod.yml \
  exec -T backend sqlite3 /app/data/tradedesk.db \
  ".backup '/app/data/manual-backup-$(date +%Y%m%d).db'"
docker cp trade-desk-backend:/app/data/manual-backup-*.db ~/backups/
```

---

## Troubleshooting

### 1. Backend container keeps restarting

Check logs: `docker compose -f ~/trade-desk/deployment/docker/docker-compose.prod.yml logs backend`. Common causes:

- **Alembic migration hasn't been run yet** — `sudo systemctl start trade-desk-migrate.service`, confirm it exits cleanly, then retry.
- **`.env` file missing or mode-600 wrong owner** — verify with `ls -la ~/trade-desk/backend/.env`, should be owned by the Pi user, mode `-rw-------`.
- **Volume permission denied on `/app/data/tradedesk.db`** — this should be fixed permanently by the Dockerfile `mkdir -p logs data` (ensures fresh volumes inherit tradedesk ownership). If you still hit this on an existing volume: `docker compose -f ~/trade-desk/deployment/docker/docker-compose.prod.yml run --rm -u 0 --entrypoint sh backend -c 'chown -R tradedesk:tradedesk /app/data /app/logs'`

### 2. `/health` returns 400 Bad Request when curl'd from inside the container

Fixed as of commit `6e2a533`. `TrustedHostMiddleware` now allows `localhost` and `127.0.0.1` in addition to the configured `APP_DOMAIN`.

### 3. `/api/v1/*` routes return 404 via tailscale but work on localhost:8000

Fixed as of commit `6e2a533`. `tailscale serve --set-path=/api` strips the mount prefix before forwarding, so the backend target URL must be `http://localhost:8000/api` (not just `http://localhost:8000`) to re-add it. See `deployment/systemd/trade-desk-tailscale-serve.service.template:38`.

### 4. `APP_ENV=production` forces SQLAlchemy to crash with `TypeError: Invalid argument(s) 'pool_size'`

Fixed as of commit `6e2a533`. `backend/app/database.py` now branches pool config on `DATABASE_URL.startswith('sqlite')` rather than on `APP_ENV`, because SQLite's `aiosqlite` dialect uses `NullPool` and rejects pool-tuning args.

### 5. `Invalid redirect URI` on Zerodha OAuth

The `ZERODHA_REDIRECT_URL` in `backend/.env` must **exactly** match what's registered in the Kite Connect developer console at https://developers.kite.trade. Including trailing slashes, protocol, and path. Fix mismatches and restart the backend container.

### 6. OAuth succeeds but Portfolio page still shows 403 / "Could not load margins"

Fixed as of commit `d58cdf1`. The session claim flow was missing — now the frontend callback page automatically calls `POST /api/v1/auth/zerodha/session/claim` with the user's JWT after OAuth, linking the `broker_session` row to `current_user.id`. Without this step, `validate_user_owns_session` fails because `broker_session.user_id` stays `NULL`.

### 7. `Your kernel does not support memory limit capabilities` warning

Cosmetic on Pi OS Bookworm (cgroup v1/v2 transition artifact). The `mem_limit` values in `docker-compose.prod.yml` are advisory in this kernel and get silently dropped. Containers still run within host memory constraints. Not a blocker; ignore.

---

## Uninstall / rollback

```bash
# Stop and disable all three systemd units
td-sudo-on
sudo systemctl disable --now trade-desk-tailscale-serve.service
sudo systemctl disable --now trade-desk.service
sudo systemctl disable --now trade-desk-migrate.service
td-sudo-off

# Remove containers (keeps named volumes so data survives)
cd ~/trade-desk
docker compose -f deployment/docker/docker-compose.prod.yml down

# Remove containers AND volumes (DESTRUCTIVE — deletes SQLite DB)
docker compose -f deployment/docker/docker-compose.prod.yml down -v

# Turn off tailscale serve
sudo tailscale serve --https=443 off
```

---

## Reference

- **Active plan**: `~/.claude/plans/cryptic-greeting-cray.md` — currently-executing work (Phase B multi-broker data plumbing)
- **Original architectural plan**: `docs/plans/2026-04-15-pi-deployment-plan.md`
- **Deploy-time handoff state**: `docs/plans/HANDOFF-2026-04-15.md`
- **Compose file**: `deployment/docker/docker-compose.prod.yml`
- **Dockerfiles**: `deployment/docker/Dockerfile.{backend,frontend}`
- **Systemd templates**: `deployment/systemd/*.service.template`
- **Setup script**: `deployment/scripts/setup-pi.sh`
- **td-sudo scripts**: `deployment/scripts/td-sudo-*.sh`
- **Sudoers drop-in**: `deployment/sudoers/trade-desk`
