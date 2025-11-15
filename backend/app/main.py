"""
TradeDesk API Application

This is the main entry point for the TradeDesk FastAPI application.
It sets up the application with all necessary middleware, routes, and
lifecycle management.

The application includes:
- SEBI-compliant trading functionality
- Risk management systems
- Audit logging
- Multiple broker integrations
- Automated token management
"""

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1 import api_router
from app.config import settings
from app.database import check_db_connection, close_db, init_db
from app.services.audit_service import audit_service
from app.services.token_refresh_service import token_refresh_service
from app.services.zerodha_streaming_service import zerodha_streaming_manager

# Configure structured logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
    handlers=[
        logging.StreamHandler(),
        # Add file handler in production
        *(
            [logging.FileHandler(settings.LOG_FILE)]
            if settings.is_production and settings.LOG_FILE
            else []
        ),
    ],
)

# Get logger for this module
logger = logging.getLogger(__name__)

# Application metadata
APP_VERSION = "1.0.0"
APP_DESCRIPTION = """
## TradeDesk API

**SEBI-compliant algorithmic trading platform** for personal use.

### 🔐 Authentication

**Getting Your JWT Token:**
1. Use the `POST /api/v1/auth/login` endpoint with your username and password
2. Copy the `access_token` from the response
3. Click the **"Authorize"** button (top right) and paste your token
4. Or include it in requests as: `Authorization: Bearer <your_token>`

**Test Users:**
- `piyushdev` / `piyush123` (user_id: 2)
- `admin` / `admin123` (user_id: 1)

**Token Expiration:**
- Access tokens expire in 15 minutes
- Use `POST /api/v1/auth/refresh` to get a new token

### Features
- 🔐 **Secure Authentication**: JWT-based auth with refresh tokens
- 📊 **Multi-Broker Support**: Zerodha, Groww integrations
- 🛡️ **Risk Management**: Position limits, stop-loss, daily loss limits
- 📝 **Audit Logging**: Complete audit trail for compliance
- 🔄 **Auto Token Refresh**: Automated broker token management
- 📈 **Performance Monitoring**: Request timing and metrics

### API Sections
- **Authentication** (`/auth`): User login, JWT tokens, Zerodha OAuth
- **Order Management** (`/orders`): Order preview, place, modify, cancel
- **Risk Management** (`/risk`): Risk config, kill switch, pre-trade checks
- **Zerodha Data** (`/data/zerodha`): Profile, margins, positions, orders, trades
- **Market Data** (`/data/zerodha`): LTP, quote, OHLC, historical data
- **Data Management** (`/data/zerodha/data`): Instrument sync, historical storage
- **Streaming** (`/data/zerodha/stream`): Real-time WebSocket data streams
- **Audit** (`/audit`): Compliance and audit logs

### 📖 Using This Documentation

1. **Get Token**: Use `POST /api/v1/auth/login` to get your JWT token
2. **Authorize**: Click "Authorize" button and paste your token
3. **Test APIs**: Click "Try it out" on any endpoint to test it
4. **View Examples**: All endpoints have example request/response bodies
"""


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifecycle management.

    Handles startup and shutdown procedures including:
    - Database initialization
    - Background service startup
    - Resource cleanup on shutdown
    """
    # ===== STARTUP =====
    startup_start = time.time()
    logger.info(f"🚀 Starting {settings.APP_NAME} v{APP_VERSION}")
    logger.info(f"Environment: {settings.APP_ENV}")
    logger.info(f"Debug Mode: {'ON' if settings.DEBUG else 'OFF'}")

    startup_errors = []

    try:
        # Check database connection
        if await check_db_connection():
            logger.info("✅ Database connection established")
            await init_db()
            logger.info("✅ Database tables initialized")
        else:
            startup_errors.append("Database connection failed")

        # Initialize audit service
        try:
            await audit_service.initialize()
            await audit_service.log_system_event(
                event_type="startup",
                severity="info",
                message=f"{settings.APP_NAME} application started",
                component="main",
                details={
                    "version": APP_VERSION,
                    "environment": settings.APP_ENV,
                    "debug_mode": settings.DEBUG,
                    "startup_time": time.time() - startup_start,
                },
            )
            logger.info("✅ Audit service initialized")
        except Exception as e:
            logger.warning(f"⚠️  Audit service initialization failed: {e}")

        # Start token refresh service
        if settings.ZERODHA_AUTO_REFRESH_ENABLED:
            token_refresh_service.refresh_interval_minutes = (
                settings.ZERODHA_REFRESH_INTERVAL_MINUTES
            )
            token_refresh_service.expiry_buffer_minutes = (
                settings.ZERODHA_REFRESH_EXPIRY_BUFFER_MINUTES
            )
            await token_refresh_service.start()
            logger.info("✅ Token refresh service started")
        else:
            logger.info("ℹ️  Token auto-refresh is disabled")

        # Log successful startup
        startup_time = time.time() - startup_start
        logger.info(f"✅ Application startup complete in {startup_time:.2f}s")

        if startup_errors:
            logger.warning(f"⚠️  Startup completed with errors: {startup_errors}")

    except Exception as e:
        logger.error(f"❌ Critical startup failure: {e}", exc_info=True)
        # Log critical failure to audit if possible
        try:
            await audit_service.log_system_event(
                event_type="startup_failure",
                severity="critical",
                message=f"Application startup failed: {str(e)}",
                component="main",
                stack_trace=str(e),
            )
        except Exception:
            pass
        raise

    yield  # Application runs here

    # ===== SHUTDOWN =====
    shutdown_start = time.time()
    logger.info("🛑 Initiating graceful shutdown...")

    shutdown_errors = []

    try:
        # Log shutdown event
        try:
            await audit_service.log_system_event(
                event_type="shutdown",
                severity="info",
                message="Application shutdown initiated",
                component="main",
            )
        except Exception as e:
            shutdown_errors.append(f"Audit logging failed: {e}")

        # Stop background services
        if settings.ZERODHA_AUTO_REFRESH_ENABLED:
            token_refresh_service.stop()
            logger.info("✅ Token refresh service stopped")

        # Stop any active Zerodha streams
        try:
            zerodha_streaming_manager.stop_all()
            logger.info("✅ Zerodha streaming manager stopped")
        except Exception as e:
            shutdown_errors.append(f"Streaming manager stop failed: {e}")

        # Close database connections
        try:
            await close_db()
            logger.info("✅ Database connections closed")
        except Exception as e:
            shutdown_errors.append(f"Database closure failed: {e}")

        shutdown_time = time.time() - shutdown_start
        logger.info(f"✅ Shutdown complete in {shutdown_time:.2f}s")

        if shutdown_errors:
            logger.warning(f"⚠️  Shutdown completed with errors: {shutdown_errors}")

    except Exception as e:
        logger.error(f"❌ Error during shutdown: {e}", exc_info=True)


# Create FastAPI application instance
app = FastAPI(
    title=settings.APP_NAME,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    docs_url="/docs" if settings.DEBUG else None,  # Disable in production
    redoc_url="/redoc" if settings.DEBUG else None,  # Disable in production
    openapi_url="/openapi.json" if settings.DEBUG else None,  # Disable in production
    # default_response_class=ORJSONResponse,  # Faster JSON serialization
    lifespan=lifespan,
)

# ===== MIDDLEWARE CONFIGURATION =====

# CORS middleware - Configure allowed origins
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:3002",
    "http://localhost:5173",
]

# Add production origins if configured
if settings.APP_URL:
    ALLOWED_ORIGINS.append(settings.APP_URL)
if settings.APP_DOMAIN:
    ALLOWED_ORIGINS.extend([f"https://{settings.APP_DOMAIN}", f"http://{settings.APP_DOMAIN}"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=3600,  # Cache preflight requests for 1 hour
)

# Trusted host middleware (security)
if settings.is_production and settings.APP_DOMAIN:
    app.add_middleware(
        TrustedHostMiddleware, allowed_hosts=[settings.APP_DOMAIN, "*.piyushdev.com"]
    )

# GZip compression for responses
app.add_middleware(GZipMiddleware, minimum_size=1000)


# ===== CUSTOM MIDDLEWARE =====


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """
    Add processing time to response headers.

    Adds an X-Process-Time header to all responses for performance monitoring.
    """
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.3f}"

    # Log slow requests
    if process_time > 1.0:  # Log requests taking more than 1 second
        logger.warning(
            f"Slow request: {request.method} {request.url.path} took {process_time:.3f}s"
        )

    return response


@app.middleware("http")
async def catch_exceptions_middleware(request: Request, call_next):
    """
    Global exception catching middleware.

    Ensures all exceptions are properly logged and formatted.
    """
    try:
        return await call_next(request)
    except Exception as exc:
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        # Re-raise to let exception handlers deal with it
        raise


# ===== EXCEPTION HANDLERS =====


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions with consistent formatting."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
                "type": "http_error",
            }
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with detailed information."""
    errors = []
    for error in exc.errors():
        errors.append(
            {
                "field": ".".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"],
            }
        )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": 422,
                "message": "Validation failed",
                "type": "validation_error",
                "details": errors,
            }
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all uncaught exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    # Log to audit service
    try:
        await audit_service.log_system_event(
            event_type="unhandled_exception",
            severity="error",
            message=f"Unhandled exception: {type(exc).__name__}",
            component="main",
            details={
                "exception_type": type(exc).__name__,
                "exception_message": str(exc),
                "path": request.url.path,
                "method": request.method,
            },
            stack_trace=str(exc),
        )
    except Exception:
        pass  # Don't fail the response if audit logging fails

    if settings.DEBUG:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": 500,
                    "message": str(exc),
                    "type": type(exc).__name__,
                }
            },
        )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": 500,
                "message": "Internal server error",
                "type": "internal_error",
            }
        },
    )


