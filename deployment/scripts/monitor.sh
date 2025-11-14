#!/bin/bash
#
# TradeDesk Monitoring Script
# 
# This script monitors the health and performance of TradeDesk services
# and sends alerts if issues are detected.
#
# Usage: ./monitor.sh
# Can be run via cron: */5 * * * * /home/trade-desk/deployment/scripts/monitor.sh

set -euo pipefail

# Configuration
BASE_DIR="/home/trade-desk"
LOG_DIR="${BASE_DIR}/logs"
MONITOR_LOG="${LOG_DIR}/monitor.log"
ALERT_LOG="${LOG_DIR}/alerts.log"

# Thresholds
CPU_THRESHOLD=80
MEMORY_THRESHOLD=80
DISK_THRESHOLD=85
RESPONSE_TIME_THRESHOLD=2000  # milliseconds

# Alert settings
ALERT_EMAIL=""  # Set email for alerts
SLACK_WEBHOOK=""  # Set Slack webhook for alerts

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Functions
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" >> "$MONITOR_LOG"
}

alert() {
    local level=$1
    local message=$2
    
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] [$level] $message${NC}" | tee -a "$ALERT_LOG"
    
    # Send email alert
    if [ -n "$ALERT_EMAIL" ]; then
        echo "$message" | mail -s "TradeDesk Alert: $level" "$ALERT_EMAIL"
    fi
    
    # Send Slack alert
    if [ -n "$SLACK_WEBHOOK" ]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"TradeDesk Alert [$level]: $message\"}" \
            "$SLACK_WEBHOOK" 2>/dev/null || true
    fi
}

check_service_status() {
    local service_name=$1
    
    # Check PM2 process status
    if pm2 list | grep -q "$service_name.*online"; then
        log "$service_name is running"
        return 0
    else
        alert "ERROR" "$service_name is not running!"
        
        # Attempt to restart
        log "Attempting to restart $service_name..."
        cd "$BASE_DIR"
        pm2 restart "$service_name"
        sleep 5
        
        if pm2 list | grep -q "$service_name.*online"; then
            alert "INFO" "$service_name restarted successfully"
        else
            alert "CRITICAL" "Failed to restart $service_name"
        fi
        return 1
    fi
}

check_http_endpoint() {
    local url=$1
    local name=$2
    local expected_status=${3:-200}
    
    # Measure response time
    response=$(curl -o /dev/null -s -w "%{http_code} %{time_total}" "$url" || echo "000 0")
    status_code=$(echo "$response" | cut -d' ' -f1)
    response_time=$(echo "$response" | cut -d' ' -f2 | awk '{print int($1 * 1000)}')
    
    if [ "$status_code" = "$expected_status" ]; then
        log "$name returned status $status_code in ${response_time}ms"
        
        # Check response time
        if [ "$response_time" -gt "$RESPONSE_TIME_THRESHOLD" ]; then
            alert "WARNING" "$name response time is high: ${response_time}ms"
        fi
    else
        alert "ERROR" "$name returned status $status_code (expected $expected_status)"
    fi
}

check_system_resources() {
    # CPU Usage
    cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print int($2)}')
    if [ "$cpu_usage" -gt "$CPU_THRESHOLD" ]; then
        alert "WARNING" "High CPU usage: ${cpu_usage}%"
    fi
    
    # Memory Usage
    memory_usage=$(free | grep Mem | awk '{print int($3/$2 * 100)}')
    if [ "$memory_usage" -gt "$MEMORY_THRESHOLD" ]; then
        alert "WARNING" "High memory usage: ${memory_usage}%"
    fi
    
    # Disk Usage
    disk_usage=$(df -h / | awk 'NR==2 {print int($5)}')
    if [ "$disk_usage" -gt "$DISK_THRESHOLD" ]; then
        alert "WARNING" "High disk usage: ${disk_usage}%"
    fi
    
    log "System resources - CPU: ${cpu_usage}%, Memory: ${memory_usage}%, Disk: ${disk_usage}%"
}

