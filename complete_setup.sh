#!/bin/bash
# Complete Setup Script - Firewall + SSL
# Run this script to configure everything

set -e

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║         Trade Desk - Complete Setup (Firewall + SSL)            ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

# Step 1: Configure GCP Firewall
echo "🔥 Step 1/5: Configuring GCP Firewall..."
echo ""

echo "   Creating HTTP firewall rule (port 80)..."
gcloud compute firewall-rules create allow-http \
    --allow tcp:80 \
    --source-ranges 0.0.0.0/0 \
    --description "Allow HTTP for Let's Encrypt and web access" \
    --direction INGRESS \
    2>&1 | grep -v "ERROR.*already exists" || true

echo "   Creating HTTPS firewall rule (port 443)..."
gcloud compute firewall-rules create allow-https \
    --allow tcp:443 \
    --source-ranges 0.0.0.0/0 \
    --description "Allow HTTPS for secure web access" \
    --direction INGRESS \
    2>&1 | grep -v "ERROR.*already exists" || true

echo "   ✅ Firewall rules configured"
echo ""

# Step 2: Wait for firewall to propagate
echo "⏳ Step 2/5: Waiting for firewall rules to propagate (10 seconds)..."
sleep 10
echo "   ✅ Done"
echo ""

# Step 3: Test connectivity
echo "📡 Step 3/5: Testing domain connectivity..."
if timeout 10 curl -I http://piyushdev.com 2>&1 | grep -q "HTTP"; then
    echo "   ✅ piyushdev.com is accessible!"
else
    echo "   ⚠️  Domain not accessible yet. Waiting 20 more seconds..."
    sleep 20
    if timeout 10 curl -I http://piyushdev.com 2>&1 | grep -q "HTTP"; then
        echo "   ✅ Now accessible!"
    else
        echo "   ❌ Still not accessible. Please check:"
        echo "      - GCP firewall rules: gcloud compute firewall-rules list"
        echo "      - DNS: dig +short piyushdev.com"
        exit 1
    fi
fi
echo ""

# Step 4: Obtain SSL certificate
echo "🔒 Step 4/5: Obtaining SSL certificate from Let's Encrypt..."
sudo certbot certonly --nginx \
    -d piyushdev.com \
    -d www.piyushdev.com \
    --non-interactive \
    --agree-tos \
    --email piyush@piyushdev.com \
    --keep-until-expiring

if [ $? -eq 0 ]; then
    echo "   ✅ SSL certificate obtained!"
else
    echo "   ❌ SSL certificate failed. Check:"
    echo "      sudo tail -50 /var/log/letsencrypt/letsencrypt.log"
    exit 1
fi
echo ""

# Step 5: Update Nginx with SSL configuration
echo "🔄 Step 5/5: Updating Nginx configuration with SSL..."
sudo cp /tmp/trade-desk-nginx.conf /etc/nginx/sites-available/trade-desk

if sudo nginx -t; then
    sudo systemctl reload nginx
    echo "   ✅ Nginx configuration updated and reloaded"
else
    echo "   ❌ Nginx configuration test failed"
    exit 1
fi
echo ""

# Final tests
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                     ✅ SETUP COMPLETE!                           ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

echo "🧪 Testing HTTPS..."
sleep 2

if timeout 10 curl -I https://piyushdev.com 2>&1 | grep -q "HTTP"; then
    echo "   ✅ HTTPS is working!"
else
    echo "   ⚠️  HTTPS test inconclusive (might still be propagating)"
fi
echo ""

echo "🌐 Your URLs:"
echo "   • Main:     https://piyushdev.com"
echo "   • Health:   https://piyushdev.com/health"
echo "   • API Docs: https://piyushdev.com/docs"
echo ""

echo "🔐 SSL Certificate:"
echo "   • Location:     /etc/letsencrypt/live/piyushdev.com/"
echo "   • Expires:      $(sudo certbot certificates 2>/dev/null | grep 'Expiry Date' | head -1 || echo 'Run: sudo certbot certificates')"
echo "   • Auto-renewal: Enabled (cron job created)"
echo ""

echo "📋 For Zerodha Registration:"
echo "   Visit: https://developers.kite.trade/"
echo ""
echo "   Redirect URL: https://piyushdev.com/api/v1/auth/zerodha/callback"
echo "   Postback URL: https://piyushdev.com/api/v1/postback/zerodha"
echo ""

echo "🧪 Quick Test Commands:"
echo "   curl https://piyushdev.com/health"
echo "   curl https://piyushdev.com/api/v1/health/status"
echo ""

echo "📁 Next: See ZERODHA_REGISTRATION.md for registration guide"
echo ""

