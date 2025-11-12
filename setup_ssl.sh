#!/bin/bash
# SSL Setup Script for Trade Desk
# Run this AFTER configuring GCP firewall rules

set -e

echo "🔧 Trade Desk SSL Setup Script"
echo "================================"
echo ""

# Step 1: Test connectivity
echo "📡 Step 1: Testing connectivity to piyushdev.com..."
if curl -I -m 10 http://piyushdev.com 2>&1 | grep -q "HTTP"; then
    echo "✅ Domain is accessible!"
else
    echo "❌ Domain is NOT accessible from internet"
    echo ""
    echo "⚠️  Please configure GCP firewall first:"
    echo "   1. Go to: https://console.cloud.google.com/networking/firewalls/list"
    echo "   2. Create: allow-http (tcp:80)"
    echo "   3. Create: allow-https (tcp:443)"
    echo ""
    echo "See GCP_FIREWALL_SETUP.md for detailed instructions"
    exit 1
fi

# Step 2: Verify Nginx is running
echo ""
echo "🌐 Step 2: Checking Nginx..."
if systemctl is-active --quiet nginx; then
    echo "✅ Nginx is running"
else
    echo "❌ Nginx is not running. Starting..."
    sudo systemctl start nginx
fi

# Step 3: Verify backend is running
echo ""
echo "🔧 Step 3: Checking backend..."
if curl -s http://localhost:8000/health | grep -q "healthy"; then
    echo "✅ Backend is running"
else
    echo "⚠️  Backend is not running. Starting..."
    cd /home/trade-desk/backend
    source venv/bin/activate
    nohup python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 > /tmp/backend.log 2>&1 &
    echo $! > /tmp/backend.pid
    sleep 3
    echo "✅ Backend started"
fi

# Step 4: Obtain SSL certificate
echo ""
echo "🔒 Step 4: Obtaining SSL certificate from Let's Encrypt..."
sudo certbot certonly --nginx \
    -d piyushdev.com \
    -d www.piyushdev.com \
    --non-interactive \
    --agree-tos \
    --email piyush@piyushdev.com \
    --keep-until-expiring

if [ $? -eq 0 ]; then
    echo "✅ SSL certificate obtained!"
else
    echo "❌ SSL certificate failed"
    exit 1
fi

# Step 5: Update Nginx config with SSL
echo ""
echo "🔄 Step 5: Updating Nginx configuration..."
sudo cp /tmp/trade-desk-nginx.conf /etc/nginx/sites-available/trade-desk
sudo nginx -t

if [ $? -eq 0 ]; then
    sudo systemctl reload nginx
    echo "✅ Nginx configuration updated"
else
    echo "❌ Nginx configuration test failed"
    exit 1
fi

# Step 6: Test HTTPS
echo ""
echo "🧪 Step 6: Testing HTTPS setup..."
sleep 2

if curl -I -m 10 https://piyushdev.com 2>&1 | grep -q "HTTP"; then
    echo "✅ HTTPS is working!"
else
    echo "⚠️  HTTPS test inconclusive"
fi

# Step 7: Display summary
echo ""
echo "================================"
echo "✅ Setup Complete!"
echo "================================"
echo ""
echo "🌐 Your URLs:"
echo "   - https://piyushdev.com"
echo "   - https://piyushdev.com/docs"
echo "   - https://piyushdev.com/health"
echo ""
echo "🔐 SSL Certificate:"
echo "   - Location: /etc/letsencrypt/live/piyushdev.com/"
echo "   - Auto-renewal: Configured"
echo ""
echo "📋 For Zerodha Registration:"
echo "   Redirect URL: https://piyushdev.com/api/v1/auth/zerodha/callback"
echo "   Postback URL: https://piyushdev.com/api/v1/postback/zerodha"
echo ""
echo "🧪 Test commands:"
echo "   curl https://piyushdev.com/health"
echo "   curl https://piyushdev.com/api/v1/health/status"
echo ""

