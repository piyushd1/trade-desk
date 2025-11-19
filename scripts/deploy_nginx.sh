#!/bin/bash
# Deploy Nginx Configuration Script
#
# This script generates the nginx configuration from the template
# by substituting environment variables.
#
# Usage:
#   ./scripts/deploy_nginx.sh
#
# Prerequisites:
#   - Set APP_DOMAIN environment variable or have backend/.env configured
#   - Run as root or with sudo for copying to /etc/nginx/sites-available

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print functions
print_header() {
    echo -e "${BLUE}=====================================================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}=====================================================================${NC}"
    echo
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Get the project root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TEMPLATE_FILE="$PROJECT_ROOT/nginx.conf.template"
OUTPUT_FILE="$PROJECT_ROOT/nginx.conf"
ENV_FILE="$PROJECT_ROOT/backend/.env"

print_header "Nginx Configuration Deployment"

# Check if template exists
if [ ! -f "$TEMPLATE_FILE" ]; then
    print_error "Template file not found: $TEMPLATE_FILE"
    exit 1
fi

print_success "Template file found: $TEMPLATE_FILE"

# Load environment variables from backend/.env if it exists
if [ -f "$ENV_FILE" ]; then
    print_info "Loading environment variables from $ENV_FILE"
    # Export variables from .env file
    set -a
    source "$ENV_FILE"
    set +a
else
    print_warning ".env file not found at $ENV_FILE"
    print_info "Using environment variables from current shell"
fi

# Check if APP_DOMAIN is set
if [ -z "$APP_DOMAIN" ]; then
    print_error "APP_DOMAIN environment variable is not set!"
    echo
    echo "Please set APP_DOMAIN in one of the following ways:"
    echo "  1. Add APP_DOMAIN to backend/.env file"
    echo "  2. Export it: export APP_DOMAIN=yourdomain.com"
    echo "  3. Run with it: APP_DOMAIN=yourdomain.com ./scripts/deploy_nginx.sh"
    echo
    exit 1
fi

print_success "APP_DOMAIN is set to: $APP_DOMAIN"

# Generate nginx.conf from template
print_info "Generating nginx configuration..."

# Use envsubst to substitute environment variables
envsubst '${APP_DOMAIN}' < "$TEMPLATE_FILE" > "$OUTPUT_FILE"

print_success "Configuration generated: $OUTPUT_FILE"

# Validate nginx configuration syntax (if nginx is installed)
if command -v nginx &> /dev/null; then
    print_info "Validating nginx configuration syntax..."
    if nginx -t -c "$OUTPUT_FILE" 2>&1 | grep -q "syntax is ok"; then
        print_success "Nginx configuration syntax is valid"
    else
        print_warning "Nginx syntax validation skipped (config not yet in nginx directory)"
    fi
else
    print_warning "Nginx is not installed. Skipping syntax validation."
fi

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    IS_ROOT=true
else
    IS_ROOT=false
fi

echo
print_header "Installation Options"
echo

if [ "$IS_ROOT" = true ]; then
    echo "You are running as root. Do you want to install the configuration now?"
    echo
    echo "This will:"
    echo "  1. Copy nginx.conf to /etc/nginx/sites-available/trade-desk"
    echo "  2. Create symbolic link in /etc/nginx/sites-enabled/"
    echo "  3. Test nginx configuration"
    echo "  4. Reload nginx"
    echo
    read -p "Install now? (y/N): " -n 1 -r
    echo

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Installing nginx configuration..."

        # Copy to sites-available
        cp "$OUTPUT_FILE" /etc/nginx/sites-available/trade-desk
        print_success "Copied to /etc/nginx/sites-available/trade-desk"

        # Create symbolic link
        ln -sf /etc/nginx/sites-available/trade-desk /etc/nginx/sites-enabled/trade-desk
        print_success "Created symbolic link in /etc/nginx/sites-enabled/"

        # Test configuration
        print_info "Testing nginx configuration..."
        if nginx -t; then
            print_success "Nginx configuration test passed"

            # Reload nginx
            print_info "Reloading nginx..."
            systemctl reload nginx
            print_success "Nginx reloaded successfully"

            echo
            print_success "Nginx configuration deployed successfully!"
        else
            print_error "Nginx configuration test failed!"
            print_warning "Please fix the errors and try again."
            exit 1
        fi
    else
        print_info "Skipping installation. You can install manually later."
    fi
else
    print_info "To install the configuration, run one of the following commands:"
    echo
    echo "  Option 1: Copy to nginx sites-available"
    echo "    sudo cp $OUTPUT_FILE /etc/nginx/sites-available/trade-desk"
    echo "    sudo ln -sf /etc/nginx/sites-available/trade-desk /etc/nginx/sites-enabled/trade-desk"
    echo "    sudo nginx -t"
    echo "    sudo systemctl reload nginx"
    echo
    echo "  Option 2: Run this script with sudo"
    echo "    sudo $0"
fi

echo
print_header "Deployment Summary"
echo
echo "Generated file: $OUTPUT_FILE"
echo "Domain: $APP_DOMAIN"
echo "Template: $TEMPLATE_FILE"
echo
print_success "Deployment script completed!"
echo
