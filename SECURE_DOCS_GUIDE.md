# Secure Documentation Implementation Guide

**Date:** January 31, 2025  
**Task:** Secure `/docs` and disable `/redoc`

---

## ✅ Changes Made

### 1. Backend Changes (Already Applied)
- ✅ Disabled `/redoc` in FastAPI app
- ✅ Kept `/docs` enabled (will be secured by Nginx)
- ✅ Backend needs restart

### 2. Nginx Changes (You Need to Apply)
- 🔒 Add HTTP Basic Auth to `/docs` and `/openapi.json`
- ❌ Block `/redoc` completely (return 404)
- 📝 Create password file for docs access

---

## 🚀 Step-by-Step Implementation

### Step 1: Restart Backend (2 minutes)

```bash
cd /home/trade-desk/backend
kill $(cat /tmp/backend.pid)
source venv/bin/activate
nohup python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 > /tmp/backend.log 2>&1 &
echo $! > /tmp/backend.pid
echo "✅ Backend restarted"
```

**Verify:**
```bash
curl -s http://localhost:8000/health | python3 -m json.tool
# Should show: {"status": "healthy", ...}
```

---

### Step 2: Create Password File for Docs (1 minute)

**Create a password for accessing `/docs`:**

```bash
# Install htpasswd if not already installed
sudo apt-get update && sudo apt-get install -y apache2-utils

# Create password file (will prompt for password)
sudo htpasswd -c /etc/nginx/.htpasswd_docs piyushdev
```

**When prompted:**
- Enter your desired password (e.g., `TradeDesk@2025`)
- Re-enter to confirm

**⚠️ Important:** Remember this password! You'll need it to access `/docs`.

**Verify file created:**
```bash
sudo cat /etc/nginx/.htpasswd_docs
# Should show: piyushdev:$apr1$...
```

---

### Step 3: Backup Current Nginx Config (1 minute)

**Always backup before changes:**

```bash
sudo cp /etc/nginx/sites-available/trade-desk /etc/nginx/sites-available/trade-desk.backup-$(date +%Y%m%d-%H%M%S)
echo "✅ Backup created"
```

**List backups:**
```bash
ls -la /etc/nginx/sites-available/trade-desk*
```

---

### Step 4: Update Nginx Configuration (2 minutes)

**Copy the new configuration:**

```bash
sudo cp /home/trade-desk/nginx-config-updated.conf /etc/nginx/sites-available/trade-desk
```

**Or manually edit:**
```bash
sudo nano /etc/nginx/sites-available/trade-desk
```

**Key changes in the new config:**

#### A. Secure Documentation (around line 55)
```nginx
# Secure API documentation (password protected)
location ~ ^/(docs|openapi\.json) {
    auth_basic "TradeDesk Documentation";
    auth_basic_user_file /etc/nginx/.htpasswd_docs;
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

#### B. Block /redoc (around line 65)
```nginx
# Block /redoc completely (disabled)
location /redoc {
    return 404;
}
```

#### C. Remove old /docs and /redoc blocks
Delete these sections (if present):
```nginx
# DELETE THIS:
location /docs {
    # auth_basic "TradeDesk Restricted";
    # auth_basic_user_file /etc/nginx/.htpasswd;
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
}

