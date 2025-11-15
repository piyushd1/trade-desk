# 🧪 Zerodha OAuth Testing Guide

**Status**: ✅ Zerodha configured and ready to test  
**Login URL**: Available via API

---

## ✅ **What's Working Now**

1. ✅ Zerodha API credentials configured
2. ✅ OAuth login URL generation working
3. ✅ OAuth callback endpoint implemented
4. ✅ Test endpoints created for API verification

---

## 🧪 **Manual OAuth Flow Test**

### **Step 1: Get Login URL**

```bash
# Optionally pass a user identifier using ?state=alias
curl -s "https://piyushdev.com/api/v1/auth/zerodha/connect?state=friend1" | python3 -m json.tool
```

**Response will include:**
```json
{
  "login_url": "https://kite.zerodha.com/connect/login?api_key=XXX&v=3&state=friend1",
  "state": "friend1"
}
```

### **Step 2: Login via Browser**

1. **Copy the `login_url`** from the response above
2. **Open it in your browser**
3. **Login** with your Zerodha credentials
4. **Click "Authorize"** to grant access to your app

### **Step 3: You'll Be Redirected**

After authorization, Zerodha will redirect you to:
```
https://piyushdev.com/api/v1/auth/zerodha/callback?request_token=XXX&status=success&state=friend1
```

**You should see a JSON response like:**
```json
{
  "status": "success",
  "message": "Successfully connected to Zerodha!",
  "user_id": "YOUR_USER_ID",
  "user_name": "YOUR_NAME",
  "broker": "zerodha",
  "access_token": "abcd1234..." (partially hidden)
}
```

**🔴 Copy the full `access_token` from this response - you'll need it for testing!**

The session is now stored in the database under `user_identifier = state` (or the Zerodha user id if `state` was omitted).

---

## 🧪 **Test Zerodha API Calls**

Once you have your `access_token`, test these endpoints:

### **Test 1: Get Profile**
```bash
curl -s "https://piyushdev.com/api/v1/test/zerodha/profile?access_token=YOUR_ACCESS_TOKEN" | python3 -m json.tool
```

**Expected:** Your Zerodha profile data (name, email, products, etc.)

### **Test 2: Get Margins**
```bash
curl -s "https://piyushdev.com/api/v1/test/zerodha/margins?access_token=YOUR_ACCESS_TOKEN" | python3 -m json.tool
```

**Expected:** Available margin in equity, commodity, etc.

### **Test 3: Get Positions**
```bash
curl -s "https://piyushdev.com/api/v1/test/zerodha/positions?access_token=YOUR_ACCESS_TOKEN" | python3 -m json.tool
```

**Expected:** Current open positions (if any)

### **Test 4: Get Holdings**
```bash
curl -s "https://piyushdev.com/api/v1/test/zerodha/holdings?access_token=YOUR_ACCESS_TOKEN" | python3 -m json.tool
```

**Expected:** Your delivery holdings (if any)

---

## 🚀 **Quick Test Script**

Run this to get the login URL:
```bash
cd /home/trade-desk
./test_oauth_flow.sh
```

---

## 📋 **Complete Test Checklist**

- [ ] Step 1: Get login URL via API ✅
- [ ] Step 2: Login via browser
- [ ] Step 3: Authorize the app
- [ ] Step 4: Get redirected to callback
- [ ] Step 5: Receive access token
- [ ] Step 6: Test profile API call
- [ ] Step 7: Test margins API call
- [ ] Step 8: Test positions API call
- [ ] Step 9: Test holdings API call

---

## ⚠️ **Important Notes**

1. **Access Token Validity**: 
   - Valid until 6 AM next day (IST)
   - You'll need to re-authenticate daily (or implement token storage)

2. **Rate Limits**:
   - Global: 10 requests/second
   - Historical data: 3 requests/second
   - Don't exceed these during testing!

3. **Testing Mode**:
   - These are REAL API calls to your Zerodha account
   - No orders will be placed unless you explicitly call order endpoints
   - Profile, margins, positions, holdings are read-only

4. **Security**:
   - Never share your access token
   - Access tokens are sensitive credentials
   - They expire automatically at 6 AM IST

---

## 🆘 **Troubleshooting**

### If OAuth fails:
```bash
# Check backend logs
tail -50 /tmp/backend.log

# Check if API key is correct
curl -s https://piyushdev.com/api/v1/auth/brokers/status | python3 -m json.tool
```

### If API calls fail:
```bash
# Error: "Invalid API key"
# → Check your API key in .env

# Error: "Incorrect api_secret"
# → Check your API secret in .env

# Error: "Token is invalid or has expired"
# → Re-do the OAuth flow to get a new access token
```

---

## ✅ **Success Criteria**

OAuth flow is working if:
- [ ] Login URL is generated
- [ ] Browser login works
- [ ] Redirect to callback succeeds
- [ ] Access token is received
- [ ] At least one API call (profile/margins) returns data

---

**Ready to test! Open the login URL in your browser and authorize the app!** 🚀

