#!/bin/bash
#
# TradeDesk Development Server Manager
# 
# Manages backend and frontend development servers with hot reloading
#
# Usage: ./scripts/dev-server.sh [start|stop|restart|status|logs]

set -euo pipefail

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
BACKEND_PORT=8000
FRONTEND_PORT=3000
BACKEND_PID_FILE="/tmp/trade-desk-backend.pid"
FRONTEND_PID_FILE="/tmp/trade-desk-frontend.pid"
LOG_DIR="logs/dev"

# Functions
log() {
    echo -e "${GREEN}[DEV]${NC} $1"
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

check_port() {
    local port=$1
    if lsof -i:$port > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

start_backend() {
    log "Starting backend server..."
    
    if [ -f "$BACKEND_PID_FILE" ] && kill -0 $(cat "$BACKEND_PID_FILE") 2>/dev/null; then
        warning "Backend is already running (PID: $(cat $BACKEND_PID_FILE))"
        return 0
    fi
    
    cd backend
    source venv/bin/activate
    
    # Create log directory
    mkdir -p "../$LOG_DIR"
    
    # Start with hot reload
    APP_ENV=development uvicorn app.main:app \
        --host 127.0.0.1 \
        --port $BACKEND_PORT \
        --reload \
        --reload-dir app \
        > "../$LOG_DIR/backend.log" 2>&1 &
    
    echo $! > "$BACKEND_PID_FILE"
    
    # Wait for startup
    sleep 3
    
    if check_port $BACKEND_PORT; then
        log "Backend started on port $BACKEND_PORT (PID: $(cat $BACKEND_PID_FILE))"
    else
        error "Backend failed to start"
        rm -f "$BACKEND_PID_FILE"
        return 1
    fi
    
    cd ..
}

start_frontend() {
    log "Starting frontend server..."
    
    if [ -f "$FRONTEND_PID_FILE" ] && kill -0 $(cat "$FRONTEND_PID_FILE") 2>/dev/null; then
        warning "Frontend is already running (PID: $(cat $FRONTEND_PID_FILE))"
        return 0
    fi
    
    cd frontend
    
    # Create log directory
    mkdir -p "../$LOG_DIR"
    
    # Start Next.js dev server
    npm run dev > "../$LOG_DIR/frontend.log" 2>&1 &
    
    echo $! > "$FRONTEND_PID_FILE"
    
    # Wait for startup
    sleep 5
    
    if check_port $FRONTEND_PORT; then
        log "Frontend started on port $FRONTEND_PORT (PID: $(cat $FRONTEND_PID_FILE))"
    else
        error "Frontend failed to start"
        rm -f "$FRONTEND_PID_FILE"
        return 1
    fi
    
    cd ..
}

stop_backend() {
    log "Stopping backend server..."
    
    if [ -f "$BACKEND_PID_FILE" ]; then
        PID=$(cat "$BACKEND_PID_FILE")
        if kill -0 $PID 2>/dev/null; then
            kill $PID
            sleep 2
            if kill -0 $PID 2>/dev/null; then
                kill -9 $PID
            fi
            log "Backend stopped"
        else
            warning "Backend process not found"
        fi
        rm -f "$BACKEND_PID_FILE"
    else
        warning "Backend PID file not found"
    fi
}

stop_frontend() {
    log "Stopping frontend server..."
    
    if [ -f "$FRONTEND_PID_FILE" ]; then
        PID=$(cat "$FRONTEND_PID_FILE")
        if kill -0 $PID 2>/dev/null; then
            kill $PID
            sleep 2
            if kill -0 $PID 2>/dev/null; then
                kill -9 $PID
            fi
            log "Frontend stopped"
        else
            warning "Frontend process not found"
        fi
        rm -f "$FRONTEND_PID_FILE"
    else
        warning "Frontend PID file not found"
    fi
}

show_status() {
    echo -e "\n${BLUE}TradeDesk Development Servers Status${NC}"
    echo "======================================"
    
    # Backend status
    if [ -f "$BACKEND_PID_FILE" ] && kill -0 $(cat "$BACKEND_PID_FILE") 2>/dev/null; then
        echo -e "Backend:  ${GREEN}✓ Running${NC} (PID: $(cat $BACKEND_PID_FILE), Port: $BACKEND_PORT)"
    else
        echo -e "Backend:  ${RED}✗ Stopped${NC}"
    fi
    
    # Frontend status
    if [ -f "$FRONTEND_PID_FILE" ] && kill -0 $(cat "$FRONTEND_PID_FILE") 2>/dev/null; then
        echo -e "Frontend: ${GREEN}✓ Running${NC} (PID: $(cat $FRONTEND_PID_FILE), Port: $FRONTEND_PORT)"
    else
        echo -e "Frontend: ${RED}✗ Stopped${NC}"
    fi
    
    echo ""
    
    # URLs
    if check_port $BACKEND_PORT; then
        echo "Backend API: http://localhost:$BACKEND_PORT/docs"
    fi
    
    if check_port $FRONTEND_PORT; then
        echo "Frontend: http://localhost:$FRONTEND_PORT"
    fi
    
    echo ""
}

show_logs() {
    local service="${1:-all}"
    
    case "$service" in
        backend)
            log "Backend logs:"
            tail -f "$LOG_DIR/backend.log"
            ;;
        frontend)
            log "Frontend logs:"
            tail -f "$LOG_DIR/frontend.log"
            ;;
        all)
            # Use multitail if available
            if command -v multitail &> /dev/null; then
                multitail "$LOG_DIR/backend.log" "$LOG_DIR/frontend.log"
            else
                warning "multitail not found, showing backend logs only"
                tail -f "$LOG_DIR/backend.log"
            fi
            ;;
    esac
}

# Main command handler
main() {
    local command="${1:-help}"
    
    case "$command" in
        start)
            start_backend
            start_frontend
            show_status
            ;;
        stop)
            stop_backend
            stop_frontend
            log "All services stopped"
            ;;
        restart)
            stop_backend
            stop_frontend
            sleep 2
            start_backend
            start_frontend
            show_status
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs "${2:-all}"
            ;;
        help)
            echo "TradeDesk Development Server Manager"
            echo ""
            echo "Usage: $0 [command] [options]"
            echo ""
            echo "Commands:"
            echo "  start    - Start both backend and frontend servers"
            echo "  stop     - Stop all servers"
            echo "  restart  - Restart all servers"
            echo "  status   - Show server status"
            echo "  logs     - Show logs (backend|frontend|all)"
            echo ""
            echo "Examples:"
            echo "  $0 start"
            echo "  $0 logs backend"
            echo "  $0 status"
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

# Run command
main "$@"
