#!/bin/bash
#
# TradeDesk Deployment Script
# 
# This script handles the full deployment process for TradeDesk,
# including dependency installation, building, migrations, and service restarts.
#
# Usage: ./deploy.sh [environment]
# Example: ./deploy.sh production

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
BASE_DIR="/home/trade-desk"
BACKEND_DIR="${BASE_DIR}/backend"
FRONTEND_DIR="${BASE_DIR}/frontend"
LOG_DIR="${BASE_DIR}/logs"
DEPLOYMENT_LOG="${LOG_DIR}/deployment-$(date +%Y%m%d-%H%M%S).log"

# Environment (default to production)
ENVIRONMENT="${1:-production}"

# Functions
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$DEPLOYMENT_LOG"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" | tee -a "$DEPLOYMENT_LOG"
}

warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1" | tee -a "$DEPLOYMENT_LOG"
}

check_requirements() {
    log "Checking system requirements..."
    
    # Check for required commands
    for cmd in git python3 npm pm2 nginx redis-cli; do
        if ! command -v "$cmd" &> /dev/null; then
            error "$cmd is not installed!"
            exit 1
        fi
    done
    
    # Check Python version
    python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    if [[ ! "$python_version" =~ ^3\.(10|11|12) ]]; then
        error "Python 3.10+ is required (found $python_version)"
        exit 1
    fi
    
    log "All requirements satisfied"
}

backup_database() {
    log "Backing up database..."
    
    backup_dir="${BASE_DIR}/backups/$(date +%Y%m%d-%H%M%S)"
    mkdir -p "$backup_dir"
    
    # Backup SQLite database
    if [ -f "${BACKEND_DIR}/trade_desk.db" ]; then
        cp "${BACKEND_DIR}/trade_desk.db" "$backup_dir/"
        log "Database backed up to $backup_dir"
    else
        warning "No database file found to backup"
    fi
}

pull_latest_code() {
    log "Pulling latest code from repository..."
    
    cd "$BASE_DIR"
    
    # Stash any local changes
    if [[ -n $(git status -s) ]]; then
        warning "Local changes detected, stashing..."
        git stash push -m "Deployment stash $(date)"
    fi
    
    # Pull latest changes
    git pull origin master
    
    log "Code updated successfully"
}

install_backend_dependencies() {
    log "Installing backend dependencies..."
    
    cd "$BACKEND_DIR"
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install dependencies
    pip install -r requirements.txt
    
    log "Backend dependencies installed"
}

run_database_migrations() {
    log "Running database migrations..."
    
    cd "$BACKEND_DIR"
    source venv/bin/activate
    
    # Check current migration status
    alembic current
    
    # Run migrations
    alembic upgrade head
    
    log "Database migrations completed"
}

install_frontend_dependencies() {
    log "Installing frontend dependencies..."
    
    cd "$FRONTEND_DIR"
    
    # Clean install
    rm -rf node_modules package-lock.json
    npm install
    
    log "Frontend dependencies installed"
}

build_frontend() {
    log "Building frontend..."
    
    cd "$FRONTEND_DIR"
    
    # Set environment
    export NODE_ENV=production
    
    # Build Next.js application
    npm run build
    
    log "Frontend build completed"
}

update_environment_files() {
    log "Updating environment files..."
    
    # Backend .env
    if [ -f "${BACKEND_DIR}/.env.${ENVIRONMENT}" ]; then
        cp "${BACKEND_DIR}/.env.${ENVIRONMENT}" "${BACKEND_DIR}/.env"
        log "Backend environment file updated"
    else
        warning "No environment file found for ${ENVIRONMENT}"
    fi
    
    # Frontend .env
    if [ -f "${FRONTEND_DIR}/.env.${ENVIRONMENT}" ]; then
        cp "${FRONTEND_DIR}/.env.${ENVIRONMENT}" "${FRONTEND_DIR}/.env.production"
        log "Frontend environment file updated"
    fi
}

reload_services() {
    log "Reloading services..."
    
    # Copy PM2 config if needed
    if [ -f "${BASE_DIR}/deployment/ecosystem.config.js" ]; then
        cp "${BASE_DIR}/deployment/ecosystem.config.js" "${BASE_DIR}/"
    fi
    
    # Reload PM2 services
    cd "$BASE_DIR"
    pm2 reload ecosystem.config.js --update-env
    
    # Save PM2 config
    pm2 save
    
    # Test nginx config
    nginx -t
    
    # Reload nginx
    systemctl reload nginx
    
    log "Services reloaded successfully"
}

run_health_checks() {
    log "Running health checks..."
    
    sleep 5  # Wait for services to start
    
    # Check backend health
    backend_status=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health || echo "000")
    if [ "$backend_status" = "200" ]; then
        log "Backend health check passed"
    else
        error "Backend health check failed (status: $backend_status)"
    fi
    
    # Check frontend health
    frontend_status=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3001/ || echo "000")
    if [ "$frontend_status" = "200" ]; then
        log "Frontend health check passed"
    else
        error "Frontend health check failed (status: $frontend_status)"
    fi
    
    # Check public URL
    public_status=$(curl -s -o /dev/null -w "%{http_code}" https://piyushdev.com/health || echo "000")
    if [ "$public_status" = "200" ]; then
        log "Public URL health check passed"
    else
        error "Public URL health check failed (status: $public_status)"
    fi
}

cleanup() {
    log "Running cleanup tasks..."
    
    # Clean old logs (keep last 30 days)
    find "$LOG_DIR" -name "*.log" -mtime +30 -delete
    
    # Clean old backups (keep last 7 days)
    find "${BASE_DIR}/backups" -type d -mtime +7 -exec rm -rf {} + 2>/dev/null || true
    
    # Clear Next.js cache
    rm -rf "${FRONTEND_DIR}/.next/cache"
    
    log "Cleanup completed"
}

# Main deployment process
main() {
    log "Starting deployment for environment: $ENVIRONMENT"
    
    # Create log directory if it doesn't exist
    mkdir -p "$LOG_DIR"
    
    # Run deployment steps
    check_requirements
    backup_database
    pull_latest_code
    install_backend_dependencies
    run_database_migrations
    install_frontend_dependencies
    build_frontend
    update_environment_files
    reload_services
    run_health_checks
    cleanup
    
    log "Deployment completed successfully!"
    log "Deployment log saved to: $DEPLOYMENT_LOG"
}

# Run main function
main "$@"
