# 🔐 Zerodha Kite Connect Registration Guide

**Official Documentation**: https://kite.trade/docs/connect/v3/

---

## 📋 **Prerequisites**

Before registering, ensure:
- ✅ You have an **active Zerodha trading account**
- ✅ **2FA TOTP is enabled** in your Zerodha account settings
- ✅ Your domain is accessible via HTTPS (run `./setup_ssl.sh` first)
- ✅ Backend is running on your server

---

## 🎯 **Registration Steps**

### **Step 1: Create Developer Account**

1. Visit: **https://developers.kite.trade/**
2. Click **"Sign up"** or **"Login"** (use your Zerodha credentials)
3. Complete the developer account setup

### **Step 2: Create Your App**

1. After login, click **"Create new app"**

2. **Fill in the details:**

   ```
   App Name: Trade Desk - Personal Algo Trading
   
   Description: 
   Personal algorithmic trading platform with SEBI compliance for 
   systematic equity trading on NSE/BSE. For personal and family use only.
   
   Type: Connect
   
   Redirect URL: https://piyushdev.com/api/v1/auth/zerodha/callback
   
   Postback URL: https://piyushdev.com/api/v1/postback/zerodha
   ```

3. Click **"Create"**

### **Step 3: Get Your Credentials**

After app creation, you'll see:

```
API Key: xxxxxxxxxxxxx
API Secret: yyyyyyyyyyyy
```

**⚠️ Important:**
- Copy both immediately
- **Never share your API Secret**
- **Never commit to git**
- Store securely

### **Step 4: Configure Your Application**

Run the configuration script:

```bash
cd /home/trade-desk
./update_zerodha_config.sh
```

Or manually edit `/home/trade-desk/backend/.env`:

```bash
nano /home/trade-desk/backend/.env

# Update these lines:
ZERODHA_API_KEY=your_actual_api_key_here
ZERODHA_API_SECRET=your_actual_api_secret_here
ZERODHA_REDIRECT_URL=https://piyushdev.com/api/v1/auth/zerodha/callback
```

### **Step 5: Restart Backend**

```bash
# Kill current process
kill $(cat /tmp/backend.pid)

# Start with new configuration
cd /home/trade-desk/backend
source venv/bin/activate
nohup python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 > /tmp/backend.log 2>&1 &
echo $! > /tmp/backend.pid

# Verify it's running
sleep 3
curl http://localhost:8000/health
```

---

## 🧪 **Test Your Setup**

### **Test 1: Generate Login URL**

The login URL format (from Kite Connect docs):
```
https://kite.zerodha.com/connect/login?v=3&api_key=YOUR_API_KEY
```

Replace `YOUR_API_KEY` with your actual API key.

### **Test 2: Manual OAuth Flow**

1. **Visit the login URL** in your browser
2. **Login with your Zerodha credentials**
3. **Authorize the app**
4. **You'll be redirected to:**
   ```
   https://piyushdev.com/api/v1/auth/zerodha/callback?request_token=xxxxx&action=login&status=success
   ```

5. **The request_token** in the URL is what you'll exchange for an access token

### **Test 3: Check Logs**

```bash
# Check if callback was received
tail -f /tmp/backend.log | grep -i zerodha
```

---

## 📊 **Understanding the OAuth Flow**

From the Kite Connect documentation:

```
1. User clicks "Connect Zerodha"
   ↓
2. User redirected to Kite login page
   https://kite.zerodha.com/connect/login?v=3&api_key=xxx
   ↓
3. User logs in with Zerodha credentials
   ↓
4. User authorizes your app
   ↓
5. Zerodha redirects back to your callback URL
   https://piyushdev.com/api/v1/auth/zerodha/callback?request_token=yyy
   ↓
6. Your backend exchanges request_token for access_token
   POST to Kite API with: api_key + request_token + api_secret
   ↓
7. Receive access_token (valid until 6 AM next day)
   ↓
8. Store access_token (encrypted) in database
   ↓
9. Use access_token for all subsequent API calls
```

---

## ⚙️ **Configuration in Your Backend**

The OAuth implementation will be in:

```python
# app/api/v1/auth.py

@router.get("/brokers/zerodha/connect")
async def zerodha_oauth_initiate():
    # Generate login URL
    kite = KiteConnect(api_key=settings.ZERODHA_API_KEY)
    login_url = kite.login_url()
    
    return {
        "login_url": login_url,
        "message": "Redirect user to this URL"
    }

@router.get("/brokers/zerodha/callback")
async def zerodha_oauth_callback(request_token: str, status: str):
    # Exchange request_token for access_token
    kite = KiteConnect(api_key=settings.ZERODHA_API_KEY)
    data = kite.generate_session(request_token, api_secret=settings.ZERODHA_API_SECRET)
    
    access_token = data["access_token"]
    
    # Store encrypted in database
    # ... (we'll implement this)
    
    return {"status": "success", "message": "Connected to Zerodha"}
```

---

## 🔒 **Security Requirements (SEBI Compliant)**

According to Kite Connect docs and SEBI requirements:

✅ **OAuth 2.0 Only:**
- Must use OAuth flow (no password storage)
- Access tokens must be stored encrypted

✅ **2FA Required:**
- Enable TOTP in your Zerodha account settings
- Go to: Kite → Settings → Security → Enable TOTP

✅ **Static IP Whitelisting:**
- Your static IP: `34.180.15.147`
- Whitelist this in Zerodha API settings

✅ **Order Tagging:**
- All algo orders must have a `tag` parameter
- Format: `algo_<strategy_id>_<unique_id>`

---

## 📞 **Zerodha Support**

If you face issues:
- **Developer Forum**: https://kite.trade/forum/
- **Email**: kitesupport@zerodha.com
- **Documentation**: https://kite.trade/docs/connect/v3/

---

## ✅ **Checklist Before Registration**

- [ ] HTTPS working on piyushdev.com
- [ ] Backend running and accessible via domain
- [ ] 2FA enabled on your Zerodha account
- [ ] You have your trading account credentials
- [ ] You understand the OAuth flow

---

**Once you have your API keys, we'll implement and test the complete OAuth flow!**

