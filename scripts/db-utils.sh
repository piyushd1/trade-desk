#!/bin/bash
#
# TradeDesk Database Utilities
# 
# Helpful database management commands for development and maintenance
#
# Usage: ./scripts/db-utils.sh [command] [options]

set -euo pipefail

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
DB_FILE="backend/trade_desk.db"
BACKUP_DIR="backups/db"

# Functions
log() {
    echo -e "${GREEN}[DB]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Database commands
db_shell() {
    log "Opening database shell..."
    sqlite3 "$DB_FILE"
}

db_backup() {
    log "Creating database backup..."
    
    mkdir -p "$BACKUP_DIR"
    timestamp=$(date +%Y%m%d-%H%M%S)
    backup_file="$BACKUP_DIR/trade_desk_backup_$timestamp.db"
    
    sqlite3 "$DB_FILE" ".backup '$backup_file'"
    
    # Compress backup
    gzip "$backup_file"
    
    log "Backup created: ${backup_file}.gz"
}

db_restore() {
    local backup_file="$1"
    
    if [ -z "$backup_file" ]; then
        error "Please provide backup file path"
        exit 1
    fi
    
    if [ ! -f "$backup_file" ]; then
        error "Backup file not found: $backup_file"
        exit 1
    fi
    
    warning "This will overwrite the current database. Continue? (y/N)"
    read -r response
    
    if [ "$response" != "y" ]; then
        log "Restore cancelled"
        exit 0
    fi
    
    # Backup current database first
    db_backup
    
    # Decompress if needed
    if [[ "$backup_file" == *.gz ]]; then
        gunzip -c "$backup_file" > "${backup_file%.gz}"
        backup_file="${backup_file%.gz}"
    fi
    
    # Restore
    cp "$backup_file" "$DB_FILE"
    
    log "Database restored from: $backup_file"
}

db_migrate() {
    log "Running database migrations..."
    
    cd backend
    source venv/bin/activate
    
    # Show current revision
    info "Current revision:"
    alembic current
    
    # Run migrations
    alembic upgrade head
    
    # Show new revision
    info "New revision:"
    alembic current
    
    cd ..
    log "Migrations completed"
}

db_rollback() {
    local steps="${1:-1}"
    
    log "Rolling back $steps migration(s)..."
    
    cd backend
    source venv/bin/activate
    
    alembic downgrade -$steps
    
    info "Current revision:"
    alembic current
    
    cd ..
    log "Rollback completed"
}

db_reset() {
    warning "This will delete all data and recreate the database. Continue? (y/N)"
    read -r response
    
    if [ "$response" != "y" ]; then
        log "Reset cancelled"
        exit 0
    fi
    
    # Backup first
    db_backup
    
    # Delete database
    rm -f "$DB_FILE"
    
    # Run migrations
    db_migrate
    
    # Create default user
    cd backend
    source venv/bin/activate
    python scripts/create_default_user.py
    cd ..
    
    log "Database reset completed"
}

db_stats() {
    log "Database statistics:"
    echo ""
    
    # File size
    size=$(du -h "$DB_FILE" | cut -f1)
    echo "Database size: $size"
    echo ""
    
    # Table counts
    echo "Table row counts:"
    sqlite3 "$DB_FILE" <<EOF
.mode column
.headers on
SELECT 'users' as table_name, COUNT(*) as count FROM users
UNION ALL
SELECT 'broker_sessions', COUNT(*) FROM broker_sessions
UNION ALL
SELECT 'audit_logs', COUNT(*) FROM audit_logs
UNION ALL
SELECT 'system_events', COUNT(*) FROM system_events
UNION ALL
SELECT 'risk_configs', COUNT(*) FROM risk_configs
UNION ALL
SELECT 'daily_risk_metrics', COUNT(*) FROM daily_risk_metrics
UNION ALL
SELECT 'risk_breach_logs', COUNT(*) FROM risk_breach_logs;
EOF
}

db_clean() {
    log "Cleaning database..."
    
    # Vacuum to reclaim space
    sqlite3 "$DB_FILE" "VACUUM;"
    
    # Analyze for query optimization
    sqlite3 "$DB_FILE" "ANALYZE;"
    
    # Clean old audit logs (keep last 30 days for dev)
    sqlite3 "$DB_FILE" "DELETE FROM audit_logs WHERE created_at < datetime('now', '-30 days');"
    sqlite3 "$DB_FILE" "DELETE FROM system_events WHERE created_at < datetime('now', '-30 days');"
    
    log "Database cleaned"
}

db_export() {
    local format="${1:-sql}"
    local output_file="exports/trade_desk_export_$(date +%Y%m%d-%H%M%S)"
    
    mkdir -p exports
    
    case "$format" in
        sql)
            log "Exporting to SQL..."
            sqlite3 "$DB_FILE" .dump > "${output_file}.sql"
            gzip "${output_file}.sql"
            log "Exported to: ${output_file}.sql.gz"
            ;;
        csv)
            log "Exporting to CSV..."
            mkdir -p "${output_file}"
            
            # Export each table to CSV
            for table in users broker_sessions audit_logs system_events risk_configs daily_risk_metrics risk_breach_logs; do
                sqlite3 -header -csv "$DB_FILE" "SELECT * FROM $table;" > "${output_file}/${table}.csv"
            done
            
            # Compress
            tar -czf "${output_file}.tar.gz" -C exports "$(basename ${output_file})"
            rm -rf "${output_file}"
            
            log "Exported to: ${output_file}.tar.gz"
            ;;
        *)
            error "Unknown format: $format"
            echo "Supported formats: sql, csv"
            exit 1
            ;;
    esac
}

