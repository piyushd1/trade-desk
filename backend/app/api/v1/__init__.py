"""
API v1 Router
Aggregates all v1 API routes
"""

from fastapi import APIRouter
from app.api.v1 import (
    health,
    auth,
    broker,
    audit,
    risk,
    zerodha_simple,
    zerodha_streaming,
    zerodha_data_management,
    orders,
)

api_router = APIRouter()

# Include route modules
api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(risk.router, tags=["Risk Management"])
api_router.include_router(audit.router, tags=["Audit & Compliance"])
api_router.include_router(broker.router, prefix="/broker", tags=["Broker Integration"])
api_router.include_router(zerodha_simple.router, prefix="/data", tags=["Zerodha Data API"])
api_router.include_router(zerodha_streaming.router, prefix="/data", tags=["Zerodha Streaming"])
api_router.include_router(zerodha_data_management.router, prefix="/data", tags=["Zerodha Data Management"])
api_router.include_router(orders.router, tags=["Order Management"])

# TODO: Add more routers as they are implemented
# api_router.include_router(strategies.router, prefix="/strategies", tags=["Strategies"])
# api_router.include_router(orders.router, prefix="/orders", tags=["Orders"])
# api_router.include_router(data.router, prefix="/data", tags=["Data"])

