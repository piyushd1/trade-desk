"""
FastAPI Application Entry Point
Main application setup with all routes and middleware
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import time
import logging
import asyncio

from app.config import settings
from app.database import init_db, close_db
from app.api.v1 import api_router
from app.services.token_refresh_service import token_refresh_service
from app.services.audit_service import audit_service

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events
    """
    # Startup
    logger.info("🚀 Starting Trade Desk...")
    logger.info(f"Environment: {settings.APP_ENV}")
    logger.info(f"Debug Mode: {settings.DEBUG}")
    
    try:
        # Initialize database
        await init_db()
        logger.info("✅ Database initialized")
        
        # Log system startup event
        await audit_service.log_system_event(
            event_type="startup",
            severity="info",
            message="TradeDesk application started",
            component="main",
            details={
                "environment": settings.APP_ENV,
                "debug_mode": settings.DEBUG,
                "version": "1.0.0"
            }
        )
        
        # Start token refresh service if enabled
        if settings.ZERODHA_AUTO_REFRESH_ENABLED:
            token_refresh_service.refresh_interval_minutes = settings.ZERODHA_REFRESH_INTERVAL_MINUTES
            token_refresh_service.expiry_buffer_minutes = settings.ZERODHA_REFRESH_EXPIRY_BUFFER_MINUTES
            await token_refresh_service.start()
            logger.info("✅ Token refresh service started")
        else:
            logger.info("⚠️ Token auto-refresh is disabled")
        
        # TODO: Initialize Redis connection
        # TODO: Initialize Celery workers
        
        logger.info("✅ Application startup complete")
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down...")
    
    try:
        # Log system shutdown event
        await audit_service.log_system_event(
            event_type="shutdown",
            severity="info",
            message="TradeDesk application shutting down",
            component="main"
        )
        
        # Stop token refresh service
        if settings.ZERODHA_AUTO_REFRESH_ENABLED:
            token_refresh_service.stop()
            logger.info("✅ Token refresh service stopped")
        
        await close_db()
        logger.info("✅ Database connections closed")
        
        # TODO: Close Redis connections
        # TODO: Stop Celery workers
        # TODO: Clean up resources
        
    except Exception as e:
        logger.error(f"❌ Shutdown error: {e}")
        await audit_service.log_system_event(
            event_type="shutdown",
            severity="error",
            message=f"Error during shutdown: {str(e)}",
            component="main",
            stack_trace=str(e)
        )


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="TradeDesk - Personal Trading Platform with SEBI Compliance",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GZip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add X-Process-Time header to responses"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": exc.errors(),
            "body": exc.body,
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all uncaught exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    if settings.DEBUG:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": str(exc),
                "type": type(exc).__name__,
            },
        )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check(request: Request):
    """
    Health check endpoint for monitoring
    
    Returns:
        dict: Service health status
    """
    # Log health check (lightweight, async fire-and-forget)
    try:
        # Don't await to avoid blocking health check response
        asyncio.create_task(
            audit_service.log_system_event(
                event_type="health_check",
                severity="info",
                message="Health check endpoint accessed",
                component="main",
                details={
                    "ip_address": request.client.host if request.client else None,
                    "user_agent": request.headers.get("user-agent")
                }
            )
        )
    except Exception:
        pass  # Don't fail health check if audit logging fails
    
    return {
        "status": "healthy",
        "environment": settings.APP_ENV,
        "version": "1.0.0",
    }


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint with API information
    """
    return {
        "message": "Trade Desk API",
        "version": "1.0.0",
        "docs": "/docs" if settings.DEBUG else "Documentation disabled in production",
        "health": "/health",
    }


# Include API routes
app.include_router(api_router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        workers=1 if settings.DEBUG else settings.WORKERS,
        log_level=settings.LOG_LEVEL.lower(),
    )

