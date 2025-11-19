# 🚀 Trade Desk Setup Instructions

**Current Status:** Nginx configured, Backend running, **GCP Firewall needed**

---

## ⚠️ **REQUIRED: Configure GCP Firewall (Do This First!)**

### **Option 1: GCP Console (Easiest - 2 minutes)**

1. **Open GCP Console:**
   ```
   https://console.cloud.google.com/networking/firewalls/list
   ```

2. **Create HTTP Rule:**
   - Click **"CREATE FIREWALL RULE"**
   - Name: `allow-http`
   - Direction: **Ingress**
   - Action: **Allow**
   - Targets: **All instances**
   - Source IP ranges: `0.0.0.0/0`
   - Protocols: **tcp:80**
   - Click **CREATE**

3. **Create HTTPS Rule:**
   - Click **"CREATE FIREWALL RULE"**
   - Name: `allow-https`
   - Direction: **Ingress**
   - Action: **Allow**
   - Targets: **All instances**
   - Source IP ranges: `0.0.0.0/0`
   - Protocols: **tcp:443**
   - Click **CREATE**

### **Option 2: gcloud Command (From local machine with gcloud auth)**

```bash
# From your local machine (not the VM)
gcloud compute firewall-rules create allow-http \
    --allow tcp:80 \
    --source-ranges 0.0.0.0/0 \
    --description "Allow HTTP"

gcloud compute firewall-rules create allow-https \
    --allow tcp:443 \
    --source-ranges 0.0.0.0/0 \
    --description "Allow HTTPS"
```

---

## ✅ **After Firewall is Configured:**

### **Run the Automated Setup Script:**

```bash
cd /home/trade-desk
./setup_ssl.sh
```

This will:
1. ✅ Test domain connectivity
2. ✅ Verify Nginx is running
3. ✅ Verify backend is running
4. ✅ Obtain SSL certificate from Let's Encrypt
5. ✅ Update Nginx with SSL configuration
6. ✅ Test HTTPS access

---

## 🧪 **Manual Testing Steps (After SSL Setup)**

### **Test 1: HTTPS Works**
```bash
curl https://yourdomain.com/health
```
**Expected:** `{"status":"healthy","environment":"development","version":"1.0.0"}`

### **Test 2: API Status**
```bash
curl https://yourdomain.com/api/v1/health/status
```
**Expected:** JSON with database latency

### **Test 3: Compliance Check**
```bash
curl https://yourdomain.com/api/v1/health/compliance
```
**Expected:** SEBI compliance configuration

### **Test 4: Swagger UI**
Visit in browser: **https://yourdomain.com/docs**

### **Test 5: HTTP Redirect**
```bash
curl -I http://yourdomain.com
```
**Expected:** `301 Moved Permanently` redirecting to HTTPS

---

## 📋 **Zerodha Registration Information**

After SSL is working, register your app at:
**https://developers.kite.trade/**

### **App Configuration:**

| Field | Value |
|-------|-------|
| **App Name** | Trade Desk - Personal Algo Trading |
| **Description** | Algorithmic trading platform for personal use |
| **Type** | Connect |
| **Redirect URL** | `https://yourdomain.com/api/v1/auth/zerodha/callback` |
| **Postback URL** | `https://yourdomain.com/api/v1/postback/zerodha` |

### **What You'll Get:**
- **API Key**: Public identifier
- **API Secret**: Private secret (keep secure!)

### **Add to .env File:**
```bash
# Edit /home/trade-desk/backend/.env
ZERODHA_API_KEY=your_api_key_here
ZERODHA_API_SECRET=your_api_secret_here
ZERODHA_REDIRECT_URL=https://yourdomain.com/api/v1/auth/zerodha/callback
```

---

## 🔧 **Current Configuration Summary**

```yaml
Domain: yourdomain.com (with www)
Static IP: 34.180.15.147
DNS: ✅ Configured (verified with dig)
Nginx: ✅ Configured and running
Backend: ✅ Running on localhost:8000
SSL: ⏳ Waiting for GCP firewall

Firewall Status:
  - Local (ufw): Inactive (not needed)
  - GCP: ❌ BLOCKING HTTP/HTTPS (needs configuration)

Once Firewall Fixed:
  - SSL: Will obtain automatically
  - HTTPS: Will be fully functional
  - Zerodha: Ready to register
```

---

## 📊 **What's Already Working:**

✅ Backend API on localhost:
```bash
curl http://localhost:8000/health
curl http://localhost:8000/docs  # Swagger UI (port forward to view)
```

✅ Nginx reverse proxy (locally):
```bash
curl http://localhost/health
```

✅ DNS resolution:
```bash
dig +short yourdomain.com
# Returns: 34.180.15.147
```

---

## ⏭️ **Next Steps:**

1. **You do**: Configure GCP firewall (2 minutes)
2. **Run**: `./setup_ssl.sh` (automated)
3. **Test**: Access https://yourdomain.com
4. **Register**: Create Zerodha app with your URLs
5. **Continue**: We'll implement OAuth flow

---

## 🆘 **Troubleshooting**

### If domain still not accessible after firewall:
```bash
# Check GCP firewall rules applied
gcloud compute firewall-rules list --filter="name:allow-http OR name:allow-https"

# Check Nginx status
sudo systemctl status nginx

# Check Nginx logs
sudo tail -f /var/log/nginx/error.log

# Check backend logs
tail -f /tmp/backend.log
```

### If SSL certificate fails:
```bash
# Check detailed Certbot logs
sudo tail -50 /var/log/letsencrypt/letsencrypt.log

# Manual test
sudo certbot certonly --nginx -d yourdomain.com --dry-run
```

---

**⏸️ Waiting for you to configure GCP firewall, then run `./setup_ssl.sh`**

