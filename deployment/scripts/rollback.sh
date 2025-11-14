#!/bin/bash
#
# TradeDesk Rollback Script
# 
# This script handles rolling back to a previous deployment in case of issues.
#
# Usage: ./rollback.sh [commit-hash]
# Example: ./rollback.sh abc123def

set -euo pipefail

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
BASE_DIR="/home/trade-desk"
BACKEND_DIR="${BASE_DIR}/backend"
FRONTEND_DIR="${BASE_DIR}/frontend"
LOG_DIR="${BASE_DIR}/logs"
ROLLBACK_LOG="${LOG_DIR}/rollback-$(date +%Y%m%d-%H%M%S).log"

# Functions
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$ROLLBACK_LOG"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" | tee -a "$ROLLBACK_LOG"
}

warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1" | tee -a "$ROLLBACK_LOG"
}

get_previous_commit() {
    cd "$BASE_DIR"
    git log --format="%H %s" -n 10 | cat -n
    echo ""
    read -p "Enter the number of the commit to rollback to (or 'q' to quit): " choice
    
    if [ "$choice" = "q" ]; then
        exit 0
    fi
    
    commit_hash=$(git log --format="%H" -n 10 | sed -n "${choice}p")
    if [ -z "$commit_hash" ]; then
        error "Invalid selection"
        exit 1
    fi
    
    echo "$commit_hash"
}

backup_current_state() {
    log "Backing up current state..."
    
    backup_dir="${BASE_DIR}/backups/rollback-$(date +%Y%m%d-%H%M%S)"
    mkdir -p "$backup_dir"
    
    # Backup database
    if [ -f "${BACKEND_DIR}/trade_desk.db" ]; then
        cp "${BACKEND_DIR}/trade_desk.db" "$backup_dir/"
    fi
    
    # Save current commit hash
    cd "$BASE_DIR"
    git rev-parse HEAD > "$backup_dir/previous_commit.txt"
    
    log "Current state backed up to $backup_dir"
}

rollback_code() {
    local commit_hash=$1
    
    log "Rolling back to commit: $commit_hash"
    
    cd "$BASE_DIR"
    
    # Stash any local changes
    if [[ -n $(git status -s) ]]; then
        warning "Local changes detected, stashing..."
        git stash push -m "Rollback stash $(date)"
    fi
    
    # Rollback to specified commit
    git checkout "$commit_hash"
    
    log "Code rolled back successfully"
}

restore_dependencies() {
    log "Restoring dependencies..."
    
    # Backend dependencies
    cd "$BACKEND_DIR"
    source venv/bin/activate
    pip install -r requirements.txt
    
    # Frontend dependencies
    cd "$FRONTEND_DIR"
    rm -rf node_modules package-lock.json
    npm install
    
    log "Dependencies restored"
}

rebuild_frontend() {
    log "Rebuilding frontend..."
    
    cd "$FRONTEND_DIR"
    export NODE_ENV=production
    npm run build
    
    log "Frontend rebuilt"
}

restart_services() {
    log "Restarting services..."
    
    cd "$BASE_DIR"
    pm2 restart ecosystem.config.js
    pm2 save
    
    # Reload nginx
    systemctl reload nginx
    
    log "Services restarted"
}

verify_rollback() {
    log "Verifying rollback..."
    
    sleep 5
    
    # Check services
    backend_status=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health || echo "000")
    frontend_status=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3001/ || echo "000")
    
    if [ "$backend_status" = "200" ] && [ "$frontend_status" = "200" ]; then
        log "Rollback verified successfully"
    else
        error "Service health checks failed after rollback"
        error "Backend: $backend_status, Frontend: $frontend_status"
    fi
}

# Main rollback process
main() {
    log "Starting rollback process..."
    
    mkdir -p "$LOG_DIR"
    
    # Get commit to rollback to
    if [ $# -eq 1 ]; then
        commit_hash=$1
    else
        commit_hash=$(get_previous_commit)
    fi
    
    # Confirm rollback
    echo ""
    warning "This will rollback the application to commit: $commit_hash"
    read -p "Are you sure you want to continue? (yes/no): " confirm
    
    if [ "$confirm" != "yes" ]; then
        log "Rollback cancelled"
        exit 0
    fi
    
    # Execute rollback
    backup_current_state
    rollback_code "$commit_hash"
    restore_dependencies
    rebuild_frontend
    restart_services
    verify_rollback
    
    log "Rollback completed!"
    log "Rollback log saved to: $ROLLBACK_LOG"
}

# Run main function
main "$@"
