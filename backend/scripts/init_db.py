#!/usr/bin/env python
"""
Database Initialization Script
Creates database and TimescaleDB extension
"""

import asyncio
import asyncpg
from app.config import settings


async def init_database():
    """
    Initialize database and TimescaleDB extension
    """
    print("🔧 Initializing database...")
    
    # Parse database URL
    db_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "")
    parts = db_url.split("@")
    user_pass = parts[0].split(":")
    host_db = parts[1].split("/")
    host_port = host_db[0].split(":")
    
    username = user_pass[0]
    password = user_pass[1] if len(user_pass) > 1 else ""
    host = host_port[0]
    port = int(host_port[1]) if len(host_port) > 1 else 5432
    database = host_db[1].split("?")[0]
    
    try:
        # Connect to postgres database to create our database
        conn = await asyncpg.connect(
            host=host,
            port=port,
            user=username,
            password=password,
            database='postgres'
        )
        
        # Check if database exists
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname=$1", database
        )
        
        if not exists:
            print(f"📦 Creating database: {database}")
            await conn.execute(f'CREATE DATABASE "{database}"')
        else:
            print(f"✅ Database already exists: {database}")
        
        await conn.close()
        
        # Connect to our database to enable TimescaleDB
        conn = await asyncpg.connect(
            host=host,
            port=port,
            user=username,
            password=password,
            database=database
        )
        
        # Enable TimescaleDB extension
        print("📊 Enabling TimescaleDB extension...")
        await conn.execute("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE")
        print("✅ TimescaleDB enabled")
        
        await conn.close()
        
        print("✅ Database initialization complete!")
        print(f"\nNext steps:")
        print("1. Run migrations: alembic upgrade head")
        print("2. Start the server: python -m app.main")
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(init_database())

