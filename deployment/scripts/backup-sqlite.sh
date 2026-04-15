#!/bin/bash
# backup-sqlite.sh — nightly backup of the TradeDesk SQLite DB + env files.
#
# Uses native `sqlite3 .backup` via `docker compose exec backend` which is
# WAL-safe and atomic even under concurrent writes from the running backend.
# Copies the resulting file out of the container to a dated subdirectory on
# the backup target, alongside the .env files needed for disaster recovery.
# Runs integrity_check on the copy and fails hard if it's not 'ok'.
# Rotates backups older than TRADEDESK_BACKUP_KEEP_DAYS (default 30).
#
# Usage:
#   bash backup-sqlite.sh                          # use defaults
#   TRADEDESK_BACKUP_ROOT=/var/tmp/td bash ...     # override target dir (testing)
#   TRADEDESK_BACKUP_KEEP_DAYS=7 bash ...          # override rotation
#
# Intended to be invoked by cron nightly. See deployment/cron/tradedesk-backup.
#
# Exit codes:
#   0 - success (backup created, integrity check passed, rotation done)
#   1 - precondition failure (missing target, missing compose file, docker not running)
#   2 - backup command failed (sqlite3 .backup inside container returned non-zero)
#   3 - integrity_check on the copy returned something other than 'ok'
#   4 - failed to acquire lock (another backup already running)
set -euo pipefail

### Config (override via env vars) ###
# Default backup target lives on the same SSD as the app ($HOME is set by
# cron for the configured user). If you move to an external HDD later, set
# TRADEDESK_BACKUP_ROOT in the cron environment or pass it inline.
BACKUP_ROOT="${TRADEDESK_BACKUP_ROOT:-${HOME}/tradedesk-backups}"
KEEP_DAYS="${TRADEDESK_BACKUP_KEEP_DAYS:-30}"
LOCK_FILE="${TRADEDESK_BACKUP_LOCK:-/var/tmp/tradedesk-backup.lock}"

### Resolve paths ###
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
COMPOSE_FILE="${REPO_ROOT}/deployment/docker/docker-compose.prod.yml"
BACKEND_ENV="${REPO_ROOT}/backend/.env"
FRONTEND_ENV="${REPO_ROOT}/frontend/.env.production"

### Helpers ###
log()  { printf '[backup-sqlite] %s\n' "$*"; }
err()  { printf '[backup-sqlite] ERROR: %s\n' "$*" >&2; }
die()  { err "$1"; exit "${2:-1}"; }

### Single-run lock ###
exec 9>"${LOCK_FILE}"
if ! flock -n 9; then
  die "another backup is already running (lockfile: ${LOCK_FILE})" 4
fi

### Preflight ###
TIMESTAMP="$(date +%Y-%m-%d_%H%M%S)"
DATE="$(date +%Y-%m-%d)"
DEST_DIR="${BACKUP_ROOT}/${DATE}"

[[ -f "${COMPOSE_FILE}" ]] || die "compose file not found: ${COMPOSE_FILE}"
[[ -f "${BACKEND_ENV}"  ]] || die "backend .env not found: ${BACKEND_ENV}"

if ! command -v docker >/dev/null 2>&1; then
  die "docker not found in PATH"
fi

# Verify backend container is running before we try to exec into it
if ! docker compose -f "${COMPOSE_FILE}" ps --format '{{.Name}}:{{.State}}' 2>/dev/null | grep -q 'trade-desk-backend:running'; then
  die "trade-desk-backend container is not running"
fi

# Ensure backup root exists and is writable
if [[ ! -d "${BACKUP_ROOT}" ]]; then
  log "backup root ${BACKUP_ROOT} does not exist, attempting to create..."
  mkdir -p "${BACKUP_ROOT}" || die "could not create backup root: ${BACKUP_ROOT}"
fi
[[ -w "${BACKUP_ROOT}" ]] || die "backup root not writable: ${BACKUP_ROOT}"

