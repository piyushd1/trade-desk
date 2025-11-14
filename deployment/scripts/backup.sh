#!/bin/bash
#
# TradeDesk Backup Script
# 
# This script performs automated backups of the TradeDesk application,
# including database, configuration files, and logs.
#
# Usage: ./backup.sh [full|database|config]
# Example: ./backup.sh full

set -euo pipefail

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
BASE_DIR="/home/trade-desk"
BACKUP_ROOT="/home/trade-desk/backups"
BACKUP_TYPE="${1:-full}"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_DIR="${BACKUP_ROOT}/${BACKUP_TYPE}-${TIMESTAMP}"

# S3 Configuration (optional)
USE_S3_BACKUP=false
S3_BUCKET="s3://trade-desk-backups"

# Functions
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

create_backup_directory() {
    log "Creating backup directory: $BACKUP_DIR"
    mkdir -p "$BACKUP_DIR"
}

backup_database() {
    log "Backing up database..."
    
    local db_file="${BASE_DIR}/backend/trade_desk.db"
    
    if [ -f "$db_file" ]; then
        # Create database backup with integrity check
        sqlite3 "$db_file" ".backup '${BACKUP_DIR}/trade_desk.db'"
        
        # Also create SQL dump for portability
        sqlite3 "$db_file" .dump > "${BACKUP_DIR}/trade_desk.sql"
        
        # Compress the SQL dump
        gzip "${BACKUP_DIR}/trade_desk.sql"
        
        log "Database backup completed"
    else
        warning "No database file found"
    fi
}

backup_configuration() {
    log "Backing up configuration files..."
    
    # Create config backup directory
    mkdir -p "${BACKUP_DIR}/config"
    
    # Backend configuration
    if [ -f "${BASE_DIR}/backend/.env" ]; then
        cp "${BASE_DIR}/backend/.env" "${BACKUP_DIR}/config/backend.env"
    fi
    
    # Frontend configuration
    if [ -f "${BASE_DIR}/frontend/.env.production" ]; then
        cp "${BASE_DIR}/frontend/.env.production" "${BACKUP_DIR}/config/frontend.env"
    fi
    
    # Nginx configuration
    if [ -f "/etc/nginx/sites-available/trade-desk" ]; then
        cp "/etc/nginx/sites-available/trade-desk" "${BACKUP_DIR}/config/nginx.conf"
    fi
    
    # PM2 configuration
    if [ -f "${BASE_DIR}/ecosystem.config.js" ]; then
        cp "${BASE_DIR}/ecosystem.config.js" "${BACKUP_DIR}/config/"
    fi
    
    # Systemd service files (if any)
    if [ -d "/etc/systemd/system/" ]; then
        find /etc/systemd/system/ -name "trade-desk*" -exec cp {} "${BACKUP_DIR}/config/" \; 2>/dev/null || true
    fi
    
    log "Configuration backup completed"
}

backup_logs() {
    log "Backing up logs..."
    
    # Create logs backup directory
    mkdir -p "${BACKUP_DIR}/logs"
    
    # Application logs
    if [ -d "${BASE_DIR}/logs" ]; then
        # Copy recent logs (last 7 days)
        find "${BASE_DIR}/logs" -name "*.log" -mtime -7 -exec cp {} "${BACKUP_DIR}/logs/" \; 2>/dev/null || true
    fi
    
    # Nginx logs
    if [ -d "/var/log/nginx" ]; then
        cp /var/log/nginx/trade-desk-*.log "${BACKUP_DIR}/logs/" 2>/dev/null || true
    fi
    
    log "Logs backup completed"
}

backup_secrets() {
    log "Backing up encrypted secrets..."
    
    # Create secrets backup directory
    mkdir -p "${BACKUP_DIR}/secrets"
    
    # Backup secrets directory (should already be encrypted)
    if [ -d "${BASE_DIR}/secrets" ]; then
        cp -r "${BASE_DIR}/secrets/"* "${BACKUP_DIR}/secrets/" 2>/dev/null || true
    fi
    
    warning "Remember: Secrets are backed up in their encrypted form"
    
    log "Secrets backup completed"
}

create_backup_manifest() {
    log "Creating backup manifest..."
    
    cat > "${BACKUP_DIR}/manifest.json" <<EOF
{
    "timestamp": "${TIMESTAMP}",
    "type": "${BACKUP_TYPE}",
    "hostname": "$(hostname)",
    "git_commit": "$(cd $BASE_DIR && git rev-parse HEAD 2>/dev/null || echo 'unknown')",
    "git_branch": "$(cd $BASE_DIR && git branch --show-current 2>/dev/null || echo 'unknown')",
    "database_size": "$(du -h ${BACKUP_DIR}/trade_desk.db 2>/dev/null | cut -f1 || echo 'N/A')",
    "total_size": "$(du -sh ${BACKUP_DIR} | cut -f1)",
    "created_by": "$(whoami)",
    "backup_version": "1.0"
}
EOF
    
    log "Backup manifest created"
}

compress_backup() {
    log "Compressing backup..."
    
    cd "${BACKUP_ROOT}"
    tar -czf "${BACKUP_TYPE}-${TIMESTAMP}.tar.gz" "${BACKUP_TYPE}-${TIMESTAMP}/"
    
    # Remove uncompressed directory
    rm -rf "${BACKUP_DIR}"
    
    BACKUP_FILE="${BACKUP_ROOT}/${BACKUP_TYPE}-${TIMESTAMP}.tar.gz"
    log "Backup compressed: $BACKUP_FILE ($(du -h $BACKUP_FILE | cut -f1))"
}

upload_to_s3() {
    if [ "$USE_S3_BACKUP" = true ]; then
        log "Uploading backup to S3..."
        
        if command -v aws &> /dev/null; then
            aws s3 cp "$BACKUP_FILE" "${S3_BUCKET}/" --storage-class STANDARD_IA
            log "Backup uploaded to S3"
        else
            warning "AWS CLI not installed, skipping S3 upload"
        fi
    fi
}

cleanup_old_backups() {
    log "Cleaning up old backups..."
    
    # Keep only last 7 days of local backups
    find "$BACKUP_ROOT" -name "*.tar.gz" -mtime +7 -delete
    
    # Clean up old S3 backups (keep 30 days)
    if [ "$USE_S3_BACKUP" = true ] && command -v aws &> /dev/null; then
        # This would need a lifecycle policy on the S3 bucket
        log "S3 cleanup managed by lifecycle policy"
    fi
    
    log "Cleanup completed"
}

# Main backup process
main() {
    log "Starting ${BACKUP_TYPE} backup..."
    
    create_backup_directory
    
    case "$BACKUP_TYPE" in
        full)
            backup_database
            backup_configuration
            backup_logs
            backup_secrets
            ;;
        database)
            backup_database
            ;;
        config)
            backup_configuration
            ;;
        logs)
            backup_logs
            ;;
        *)
            warning "Unknown backup type: $BACKUP_TYPE"
            echo "Usage: $0 [full|database|config|logs]"
            exit 1
            ;;
    esac
    
    create_backup_manifest
    compress_backup
    upload_to_s3
    cleanup_old_backups
    
    log "Backup completed successfully!"
    log "Backup location: $BACKUP_FILE"
}

# Run main function
main
