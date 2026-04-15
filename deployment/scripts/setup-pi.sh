#!/usr/bin/env bash
#
# TradeDesk Pi Setup Script
# -------------------------
# Idempotent installer. Safe to re-run after `git pull` to re-install systemd units.
#
# What it does:
#   1. Runs preflight checks (Docker, Compose, Tailscale present)
#   2. Copies .env.example to .env if missing (warns you to fill in real values)
#   3. Substitutes {{USER}} / {{GROUP}} / {{REPO_PATH}} in systemd templates
#   4. Installs the substituted units to /etc/systemd/system
#   5. Runs systemctl daemon-reload
#   6. Prints the manual next-step commands (does NOT auto-enable services)
#
# Usage:
#   cd ~/trade-desk
#   ./deployment/scripts/setup-pi.sh
#
# You'll be prompted for sudo twice: once to write the systemd unit files,
# once to reload the daemon. Nothing else touches the system.

set -euo pipefail

### Colors ###
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

info()  { echo -e "${GREEN}[info]${NC}  $*"; }
warn()  { echo -e "${YELLOW}[warn]${NC}  $*"; }
err()   { echo -e "${RED}[err ]${NC}  $*" >&2; }
step()  { echo -e "\n${BLUE}==>${NC} $*"; }

### Resolve paths ###
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_PATH="$(cd "${SCRIPT_DIR}/../.." && pwd)"
CURRENT_USER="$(id -un)"
CURRENT_GROUP="$(id -gn)"
CURRENT_HOME="${HOME}"
COMPOSE_FILE="${REPO_PATH}/deployment/docker/docker-compose.prod.yml"
SYSTEMD_DIR="/etc/systemd/system"
TEMPLATE_DIR="${REPO_PATH}/deployment/systemd"

BACKEND_ENV="${REPO_PATH}/backend/.env"
FRONTEND_ENV="${REPO_PATH}/frontend/.env.production"

### Preflight ###
step "Preflight checks"

if [[ ! -d "${REPO_PATH}" ]]; then
    err "Repo path not found: ${REPO_PATH}"
    exit 1
fi
info "Repo:  ${REPO_PATH}"
info "User:  ${CURRENT_USER}"
info "Group: ${CURRENT_GROUP}"

if ! command -v docker &>/dev/null; then
    err "Docker not installed. Install with:"
    err "    curl -fsSL https://get.docker.com | sh"
    err "    sudo usermod -aG docker \$USER && newgrp docker"
    exit 1
fi
info "Docker: $(docker --version)"

if ! docker compose version &>/dev/null; then
    err "Docker Compose v2 plugin not installed."
    err "Install the docker-compose-plugin package, or reinstall Docker via get.docker.com"
    exit 1
fi
info "Compose: $(docker compose version --short 2>/dev/null || echo 'installed')"

if ! command -v tailscale &>/dev/null; then
    err "Tailscale not installed. Install with:"
    err "    curl -fsSL https://tailscale.com/install.sh | sh"
    err "    sudo tailscale up --ssh"
    exit 1
fi
info "Tailscale: $(tailscale version | head -1)"

if ! groups "${CURRENT_USER}" | grep -q '\bdocker\b'; then
    warn "User '${CURRENT_USER}' is NOT in the 'docker' group."
    warn "You'll get 'permission denied on docker.sock' errors."
    warn "Run:  sudo usermod -aG docker ${CURRENT_USER} && newgrp docker"
    warn "Then re-run this script."
    exit 1
fi

### .env file bootstrap ###
step ".env files"

if [[ ! -f "${BACKEND_ENV}" ]]; then
    warn "backend/.env does not exist. Copying from backend/.env.example."
    warn "YOU MUST EDIT THIS FILE with real Zerodha credentials, JWT_SECRET_KEY, ENCRYPTION_KEY, etc."
    warn "The backend will not start correctly with placeholder values."
    cp "${REPO_PATH}/backend/.env.example" "${BACKEND_ENV}"
    chmod 600 "${BACKEND_ENV}"
    info "Created: ${BACKEND_ENV} (mode 600)"
else
    info "backend/.env: present"
    chmod 600 "${BACKEND_ENV}"
fi

if [[ ! -f "${FRONTEND_ENV}" ]]; then
    warn "frontend/.env.production does not exist. Copying from frontend/.env.local.example."
    cp "${REPO_PATH}/frontend/.env.local.example" "${FRONTEND_ENV}"
    chmod 600 "${FRONTEND_ENV}"
    info "Created: ${FRONTEND_ENV} (mode 600)"
else
    info "frontend/.env.production: present"
    chmod 600 "${FRONTEND_ENV}"
fi

### Install systemd units ###
step "Systemd unit templates → ${SYSTEMD_DIR}"

shopt -s nullglob
templates=( "${TEMPLATE_DIR}"/*.service.template )
shopt -u nullglob

if [[ ${#templates[@]} -eq 0 ]]; then
    err "No *.service.template files found in ${TEMPLATE_DIR}"
    exit 1
fi

for template in "${templates[@]}"; do
    unit_name="$(basename "${template}" .template)"
    target="${SYSTEMD_DIR}/${unit_name}"

    info "Installing ${unit_name}"
    sed \
        -e "s|{{USER}}|${CURRENT_USER}|g" \
        -e "s|{{GROUP}}|${CURRENT_GROUP}|g" \
        -e "s|{{HOME}}|${CURRENT_HOME}|g" \
        -e "s|{{REPO_PATH}}|${REPO_PATH}|g" \
        "${template}" | sudo tee "${target}" > /dev/null
    sudo chmod 644 "${target}"
done

sudo systemctl daemon-reload
info "systemd daemon reloaded"

### Done ###
cat <<EOF

${GREEN}============================================================${NC}
${GREEN} Setup complete.${NC}
${GREEN}============================================================${NC}

Next steps — run these manually (the script does not auto-enable services):

  ${BLUE}1. Review and edit .env files with real values:${NC}
       nano ${BACKEND_ENV}
       nano ${FRONTEND_ENV}

  ${BLUE}2. Build the Docker images (5–10 min on a Pi 4):${NC}
       docker compose -f ${COMPOSE_FILE} build

  ${BLUE}3. Run migrations (via the dedicated oneshot service):${NC}
       sudo systemctl enable --now trade-desk-migrate.service
       systemctl status trade-desk-migrate.service

  ${BLUE}4. Start the main stack:${NC}
       sudo systemctl enable --now trade-desk.service
       docker compose -f ${COMPOSE_FILE} ps

  ${BLUE}5. Enable HTTPS in the Tailscale admin console (if you haven't):${NC}
       https://login.tailscale.com/admin/dns
       (toggle "HTTPS Certificates")

  ${BLUE}6. Start the Tailscale serve reverse proxy:${NC}
       sudo systemctl enable --now trade-desk-tailscale-serve.service
       tailscale serve status

  ${BLUE}7. Smoke test (on the Pi):${NC}
       curl -f http://localhost:8000/health
       curl -f http://localhost:3001/

  ${BLUE}8. Smoke test from another tailnet device (laptop or phone):${NC}
       TS_HOST=\$(tailscale status --json | jq -r '.Self.DNSName | rtrimstr(".")')
       echo "Open: https://\${TS_HOST}/"

  ${BLUE}9. Reboot and verify everything comes back:${NC}
       sudo reboot
       # after reboot:
       systemctl status trade-desk-migrate trade-desk trade-desk-tailscale-serve

EOF