check_database() {
    local db_file="${BACKEND_DIR}/trade_desk.db"
    
    if [ -f "$db_file" ]; then
        # Check database integrity
        if sqlite3 "$db_file" "PRAGMA integrity_check;" | grep -q "ok"; then
            log "Database integrity check passed"
        else
            alert "CRITICAL" "Database integrity check failed!"
        fi
        
        # Check database size
        db_size=$(du -m "$db_file" | cut -f1)
        log "Database size: ${db_size}MB"
        
        # Alert if database is getting large
        if [ "$db_size" -gt 1000 ]; then
            alert "WARNING" "Database size is large: ${db_size}MB"
        fi
    else
        alert "ERROR" "Database file not found!"
    fi
}

check_logs_for_errors() {
    # Check backend logs for errors in last 5 minutes
    if [ -f "${LOG_DIR}/backend-error.log" ]; then
        recent_errors=$(find "${LOG_DIR}/backend-error.log" -mmin -5 -exec grep -c "ERROR" {} + 2>/dev/null || echo 0)
        if [ "$recent_errors" -gt 0 ]; then
            alert "WARNING" "Found $recent_errors errors in backend logs (last 5 minutes)"
        fi
    fi
    
    # Check frontend logs for errors
    if [ -f "${LOG_DIR}/frontend-error.log" ]; then
        recent_errors=$(find "${LOG_DIR}/frontend-error.log" -mmin -5 -exec grep -c "ERROR" {} + 2>/dev/null || echo 0)
        if [ "$recent_errors" -gt 0 ]; then
            alert "WARNING" "Found $recent_errors errors in frontend logs (last 5 minutes)"
        fi
    fi
}

check_ssl_certificate() {
    # Check SSL certificate expiration
    cert_file="/etc/letsencrypt/live/piyushdev.com/cert.pem"
    
    if [ -f "$cert_file" ]; then
        expiry_date=$(openssl x509 -enddate -noout -in "$cert_file" | cut -d= -f2)
        expiry_epoch=$(date -d "$expiry_date" +%s)
        current_epoch=$(date +%s)
        days_remaining=$(( ($expiry_epoch - $current_epoch) / 86400 ))
        
        log "SSL certificate expires in $days_remaining days"
        
        if [ "$days_remaining" -lt 7 ]; then
            alert "CRITICAL" "SSL certificate expires in $days_remaining days!"
        elif [ "$days_remaining" -lt 30 ]; then
            alert "WARNING" "SSL certificate expires in $days_remaining days"
        fi
    fi
}

generate_status_report() {
    local report_file="${LOG_DIR}/status-$(date +%Y%m%d-%H%M%S).txt"
    
    {
        echo "TradeDesk Status Report"
        echo "Generated: $(date)"
        echo "========================"
        echo ""
        echo "Services:"
        pm2 list --no-color
        echo ""
        echo "System Resources:"
        echo "CPU: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}')%"
        echo "Memory: $(free -h | grep Mem | awk '{print $3 "/" $2}')"
        echo "Disk: $(df -h / | awk 'NR==2 {print $3 "/" $2 " (" $5 ")"}')"
        echo ""
        echo "Recent Alerts:"
        tail -n 20 "$ALERT_LOG" 2>/dev/null || echo "No recent alerts"
    } > "$report_file"
    
    log "Status report generated: $report_file"
}

# Main monitoring process
main() {
    log "Starting health check..."
    
    # Check services
    check_service_status "trade-desk-backend"
    check_service_status "trade-desk-frontend"
    
    # Check HTTP endpoints
    check_http_endpoint "http://localhost:8000/health" "Backend Health" 200
    check_http_endpoint "http://localhost:3001/" "Frontend" 200
    check_http_endpoint "https://piyushdev.com/health" "Public Health" 200
    
    # Check system resources
    check_system_resources
    
    # Check database
    BACKEND_DIR="${BASE_DIR}/backend"
    check_database
    
    # Check logs
    check_logs_for_errors
    
    # Check SSL certificate
    check_ssl_certificate
    
    # Generate status report every hour
    if [ "$(date +%M)" = "00" ]; then
        generate_status_report
    fi
    
    log "Health check completed"
}

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Run main function
main
