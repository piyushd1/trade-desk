#!/bin/bash
#
# TradeDesk Development Setup Script
# 
# This script sets up a complete development environment for TradeDesk
#
# Usage: ./scripts/setup-dev.sh

set -euo pipefail

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration
PYTHON_VERSION="3.12"
NODE_VERSION="18"

# Functions
log() {
    echo -e "${GREEN}[SETUP]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

check_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        log "Detected Linux system"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        log "Detected macOS system"
    else
        error "Unsupported operating system: $OSTYPE"
    fi
}

install_system_deps() {
    log "Installing system dependencies..."
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo apt-get update
        sudo apt-get install -y \
            python3-pip \
            python3-venv \
            python3-dev \
            build-essential \
            redis-server \
            sqlite3 \
            curl \
            git \
            nginx
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # Check for Homebrew
        if ! command -v brew &> /dev/null; then
            error "Homebrew is required. Install from https://brew.sh"
        fi
        
        brew install \
            python@3.12 \
            redis \
            sqlite3 \
            nginx
    fi
}

setup_python() {
    log "Setting up Python environment..."
    
    cd backend
    
    # Create virtual environment
    python3 -m venv venv
    
    # Activate and upgrade pip
    source venv/bin/activate
    pip install --upgrade pip wheel setuptools
    
    # Install dependencies
    pip install -r requirements.txt
    pip install -r requirements-dev.txt
    
    log "Python environment ready"
}

setup_node() {
    log "Setting up Node.js environment..."
    
    # Check Node version
    if command -v node &> /dev/null; then
        current_version=$(node -v | sed 's/v//' | cut -d. -f1)
        if [ "$current_version" -lt "$NODE_VERSION" ]; then
            warning "Node.js version $current_version is installed, but version $NODE_VERSION+ is recommended"
        fi
    else
        error "Node.js is not installed. Please install Node.js $NODE_VERSION+"
    fi
    
    cd ../frontend
    
    # Install dependencies
    npm install
    
    log "Node.js environment ready"
}

setup_database() {
    log "Setting up database..."
    
    cd ../backend
    source venv/bin/activate
    
    # Run migrations
    alembic upgrade head
    
    # Create default user
    python scripts/create_default_user.py
    
    log "Database ready"
}

setup_env_files() {
    log "Setting up environment files..."
    
    # Backend
    if [ ! -f "backend/.env" ]; then
        cp deployment/env/backend.env.example backend/.env
        warning "Created backend/.env - Please update with your configuration"
    fi
    
    # Frontend
    if [ ! -f "frontend/.env.local" ]; then
        cat > frontend/.env.local <<EOF
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_APP_ENV=development
EOF
        log "Created frontend/.env.local"
    fi
}

setup_git_hooks() {
    log "Setting up Git hooks..."
    
    # Pre-commit hook
    cat > .git/hooks/pre-commit <<'EOF'
#!/bin/bash
# Run linting and formatting checks before commit

echo "Running pre-commit checks..."

# Backend checks
cd backend
source venv/bin/activate

# Ruff linting
echo "Running Ruff..."
ruff check .
if [ $? -ne 0 ]; then
    echo "❌ Ruff found issues. Please fix them before committing."
    exit 1
fi

# Black formatting
echo "Running Black..."
black --check .
if [ $? -ne 0 ]; then
    echo "❌ Black found formatting issues. Run 'black .' to fix."
    exit 1
fi

cd ..

# Frontend checks
cd frontend

# ESLint
echo "Running ESLint..."
npm run lint
if [ $? -ne 0 ]; then
    echo "❌ ESLint found issues. Run 'npm run lint:fix' to fix."
    exit 1
fi

# TypeScript
echo "Running TypeScript check..."
npm run type-check
if [ $? -ne 0 ]; then
    echo "❌ TypeScript found issues."
    exit 1
fi

echo "✅ All checks passed!"
EOF
    
    chmod +x .git/hooks/pre-commit
    log "Git hooks installed"
}

install_dev_tools() {
    log "Installing development tools..."
    
    # Install pre-commit
    pip install --user pre-commit
    
    # Install global tools
    npm install -g pm2
    
    log "Development tools installed"
}

print_next_steps() {
    echo ""
    echo "✅ Development environment setup complete!"
    echo ""
    echo "Next steps:"
    echo "1. Update configuration files:"
    echo "   - backend/.env"
    echo "   - frontend/.env.local"
    echo ""
    echo "2. Start the services:"
    echo "   Backend: cd backend && source venv/bin/activate && uvicorn app.main:app --reload"
    echo "   Frontend: cd frontend && npm run dev"
    echo ""
    echo "3. Access the application:"
    echo "   Frontend: http://localhost:3000"
    echo "   Backend API: http://localhost:8000/docs"
    echo ""
    echo "4. Run tests:"
    echo "   Backend: cd backend && pytest"
    echo "   Frontend: cd frontend && npm test"
}

# Main setup process
main() {
    log "Starting TradeDesk development setup..."
    
    check_os
    install_system_deps
    setup_python
    setup_node
    setup_database
    setup_env_files
    setup_git_hooks
    install_dev_tools
    
    print_next_steps
}

# Change to project root
cd "$(dirname "$0")/.."

# Run setup
main
