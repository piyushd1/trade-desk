#!/bin/bash
# Update Zerodha Configuration Script

echo "🔐 Zerodha API Configuration Updater"
echo "===================================="
echo ""

# Prompt for API key
read -p "Enter your Zerodha API Key: " api_key
read -p "Enter your Zerodha API Secret: " api_secret

# Update .env file
cd /home/trade-desk/backend

# Create backup
cp .env .env.backup.$(date +%Y%m%d_%H%M%S)

# Update values
sed -i "s|^ZERODHA_API_KEY=.*|ZERODHA_API_KEY=$api_key|" .env
sed -i "s|^ZERODHA_API_SECRET=.*|ZERODHA_API_SECRET=$api_secret|" .env
sed -i "s|^ZERODHA_REDIRECT_URL=.*|ZERODHA_REDIRECT_URL=https://piyushdev.com/api/v1/auth/zerodha/callback|" .env

echo ""
echo "✅ Configuration updated!"
echo ""
echo "Updated values:"
grep "^ZERODHA_" .env
echo ""
echo "📝 Backup created: .env.backup.*"
echo ""
echo "🔄 Restart backend to apply changes:"
echo "   kill \$(cat /tmp/backend.pid) && sleep 2"
echo "   cd /home/trade-desk/backend && source venv/bin/activate"
echo "   nohup python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 > /tmp/backend.log 2>&1 &"
echo "   echo \$! > /tmp/backend.pid"

