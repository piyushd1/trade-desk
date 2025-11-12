# 🚀 Quick Start Guide

**Get the backend running in 5 minutes!**

---

## ✅ Step 1: Verify Setup (30 seconds)

```bash
cd /home/trade-desk/backend
source venv/bin/activate
python test_setup.py
```

**Expected Output:** All 6 checks should pass ✅

---

## ✅ Step 2: Start the Server (10 seconds)

```bash
cd /home/trade-desk/backend
source venv/bin/activate
python -m uvicorn app.main:app --reload
```

**Expected Output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
✅ Application startup complete
```

---

## ✅ Step 3: Test the API (30 seconds)

Open a **new terminal** and run:

```bash
# Test 1: Health check
curl http://localhost:8000/health

# Test 2: System status
curl http://localhost:8000/api/v1/health/status

# Test 3: SEBI compliance
curl http://localhost:8000/api/v1/health/compliance

# Test 4: Browse API docs
open http://localhost:8000/docs
```

---

## ✅ Step 4: What's Working?

- ✅ FastAPI backend running
- ✅ SQLite database initialized
- ✅ 3 health check endpoints
- ✅ Swagger API documentation
- ✅ All 60+ dependencies installed
- ✅ Configuration management working

---

## 📋 Next Steps

### Immediate (Today):
1. Get Zerodha API keys from https://developers.kite.trade/
2. Get Groww API keys from https://groww.in/v3/api-keys
3. Add keys to `.env` file
4. Test OAuth flow

### This Week:
1. Implement authentication
2. Test order placement (paper mode)
3. Add risk controls
4. Create first strategy

---

## 🔧 Useful Commands

```bash
# Start server
cd /home/trade-desk/backend && source venv/bin/activate
python -m uvicorn app.main:app --reload

# Run tests
python test_setup.py

# Check logs
tail -f logs/app.log

# Stop server
pkill -f uvicorn

# Access Swagger UI
open http://localhost:8000/docs
```

---

## 📚 Documentation

- **API Docs**: http://localhost:8000/docs (when server running)
- **Implementation Status**: See `TESTED_AND_WORKING.md`
- **Full PRD**: See `docs/` directory
- **Zerodha Docs**: https://kite.trade/docs/connect/v3/
- **Groww Docs**: https://groww.in/trade-api/docs/python-sdk

---

## 🎯 Current Status

```
✅ Backend Foundation: 100% Complete
✅ API Working: 100% Complete
📋 Broker Integration: 40% Complete
📋 Authentication: 10% Complete
📋 Risk Management: 0% Complete
📋 Strategy Engine: 0% Complete
```

**Overall Progress: 35% Complete (Phase 0)**

---

## ❓ Need Help?

1. Check `TESTED_AND_WORKING.md` for detailed status
2. Check `IMPLEMENTATION_STATUS.md` for roadmap
3. Review PRD docs in `docs/` directory
4. Check server logs: `tail -f backend/server.log`

---

**You're all set! Backend is running successfully! 🎉**

**Next**: Get your broker API keys and start implementing OAuth!