# ===== ROOT ENDPOINTS =====


@app.get("/", tags=["Root"], summary="API Information")
async def root() -> dict[str, Any]:
    """
    Get API information and available endpoints.

    Returns basic information about the API including version,
    documentation URLs, and health check endpoint.
    """
    return {
        "name": settings.APP_NAME,
        "version": APP_VERSION,
        "environment": settings.APP_ENV,
        "docs": "/docs" if settings.DEBUG else "Disabled in production",
        "redoc": "/redoc" if settings.DEBUG else "Disabled in production",
        "health": "/health",
        "api": "/api/v1",
    }


@app.get(
    "/health",
    tags=["Health"],
    summary="Health Check",
    response_model=dict[str, Any],
)
async def health_check(request: Request) -> dict[str, Any]:
    """
    Health check endpoint for monitoring.

    Returns the current health status of the application including
    database connectivity and background service status.

    This endpoint is designed to be lightweight and fast for use
    with load balancers and monitoring systems.
    """
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "version": APP_VERSION,
        "environment": settings.APP_ENV,
        "services": {},
    }

    # Check database connectivity
    try:
        db_healthy = await check_db_connection()
        health_status["services"]["database"] = "healthy" if db_healthy else "unhealthy"
    except Exception:
        health_status["services"]["database"] = "error"
        health_status["status"] = "degraded"

    # Check token refresh service
    if settings.ZERODHA_AUTO_REFRESH_ENABLED:
        health_status["services"]["token_refresh"] = (
            "running" if token_refresh_service.is_running else "stopped"
        )

    # Log health check asynchronously
    asyncio.create_task(
        audit_service.log_system_event(
            event_type="health_check",
            severity="info",
            message="Health check performed",
            component="main",
            details={
                "status": health_status["status"],
                "ip_address": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent"),
            },
        )
    )

    # Return appropriate status code
    status_code = (
        status.HTTP_200_OK
        if health_status["status"] == "healthy"
        else status.HTTP_503_SERVICE_UNAVAILABLE
    )

    return JSONResponse(content=health_status, status_code=status_code)


# ===== INCLUDE ROUTERS =====

# Include all API routes with version prefix
app.include_router(api_router, prefix="/api/v1")


# ===== MAIN EXECUTION =====

if __name__ == "__main__":
    import uvicorn

    # Configure uvicorn for development/production
    uvicorn_config = {
        "app": "app.main:app",
        "host": settings.API_HOST,
        "port": settings.API_PORT,
        "log_level": settings.LOG_LEVEL.lower(),
    }

    if settings.is_development:
        # Development settings
        uvicorn_config.update(
            {
                "reload": True,
                "workers": 1,
                "reload_dirs": ["app"],
            }
        )
    else:
        # Production settings
        uvicorn_config.update(
            {
                "reload": False,
                "workers": settings.WORKERS,
                "access_log": False,  # Use custom logging
                "loop": "uvloop",  # Faster event loop
            }
        )

    uvicorn.run(**uvicorn_config)