db_query() {
    local query="$1"
    
    if [ -z "$query" ]; then
        error "Please provide a SQL query"
        exit 1
    fi
    
    log "Executing query..."
    sqlite3 -header -column "$DB_FILE" "$query"
}

# Main command handler
main() {
    local command="${1:-help}"
    shift || true
    
    case "$command" in
        shell)
            db_shell
            ;;
        backup)
            db_backup
            ;;
        restore)
            db_restore "$@"
            ;;
        migrate)
            db_migrate
            ;;
        rollback)
            db_rollback "$@"
            ;;
        reset)
            db_reset
            ;;
        stats)
            db_stats
            ;;
        clean)
            db_clean
            ;;
        export)
            db_export "$@"
            ;;
        query)
            db_query "$@"
            ;;
        help)
            echo "TradeDesk Database Utilities"
            echo ""
            echo "Usage: $0 [command] [options]"
            echo ""
            echo "Commands:"
            echo "  shell              - Open SQLite shell"
            echo "  backup             - Create database backup"
            echo "  restore <file>     - Restore from backup"
            echo "  migrate            - Run pending migrations"
            echo "  rollback [steps]   - Rollback migrations (default: 1)"
            echo "  reset              - Reset database (deletes all data)"
            echo "  stats              - Show database statistics"
            echo "  clean              - Vacuum and clean database"
            echo "  export [sql|csv]   - Export database (default: sql)"
            echo "  query <sql>        - Execute SQL query"
            echo ""
            echo "Examples:"
            echo "  $0 backup"
            echo "  $0 restore backups/db/trade_desk_backup_20251112-120000.db.gz"
            echo "  $0 query \"SELECT COUNT(*) FROM users\""
            echo "  $0 export csv"
            ;;
        *)
            error "Unknown command: $command"
            echo "Run '$0 help' for usage information"
            exit 1
            ;;
    esac
}

# Change to project root
cd "$(dirname "$0")/.."

# Check if database exists
if [ ! -f "$DB_FILE" ] && [ "$1" != "migrate" ] && [ "$1" != "help" ]; then
    error "Database file not found: $DB_FILE"
    echo "Run migrations first: $0 migrate"
    exit 1
fi

# Run command
main "$@"