mkdir -p "${DEST_DIR}"

### Do the backup ###
log "target: ${DEST_DIR}"
log "running sqlite3 .backup inside the backend container..."

# Use a predictable temp name inside the container. /app/data is the volume
# mount, so the backup file lives on the same volume as the source — the
# .backup command does an atomic copy.
IN_CONTAINER_TMP="/app/data/.backup-${TIMESTAMP}.db"
OUT_FILE="${DEST_DIR}/tradedesk-${TIMESTAMP}.db"

# Helper: best-effort cleanup of the in-container temp file. Used from
# several exit paths so we never leave garbage in /app/data.
cleanup_in_container_tmp() {
  docker compose -f "${COMPOSE_FILE}" exec -T backend \
    sh -c "rm -f '${IN_CONTAINER_TMP}'" 2>/dev/null || true
}

# Run the .backup inside the container. The sqlite3 CLI in the container
# comes from deployment/docker/Dockerfile.backend (installed in a separate
# layer after pip install — see commit 6e2a533).
if ! docker compose -f "${COMPOSE_FILE}" exec -T backend \
     sqlite3 /app/data/tradedesk.db ".backup '${IN_CONTAINER_TMP}'"; then
  err "sqlite3 .backup failed inside the container"
  cleanup_in_container_tmp
  exit 2
fi

### Integrity check on the in-container copy (BEFORE docker cp) ###
# We run integrity_check inside the container where we already know sqlite3
# is available. Avoids depending on a host-side sqlite3 install (which
# Raspberry Pi OS Bookworm doesn't ship by default) and avoids a second
# docker-cp round-trip.
log "running PRAGMA integrity_check on the backup (in-container)..."
INTEGRITY="$(docker compose -f "${COMPOSE_FILE}" exec -T backend \
             sqlite3 "${IN_CONTAINER_TMP}" 'PRAGMA integrity_check;' 2>/dev/null \
             | tr -d '[:space:]')"

if [[ "${INTEGRITY}" != "ok" ]]; then
  err "integrity check FAILED on in-container backup: '${INTEGRITY}'"
  cleanup_in_container_tmp
  exit 3
fi
log "integrity check: ok"

# Copy the backup out of the container volume to the dated dir
if ! docker cp "trade-desk-backend:${IN_CONTAINER_TMP}" "${OUT_FILE}"; then
  err "failed to copy backup out of container"
  cleanup_in_container_tmp
  exit 2
fi

cleanup_in_container_tmp

### Copy env files alongside ###
log "copying env files..."
cp "${BACKEND_ENV}" "${DEST_DIR}/backend.env"
chmod 600 "${DEST_DIR}/backend.env"
if [[ -f "${FRONTEND_ENV}" ]]; then
  cp "${FRONTEND_ENV}" "${DEST_DIR}/frontend.env.production"
  chmod 600 "${DEST_DIR}/frontend.env.production"
fi

### Report ###
SIZE="$(du -h "${OUT_FILE}" | cut -f1)"
log "backup complete: ${OUT_FILE} (${SIZE})"

### Rotation ###
# Delete dated directories older than KEEP_DAYS under BACKUP_ROOT.
# Uses -mindepth/-maxdepth 1 so we only touch the YYYY-MM-DD subdirectories,
# never BACKUP_ROOT itself or anything nested deeper.
log "rotating: deleting backups older than ${KEEP_DAYS} days..."
REMOVED=0
while IFS= read -r -d '' old_dir; do
  rm -rf "${old_dir}"
  REMOVED=$((REMOVED + 1))
  log "  removed: ${old_dir}"
done < <(find "${BACKUP_ROOT}" -mindepth 1 -maxdepth 1 -type d -mtime "+${KEEP_DAYS}" -print0 2>/dev/null || true)

if (( REMOVED > 0 )); then
  log "rotation removed ${REMOVED} old backup(s)"
else
  log "rotation: nothing to remove"
fi

log "done"
exit 0
