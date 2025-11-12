#!/bin/bash
# Configure GCP Firewall Rules for Trade Desk

set -e

echo "🔥 Configuring GCP Firewall Rules..."
echo "===================================="
echo ""

# Check if running in GCP environment
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud command not found"
    echo ""
    echo "Run this in GCP Cloud Shell instead:"
    echo "https://console.cloud.google.com/?cloudshell=true"
    exit 1
fi

echo "📡 Creating HTTP firewall rule (port 80)..."
gcloud compute firewall-rules create allow-http \
    --allow tcp:80 \
    --source-ranges 0.0.0.0/0 \
    --description "Allow HTTP for Let's Encrypt and web access" \
    --direction INGRESS \
    || echo "⚠️  Rule may already exist (this is OK)"

echo ""
echo "🔒 Creating HTTPS firewall rule (port 443)..."
gcloud compute firewall-rules create allow-https \
    --allow tcp:443 \
    --source-ranges 0.0.0.0/0 \
    --description "Allow HTTPS for secure web access" \
    --direction INGRESS \
    || echo "⚠️  Rule may already exist (this is OK)"

echo ""
echo "✅ Firewall rules configured!"
echo ""
echo "📋 Verifying rules..."
gcloud compute firewall-rules list --filter="name:(allow-http OR allow-https)" \
    --format="table(name,allowed,sourceRanges,direction)"

echo ""
echo "🧪 Testing connectivity..."
sleep 5
if curl -I -m 10 http://piyushdev.com 2>&1 | grep -q "HTTP"; then
    echo "✅ Domain is now accessible!"
else
    echo "⏳ Still propagating... wait 30 seconds and test:"
    echo "   curl http://piyushdev.com"
fi

echo ""
echo "🎉 Firewall configuration complete!"
echo ""
echo "Next step: Run SSL setup"
echo "   cd /home/trade-desk"
echo "   ./setup_ssl.sh"

