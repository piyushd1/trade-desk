# Streaming API Fix Summary

**Date:** November 15, 2025  
**Status:** ✅ Complete

---

## 🔧 Issues Fixed

### 1. Authentication Token Not Being Sent

**Problem:** The test script was getting 401 "Not authenticated" errors because the `ACCESS_TOKEN` wasn't being properly set or exported.

**Fix:** Enhanced the `test_streaming_apis.sh` script to:
- Better error handling for login
- Verify login response before extracting token
- Export `ACCESS_TOKEN` so it's available to all curl commands
- Add debug logging to show token status

**Changes in `test_streaming_apis.sh`:**
```bash
# Before: Simple check, no export
if [ -z "$ACCESS_TOKEN" ]; then
  ACCESS_TOKEN=$(...)
fi

# After: Proper validation and export
if [ -z "$ACCESS_TOKEN" ]; then
  # Check login response
  if echo "$LOGIN_RESPONSE" | python3 -c "..."; then
    ACCESS_TOKEN=$(...)
    export ACCESS_TOKEN  # Make it available to all commands
    log "✅ Logged in successfully"
  fi
fi
```

---

### 2. Timezone Error in Session Status Endpoint

**Problem:** `TypeError: can't subtract offset-naive and offset-aware datetimes` when calculating `expires_in_minutes`.

**Root Cause:** 
- `expires_at` is stored as timezone-naive in the database (for SQLite compatibility)
- The code was trying to create a timezone-aware `now` datetime
- Python can't subtract naive and aware datetimes

**Fix:** Updated `zerodha_streaming.py` to handle both naive and timezone-aware datetimes:

```python
# Before: Assumed expires_at had timezone info
tz = session.expires_at.tzinfo or timezone.utc
now = datetime.now(tz)
expires_in_minutes = (session.expires_at - now).total_seconds() / 60

# After: Handle both naive and aware datetimes
if session.expires_at.tzinfo is None:
    # If naive, assume it's UTC and make it timezone-aware
    expires_at_aware = session.expires_at.replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
else:
    # If already timezone-aware, use as-is
    expires_at_aware = session.expires_at
    now = datetime.now(expires_at_aware.tzinfo)
expires_in_minutes = (expires_at_aware - now).total_seconds() / 60
```

---

## ✅ Verification

**Test Results:**
```bash
$ curl -H "Authorization: Bearer $ACCESS_TOKEN" \
  "https://piyushdev.com/api/v1/data/zerodha/session/status?user_identifier=RO0252"

{
    "user_identifier": "RO0252",
    "broker": "zerodha",
    "status": "active",
    "has_refresh_token": false,
    "expires_at": "2025-11-16T00:30:00",
    "expires_in_minutes": 1036.3981759666667
}
```

**Status:** ✅ Working correctly!

---

## 📋 Files Modified

1. **`test_streaming_apis.sh`**
   - Enhanced login token extraction
   - Added proper error handling
   - Export `ACCESS_TOKEN` for all commands
   - Added debug logging

2. **`backend/app/api/v1/zerodha_streaming.py`**
   - Fixed timezone handling in session status endpoint
   - Handle both naive and timezone-aware datetimes

---

## 🧪 Testing

**To test the streaming APIs:**

```bash
# 1. Run the test script
cd /home/trade-desk
bash test_streaming_apis.sh

# 2. Or test manually
export ACCESS_TOKEN=$(curl -s -X POST https://piyushdev.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"piyushdev","password":"piyush123"}' | \
  python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

# 3. Test session status
curl -H "Authorization: Bearer $ACCESS_TOKEN" \
  "https://piyushdev.com/api/v1/data/zerodha/session/status?user_identifier=RO0252"
```

---

## 🎉 Result

**Before:**
- ❌ 401 "Not authenticated" errors
- ❌ 500 "can't subtract offset-naive and offset-aware datetimes" errors

**After:**
- ✅ Authentication working correctly
- ✅ Session status endpoint returning data
- ✅ All streaming endpoints ready for testing

---

**Streaming APIs are now fixed and ready for use!** 🎉

