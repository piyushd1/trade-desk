# TradeDesk Makefile
# 
# Common development and deployment commands
# Run 'make help' to see all available commands

.PHONY: help setup dev test deploy clean

# Default target
.DEFAULT_GOAL := help

# Colors
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m

## help: Show this help message
help:
	@echo "TradeDesk Development Commands"
	@echo "============================="
	@echo ""
	@awk 'BEGIN {FS = ":.*##"; printf "Usage: make [target]\n\n"} \
		/^[a-zA-Z0-9_-]+:.*?##/ { printf "  ${GREEN}%-15s${NC} %s\n", $$1, $$2 } \
		/^##@/ { printf "\n${YELLOW}%s${NC}\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Setup Commands

## setup: Complete development environment setup
setup:
	@echo "${GREEN}Setting up development environment...${NC}"
	./scripts/setup-dev.sh

## install: Install dependencies
install: install-backend install-frontend

## install-backend: Install backend dependencies
install-backend:
	@echo "${GREEN}Installing backend dependencies...${NC}"
	cd backend && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt

## install-frontend: Install frontend dependencies
install-frontend:
	@echo "${GREEN}Installing frontend dependencies...${NC}"
	cd frontend && npm install

##@ Development Commands

## dev: Start development servers
dev:
	@echo "${GREEN}Starting development servers...${NC}"
	./scripts/dev-server.sh start

## dev-stop: Stop development servers
dev-stop:
	@echo "${GREEN}Stopping development servers...${NC}"
	./scripts/dev-server.sh stop

## dev-restart: Restart development servers
dev-restart:
	@echo "${GREEN}Restarting development servers...${NC}"
	./scripts/dev-server.sh restart

## dev-status: Show development server status
dev-status:
	./scripts/dev-server.sh status

## logs: Show development logs
logs:
	./scripts/dev-server.sh logs

##@ Database Commands

## db-shell: Open database shell
db-shell:
	./scripts/db-utils.sh shell

## db-migrate: Run database migrations
db-migrate:
	./scripts/db-utils.sh migrate

## db-backup: Create database backup
db-backup:
	./scripts/db-utils.sh backup

## db-reset: Reset database (WARNING: deletes all data)
db-reset:
	./scripts/db-utils.sh reset

## db-stats: Show database statistics
db-stats:
	./scripts/db-utils.sh stats

##@ Testing Commands

## test: Run all tests
test:
	@echo "${GREEN}Running all tests...${NC}"
	./scripts/test-all.sh all

## test-backend: Run backend tests
test-backend:
	./scripts/test-all.sh backend

## test-frontend: Run frontend tests
test-frontend:
	./scripts/test-all.sh frontend

## test-integration: Run integration tests
test-integration:
	./scripts/test-all.sh integration

## lint: Run linting checks
lint: lint-backend lint-frontend

## lint-backend: Lint backend code
lint-backend:
	@echo "${GREEN}Linting backend...${NC}"
	cd backend && source venv/bin/activate && ruff check . && black --check .

## lint-frontend: Lint frontend code
lint-frontend:
	@echo "${GREEN}Linting frontend...${NC}"
	cd frontend && npm run lint

## format: Auto-format code
format: format-backend format-frontend

## format-backend: Format backend code
format-backend:
	@echo "${GREEN}Formatting backend...${NC}"
	cd backend && source venv/bin/activate && ruff check --fix . && black .

## format-frontend: Format frontend code
format-frontend:
	@echo "${GREEN}Formatting frontend...${NC}"
	cd frontend && npm run format

##@ Build Commands

## build: Build production assets
build: build-frontend

## build-frontend: Build frontend for production
build-frontend:
	@echo "${GREEN}Building frontend...${NC}"
	cd frontend && npm run build

##@ Deployment Commands

## deploy: Deploy to production
deploy:
	@echo "${GREEN}Deploying to production...${NC}"
	./deployment/scripts/deploy.sh production

## deploy-staging: Deploy to staging
deploy-staging:
	@echo "${GREEN}Deploying to staging...${NC}"
	./deployment/scripts/deploy.sh staging

## backup: Create full backup
backup:
	@echo "${GREEN}Creating backup...${NC}"
	./deployment/scripts/backup.sh full

## monitor: Run monitoring checks
monitor:
	./deployment/scripts/monitor.sh

##@ Utility Commands

## clean: Clean build artifacts and caches
clean:
	@echo "${GREEN}Cleaning build artifacts...${NC}"
	rm -rf frontend/.next
	rm -rf frontend/node_modules
	rm -rf backend/__pycache__
	rm -rf backend/venv
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name ".DS_Store" -delete

## pm2-start: Start services with PM2
pm2-start:
	pm2 start ecosystem.config.js

## pm2-stop: Stop PM2 services
pm2-stop:
	pm2 stop all

## pm2-restart: Restart PM2 services
pm2-restart:
	pm2 restart all

## pm2-logs: Show PM2 logs
pm2-logs:
	pm2 logs

## pm2-status: Show PM2 status
pm2-status:
	pm2 status

## docker-build: Build Docker images
docker-build:
	@echo "${GREEN}Building Docker images...${NC}"
	cd deployment/docker && docker-compose build

## docker-up: Start Docker containers
docker-up:
	@echo "${GREEN}Starting Docker containers...${NC}"
	cd deployment/docker && docker-compose up -d

## docker-down: Stop Docker containers
docker-down:
	@echo "${GREEN}Stopping Docker containers...${NC}"
	cd deployment/docker && docker-compose down

## docker-logs: Show Docker logs
docker-logs:
	cd deployment/docker && docker-compose logs -f

##@ Git Commands

## git-status: Show git status
git-status:
	git status

## git-commit: Commit changes
git-commit:
	git add -A && git commit

## git-push: Push to remote
git-push:
	git push origin master
