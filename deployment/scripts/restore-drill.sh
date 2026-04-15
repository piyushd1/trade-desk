#!/bin/bash
# restore-drill.sh — verify the most recent backup is actually restorable.
#
# Picks the most recent dated directory under TRADEDESK_BACKUP_ROOT, copies
# the .db file to a scratch location, runs PRAGMA integrity_check, and runs
# row counts on a set of critical tables. Logs the result. Fails loudly if
# anything is wrong — a passing backup file that fails this drill means we
# have NOT-RESTORABLE backups and need to know immediately.
#
# Intended to run monthly via cron. See deployment/cron/tradedesk-backup.
#
# Usage:
#   bash restore-drill.sh                          # use defaults
#   TRADEDESK_BACKUP_ROOT=/var/tmp/td bash ...     # override target dir (testing)
#
# Exit codes:
#   0 - drill passed (integrity ok, row counts look reasonable)
#   1 - precondition failure (no backups found, sqlite3 missing, etc)
#   2 - integrity check failed
#   3 - critical table missing or row count looks broken
set -euo pipefail

BACKUP_ROOT="${TRADEDESK_BACKUP_ROOT:-${HOME}/tradedesk-backups}"
SCRATCH_DIR="${TRADEDESK_DRILL_SCRATCH:-/var/tmp/tradedesk-restore-drill}"

log()  { printf '[restore-drill] %s\n' "$*"; }
err()  { printf '[restore-drill] ERROR: %s\n' "$*" >&2; }
die()  { err "$1"; exit "${2:-1}"; }

if ! command -v sqlite3 >/dev/null 2>&1; then
  err "sqlite3 is not installed on the host."
  err "Fix: sudo apt install -y sqlite3"
  err ""
  err "(The restore drill intentionally runs on the host and not inside the"
  err "backend container, so you can still verify + recover backups even if"
  err "the container is completely broken.)"
  exit 1
fi

[[ -d "${BACKUP_ROOT}" ]] || die "backup root not found: ${BACKUP_ROOT}"

# Find the most recent dated subdirectory. Sort by name lexicographically
# (works because YYYY-MM-DD sorts correctly). -maxdepth 1 -mindepth 1 so we
# only look at direct children, not nested.
LATEST_DIR="$(find "${BACKUP_ROOT}" -mindepth 1 -maxdepth 1 -type d -name '[0-9]*' \
              | sort -r | head -1)"

if [[ -z "${LATEST_DIR}" ]]; then
  die "no backup directories found under ${BACKUP_ROOT}"
fi

# Find the .db file inside the latest dir. There should be exactly one per
# backup run, but if a day had multiple runs (e.g. manual + cron), pick the
# most recent one by filename (which includes the timestamp suffix).
LATEST_DB="$(find "${LATEST_DIR}" -maxdepth 1 -type f -name 'tradedesk-*.db' \
             | sort -r | head -1)"

if [[ -z "${LATEST_DB}" ]]; then
  die "no tradedesk-*.db file found in ${LATEST_DIR}"
fi

log "latest backup: ${LATEST_DB}"
log "backup size:   $(du -h "${LATEST_DB}" | cut -f1)"
log "backup age:    $(stat --printf='%y' "${LATEST_DB}")"

### Copy to scratch ###
mkdir -p "${SCRATCH_DIR}"
SCRATCH_DB="${SCRATCH_DIR}/drill-$(date +%Y%m%d-%H%M%S).db"
cp "${LATEST_DB}" "${SCRATCH_DB}"
log "copied to scratch: ${SCRATCH_DB}"

# Ensure we clean up the scratch file on any exit path
trap 'rm -f "${SCRATCH_DB}"' EXIT

### Integrity check ###
log "running PRAGMA integrity_check..."
INTEGRITY="$(sqlite3 "${SCRATCH_DB}" 'PRAGMA integrity_check;' 2>&1 || true)"
if [[ "${INTEGRITY}" != "ok" ]]; then
  err "integrity check FAILED: ${INTEGRITY}"
  exit 2
fi
log "integrity: ok"

### Schema sanity: required tables exist ###
log "checking critical tables..."
REQUIRED_TABLES=(users broker_sessions audit_logs system_events)
# portfolio_snapshots is required once B2 lands; until then its absence is
# not a failure.
OPTIONAL_TABLES=(portfolio_snapshots)

MISSING=()
for table in "${REQUIRED_TABLES[@]}"; do
  if ! sqlite3 "${SCRATCH_DB}" \
       "SELECT name FROM sqlite_master WHERE type='table' AND name='${table}';" \
       | grep -q "^${table}$"; then
    MISSING+=("${table}")
  fi
done

if (( ${#MISSING[@]} > 0 )); then
  err "missing required tables: ${MISSING[*]}"
  exit 3
fi
log "all required tables present"

### Row counts ###
log "row counts:"
for table in "${REQUIRED_TABLES[@]}" "${OPTIONAL_TABLES[@]}"; do
  if sqlite3 "${SCRATCH_DB}" \
       "SELECT name FROM sqlite_master WHERE type='table' AND name='${table}';" \
       | grep -q "^${table}$"; then
    COUNT="$(sqlite3 "${SCRATCH_DB}" "SELECT COUNT(*) FROM ${table};" 2>/dev/null || echo '?')"
    printf '  %-24s %s\n' "${table}:" "${COUNT}"
  else
    printf '  %-24s (not in this backup)\n' "${table}:"
  fi
done

### Reasonableness check ###
# These are soft checks. If the users table has 0 rows the DB is broken
# (there's always at least the admin user seeded). The others can legitimately
# be 0 on a fresh deploy.
USER_COUNT="$(sqlite3 "${SCRATCH_DB}" 'SELECT COUNT(*) FROM users;')"
if [[ "${USER_COUNT}" == "0" ]]; then
  err "users table is empty — no admin seeded? treating as failure"
  exit 3
fi

log "drill PASSED (users=${USER_COUNT}, latest backup restorable)"
exit 0
