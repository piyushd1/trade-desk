# GCP Firewall Configuration Required

## ⚠️ Action Needed: Configure GCP Firewall Rules

Your domain cannot be reached because GCP firewall is blocking HTTP/HTTPS traffic.

### **Steps to Fix (5 minutes):**

1. **Go to GCP Console:**
   - Visit: https://console.cloud.google.com/networking/firewalls/list

2. **Create HTTP Firewall Rule:**
   - Click **"CREATE FIREWALL RULE"**
   - Name: `allow-http`
   - Logs: Off
   - Direction: Ingress
   - Action on match: Allow
   - Targets: All instances in the network (or specify your VM)
   - Source filter: IP ranges
   - Source IP ranges: `0.0.0.0/0`
   - Protocols and ports: 
     - ✅ Specified protocols and ports
     - ✅ tcp: `80`
   - Click **CREATE**

3. **Create HTTPS Firewall Rule:**
   - Click **"CREATE FIREWALL RULE"** again
   - Name: `allow-https`
   - Logs: Off
   - Direction: Ingress
   - Action on match: Allow
   - Targets: All instances in the network
   - Source filter: IP ranges
   - Source IP ranges: `0.0.0.0/0`
   - Protocols and ports:
     - ✅ Specified protocols and ports
     - ✅ tcp: `443`
   - Click **CREATE**

4. **Verify Rules:**
   - You should see two new rules in the list
   - Priority: 1000 (default)
   - Target: All instances

### **Alternative: Use gcloud CLI (If you have permissions):**

```bash
gcloud compute firewall-rules create allow-http \
    --allow tcp:80 \
    --source-ranges 0.0.0.0/0 \
    --description "Allow HTTP for Let's Encrypt" \
    --priority 1000

gcloud compute firewall-rules create allow-https \
    --allow tcp:443 \
    --source-ranges 0.0.0.0/0 \
    --description "Allow HTTPS for secure access" \
    --priority 1000
```

### **After Creating Rules:**

**Test connectivity:**
```bash
# From any external machine or your local computer:
curl http://piyushdev.com

# Should return response, not timeout
```

**Then continue with SSL setup.**

---

## ✅ Once Firewall is Configured:

Run this command to obtain SSL certificate:
```bash
sudo certbot certonly --nginx -d piyushdev.com -d www.piyushdev.com \
    --non-interactive --agree-tos --email piyush@piyushdev.com
```

This will:
1. Verify domain ownership
2. Obtain SSL certificate from Let's Encrypt
3. Store certificate at `/etc/letsencrypt/live/piyushdev.com/`

---

**⏸️ Paused here - Please configure GCP firewall first!**

