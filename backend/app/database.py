"""
Database Configuration and Management

This module handles all database-related functionality including:
- Connection management with AsyncPG
- Session lifecycle management
- Database initialization and migrations
- Connection pooling and error handling

The application uses PostgreSQL/TimescaleDB with SQLAlchemy ORM in async mode
for high-performance database operations.
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy import event, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool

from app.config import settings

# Configure logging
logger = logging.getLogger(__name__)

# Database engine configuration based on environment
engine_config = {
    "echo": settings.DEBUG,  # Log SQL queries in debug mode
    "pool_pre_ping": True,  # Verify connections before use
    "future": True,  # Use SQLAlchemy 2.0 style
}

# Configure connection pooling based on the actual database dialect, not APP_ENV.
# SQLite always uses NullPool (pool_size / max_overflow / pool_timeout are not
# accepted by NullPool and would raise TypeError). Only real pooled databases
# like PostgreSQL benefit from the tuning args.
if settings.DATABASE_URL.startswith("sqlite"):
    # SQLite (any environment): use NullPool. Each session gets its own connection.
    engine_config.update({"poolclass": NullPool})
elif settings.is_production:
    # Production with a pooled database (Postgres/Timescale): tune the pool.
    engine_config.update(
        {
            "pool_size": settings.DATABASE_POOL_SIZE,
            "max_overflow": settings.DATABASE_MAX_OVERFLOW,
            "pool_timeout": 30,  # Connection timeout in seconds
            "pool_recycle": 3600,  # Recycle connections after 1 hour
        }
    )
else:
    # Development/testing with a pooled database: NullPool to avoid connection issues
    engine_config.update({"poolclass": NullPool})

# Create async engine with configured settings
engine = create_async_engine(settings.DATABASE_URL, **engine_config)


# SQLite hardening: apply pragmas on every new connection.
# - journal_mode=WAL: readers don't block writers, writers don't block readers
# - busy_timeout=5000: wait up to 5s on lock contention instead of failing immediately
# - synchronous=NORMAL: safe with WAL; big write-throughput win vs FULL
# - foreign_keys=ON: SQLite disables FK enforcement by default, we want it on
# These pragmas are per-connection (except journal_mode, which persists in the
# file header but is also cheap to re-assert). They're no-ops for PostgreSQL.
if settings.DATABASE_URL.startswith("sqlite"):

    @event.listens_for(engine.sync_engine, "connect")
    def _set_sqlite_pragmas(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Don't expire objects after commit
    autocommit=False,  # Use explicit commits
    autoflush=False,  # Don't auto-flush before queries
)

# Base class for all ORM models
Base = declarative_base()

# Add some common functionality to Base
Base.__table_args__ = {"extend_existing": True}  # Allow redefinition of tables


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency injection function for database sessions.

    This function provides a database session with automatic transaction
    management. It ensures that sessions are properly committed on success
    or rolled back on failure, and always closed after use.

    Usage in FastAPI:
        ```python
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Item))
            return result.scalars().all()
        ```

    Yields:
        AsyncSession: Database session for the request

    Raises:
        SQLAlchemyError: On database operation failures
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
            logger.debug("Database session committed successfully")
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"Database error, rolling back: {e}")
            raise
        except Exception as e:
            await session.rollback()
            logger.error(f"Unexpected error, rolling back: {e}")
            raise
        finally:
            await session.close()
            logger.debug("Database session closed")


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager for database sessions outside of FastAPI dependencies.

    This is useful for background tasks, scripts, and testing where you
    need a database session but aren't in a FastAPI request context.

    Usage:
        ```python
        async with get_db_context() as db:
            user = await db.get(User, user_id)
            user.last_login = datetime.utcnow()
            await db.commit()
        ```

    Yields:
        AsyncSession: Database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize database tables.

    This function creates all tables defined in the ORM models if they
    don't already exist. In production, you should use Alembic migrations
    instead of this function.

    Note:
        This is primarily for development and testing. Production deployments
        should use proper migration tools like Alembic.
    """
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables initialized successfully")
    except SQLAlchemyError as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


async def check_db_connection() -> bool:
    """
    Check if database is accessible.

    This function attempts to execute a simple query to verify that the
    database is reachable and operational.

    Returns:
        bool: True if database is accessible, False otherwise
    """
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
            logger.info("Database connection check successful")
            return True
    except SQLAlchemyError as e:
        logger.error(f"Database connection check failed: {e}")
        return False


async def close_db() -> None:
    """
    Close all database connections.

    This should be called during application shutdown to ensure all
    database connections are properly closed and resources are released.
    """
    try:
        await engine.dispose()
        logger.info("Database connections closed successfully")
    except Exception as e:
        logger.error(f"Error closing database connections: {e}")
        raise


# Export commonly used items
__all__ = [
    "Base",
    "engine",
    "AsyncSessionLocal",
    "get_db",
    "get_db_context",
    "init_db",
    "check_db_connection",
    "close_db",
]
