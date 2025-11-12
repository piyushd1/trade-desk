# ✅ Next Steps Checklist

**What's Done:** Backend configured, Nginx configured, Scripts ready  
**Blocking Issue:** GCP Firewall  
**Time to Fix:** 2 minutes

---

## 🎯 **Your Action Items (In Order)**

### ☐ **Action 1: Configure GCP Firewall** (2 minutes)

**Go to GCP Console:**
https://console.cloud.google.com/networking/firewalls/list

**Create Two Firewall Rules:**

1. **HTTP Rule:**
   - Name: `allow-http`
   - Direction: Ingress
   - Targets: All instances
   - Source IP: `0.0.0.0/0`
   - Protocol/Port: `tcp:80`

2. **HTTPS Rule:**
   - Name: `allow-https`
   - Direction: Ingress
   - Targets: All instances
   - Source IP: `0.0.0.0/0`
   - Protocol/Port: `tcp:443`

**Detailed guide:** `GCP_FIREWALL_SETUP.md`

---

### ☐ **Action 2: Run SSL Setup** (1 minute)

After firewall is configured:

```bash
cd /home/trade-desk
./setup_ssl.sh
```

**This will:**
- Test connectivity
- Obtain SSL certificate
- Configure HTTPS
- Test everything

---

### ☐ **Action 3: Test HTTPS** (30 seconds)

```bash
# Test from your local machine or browser
curl https://piyushdev.com/health

# Visit in browser
https://piyushdev.com/docs
```

**Expected:** Should see Swagger API documentation

---

### ☐ **Action 4: Register with Zerodha** (5 minutes)

1. **Go to:** https://developers.kite.trade/
2. **Create an app** with these details:

   ```
   App Name: Trade Desk - Personal Algo Trading
   Type: Connect
   Redirect URL: https://piyushdev.com/api/v1/auth/zerodha/callback
   Postback URL: https://piyushdev.com/api/v1/postback/zerodha
   ```

3. **Copy your credentials:**
   - API Key: `xxxxxxxxxxxxx`
   - API Secret: `yyyyyyyyyyyy`

**Detailed guide:** `ZERODHA_REGISTRATION.md`

---

### ☐ **Action 5: Add Zerodha Credentials** (1 minute)

**Option A: Use the helper script**
```bash
cd /home/trade-desk
./update_zerodha_config.sh
```

**Option B: Manual edit**
```bash
nano /home/trade-desk/backend/.env

# Update these lines:
ZERODHA_API_KEY=your_api_key
ZERODHA_API_SECRET=your_api_secret
```

---

### ☐ **Action 6: Restart Backend** (30 seconds)

```bash
# Stop current backend
kill $(cat /tmp/backend.pid)

# Start with new config
cd /home/trade-desk/backend
source venv/bin/activate
nohup python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 > /tmp/backend.log 2>&1 &
echo $! > /tmp/backend.pid

# Verify
curl http://localhost:8000/health
```

---

### ☐ **Action 7: Notify Me to Continue** (Let me know!)

Once you've completed Actions 1-6, let me know and I'll:
- ✅ Implement the complete OAuth flow
- ✅ Test order placement (paper mode)
- ✅ Add risk management controls
- ✅ Create example strategies

---

## 📁 **Files Created for You**

| File | Purpose |
|------|---------|
| `GCP_FIREWALL_SETUP.md` | How to configure GCP firewall |
| `SETUP_INSTRUCTIONS.md` | Complete setup guide |
| `ZERODHA_REGISTRATION.md` | Zerodha registration guide |
| `setup_ssl.sh` | Automated SSL setup script |
| `update_zerodha_config.sh` | Update Zerodha credentials |
| `CURRENT_STATUS.md` | Current status |
| `NEXT_STEPS_CHECKLIST.md` | This file |

---

## 🧪 **Testing After Each Step**

### After Action 1 (Firewall):
```bash
curl http://piyushdev.com
# Should connect (not timeout)
```

### After Action 2 (SSL):
```bash
curl https://piyushdev.com/health
# Should return JSON
```

### After Action 4-6 (Zerodha):
```bash
# Test OAuth initiation endpoint
curl https://piyushdev.com/api/v1/auth/zerodha/connect

# Should return login URL
```

---

## ⏱️ **Estimated Time:**

- Action 1 (GCP Firewall): **2 minutes**
- Action 2 (SSL Setup): **1 minute** (automated)
- Action 3 (Test HTTPS): **30 seconds**
- Action 4 (Zerodha Registration): **5 minutes**
- Action 5 (Add Credentials): **1 minute**
- Action 6 (Restart Backend): **30 seconds**

**Total: ~10 minutes**

---

## 🎯 **Success Criteria**

Before notifying me to continue, verify:

- [ ] `curl https://piyushdev.com/health` returns 200 OK
- [ ] Browser can access https://piyushdev.com/docs
- [ ] Zerodha app created successfully
- [ ] API credentials added to .env file
- [ ] Backend restarted with new config

---

## 🆘 **If You Get Stuck**

### Check Backend Logs:
```bash
tail -50 /tmp/backend.log
```

### Check Nginx Logs:
```bash
sudo tail -50 /var/log/nginx/trade-desk-error.log
```

### Test Connectivity:
```bash
# From your local machine
curl -v http://piyushdev.com

# Check firewall status
gcloud compute firewall-rules list
```

---

**Start with Action 1 (GCP Firewall)!** 🚀
