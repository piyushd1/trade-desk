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
    technical_analysis,
    fundamentals,
)

api_router = APIRouter()

# Include route modules
api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(risk.router, tags=["Risk Management"])
api_router.include_router(audit.router, tags=["Audit & Compliance"])
api_router.include_router(broker.router, prefix="/broker", tags=["Broker Integration"])
api_router.include_router(zerodha_simple.router, prefix="/data", tags=["Zerodha Data API"])
api_router.include_router(zerodha_streaming.router, prefix="/data")  # Already has prefix="/zerodha" and tags in router
api_router.include_router(zerodha_data_management.router, prefix="/data")  # Already has prefix="/zerodha/data" and tags in router
api_router.include_router(orders.router)  # Already has prefix and tags in router
api_router.include_router(technical_analysis.router)  # Already has prefix and tags in router
api_router.include_router(fundamentals.router)  # Already has prefix and tags in router

# TODO: Add more routers as they are implemented
# api_router.include_router(strategies.router, prefix="/strategies", tags=["Strategies"])
# api_router.include_router(orders.router, prefix="/orders", tags=["Orders"])
# api_router.include_router(data.router, prefix="/data", tags=["Data"])