# DELETE THIS:
location /redoc {
    # auth_basic "TradeDesk Restricted";
    # auth_basic_user_file /etc/nginx/.htpasswd;
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
}
```

**Save and exit:**
- Press `Ctrl + O` to save
- Press `Enter` to confirm
- Press `Ctrl + X` to exit

---

### Step 5: Test Nginx Configuration (1 minute)

**Test for syntax errors:**

```bash
sudo nginx -t
```

**Expected output:**
```
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
```

**If there's an error:**
- Review the error message
- Check line numbers mentioned
- Or restore backup: `sudo cp /etc/nginx/sites-available/trade-desk.backup-* /etc/nginx/sites-available/trade-desk`

---

### Step 6: Reload Nginx (30 seconds)

**Apply the new configuration:**

```bash
sudo systemctl reload nginx
echo "✅ Nginx reloaded"
```

**Check Nginx status:**
```bash
sudo systemctl status nginx
# Should show: active (running)
```

---

## ✅ Verification & Testing

### Test 1: Health Check (Should Work - No Auth)

```bash
curl -s https://piyushdev.com/health | python3 -m json.tool
```

**Expected:** `{"status": "healthy", ...}`

---

### Test 2: /docs - Should Require Password

**Try without password:**
```bash
curl -I https://piyushdev.com/docs
```

**Expected:**
```
HTTP/2 401
www-authenticate: Basic realm="TradeDesk Documentation"
```

**Try with password:**
```bash
curl -u piyushdev:YOUR_PASSWORD https://piyushdev.com/docs
```

**Expected:** HTML page with Swagger UI

---

### Test 3: /redoc - Should Return 404

```bash
curl -I https://piyushdev.com/redoc
```

**Expected:**
```
HTTP/2 404
```

---

### Test 4: Browser Access

**Open browser and visit:**
1. https://piyushdev.com/docs
   - Should show login popup
   - Enter username: `piyushdev`
   - Enter password: `YOUR_PASSWORD`
   - Should load Swagger UI

2. https://piyushdev.com/redoc
   - Should show 404 Not Found error

3. https://piyushdev.com/health
   - Should work without password
   - Shows: `{"status":"healthy",...}`

---

## 📋 What's Secured Now

| Endpoint | Status | Access |
|----------|--------|--------|
| `/docs` | 🔒 **Secured** | Username + Password required |
| `/openapi.json` | 🔒 **Secured** | Username + Password required |
| `/redoc` | ❌ **Disabled** | Returns 404 |
| `/health` | ✅ Public | No authentication |
| `/api/*` | ⚠️ **JWT Required** | JWT token in headers |

---

## 🔐 Credentials

**For Documentation Access:**
- **URL:** https://piyushdev.com/docs
- **Username:** `piyushdev`
- **Password:** `[The password you set in Step 2]`

**For API Access:**
- **Method:** JWT Token
- **Get Token:** `POST /api/v1/auth/login`
- **Use Token:** `Authorization: Bearer <token>`

---

## 🛠️ Troubleshooting

### Issue: "401 Unauthorized" on /docs

**Cause:** Password file not found or incorrect

**Fix:**
```bash
# Check if file exists
sudo ls -la /etc/nginx/.htpasswd_docs

# If missing, create it again
sudo htpasswd -c /etc/nginx/.htpasswd_docs piyushdev
```

---

### Issue: Nginx won't reload

**Cause:** Syntax error in config

**Fix:**
```bash
# Test config
sudo nginx -t

# If error, restore backup
sudo cp /etc/nginx/sites-available/trade-desk.backup-* /etc/nginx/sites-available/trade-desk
sudo systemctl reload nginx
```

---

### Issue: Can't remember password

**Solution:** Reset password
```bash
sudo htpasswd /etc/nginx/.htpasswd_docs piyushdev
# Enter new password
```

---

### Issue: /redoc still accessible

**Check:**
```bash
# Verify Nginx config loaded
sudo nginx -t
sudo systemctl reload nginx

# Test
curl -I https://piyushdev.com/redoc
# Should return 404
```

---

### Issue: Backend not responding

**Check backend status:**
```bash
# Check if running
ps aux | grep uvicorn

# Check logs
tail -f /tmp/backend.log

# Restart if needed
cd /home/trade-desk/backend
kill $(cat /tmp/backend.pid)
source venv/bin/activate
nohup python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 > /tmp/backend.log 2>&1 &
echo $! > /tmp/backend.pid
```

---

## 📊 Summary

### What Changed:
1. ✅ `/redoc` completely disabled (returns 404)
2. ✅ `/docs` secured with HTTP Basic Auth
3. ✅ `/openapi.json` secured with HTTP Basic Auth
4. ✅ Backend updated to disable ReDoc
5. ✅ Nginx configured with password protection

### Security Benefits:
- 🔒 Documentation only accessible with password
- 🚫 No unauthorized API schema access
- ✅ Health check still public (for monitoring)
- 🔐 API endpoints still protected by JWT

### Time Taken:
- **Total:** ~7 minutes
- Step 1: 2 min (restart backend)
- Step 2: 1 min (create password)
- Step 3: 1 min (backup)
- Step 4: 2 min (update config)
- Step 5: 1 min (test & reload)

---

## ✅ Completion Checklist

- [ ] Backend restarted
- [ ] Password file created (`/etc/nginx/.htpasswd_docs`)
- [ ] Nginx config backed up
- [ ] Nginx config updated
- [ ] Nginx config tested (`nginx -t`)
- [ ] Nginx reloaded
- [ ] `/docs` requires password ✓
- [ ] `/redoc` returns 404 ✓
- [ ] `/health` works without auth ✓
- [ ] Password saved securely

---

## 🎉 Done!

Your documentation is now secured and ReDoc is disabled.

**To access documentation:**
1. Visit: https://piyushdev.com/docs
2. Enter username: `piyushdev`
3. Enter your password
4. Enjoy secure access!

**Next Steps:**
- Consider adding more security measures (see `SECURITY_IMPROVEMENTS_PLAN.md`)
- Set up alerts for failed authentication attempts
- Regularly review access logs

---

**Need Help?**
- Check logs: `sudo tail -f /var/log/nginx/trade-desk-error.log`
- Backend logs: `tail -f /tmp/backend.log`
- Restore backup if needed

---

**Files Created:**
- `/home/trade-desk/nginx-config-updated.conf` - New Nginx config
- `/home/trade-desk/SECURE_DOCS_GUIDE.md` - This guide
- `/etc/nginx/.htpasswd_docs` - Password file (created in Step 2)

