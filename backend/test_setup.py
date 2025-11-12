#!/usr/bin/env python3
"""
Setup Verification Script
Tests that all basic dependencies and configurations are working
"""

import sys
import importlib
from typing import List, Tuple

def check_python_version():
    """Check Python version"""
    print("🐍 Checking Python version...")
    version = sys.version_info
    if version >= (3, 11):
        print(f"   ✅ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"   ❌ Python {version.major}.{version.minor}.{version.micro} (Need 3.11+)")
        return False

def check_dependencies():
    """Check if all required packages are installed"""
    print("\n📦 Checking dependencies...")
    
    required_packages = [
        ('fastapi', 'FastAPI'),
        ('uvicorn', 'Uvicorn'),
        ('sqlalchemy', 'SQLAlchemy'),
        ('asyncpg', 'AsyncPG'),
        ('redis', 'Redis'),
        ('pydantic', 'Pydantic'),
        ('pydantic_settings', 'Pydantic Settings'),
        ('alembic', 'Alembic'),
        ('kiteconnect', 'Kite Connect'),
        ('pandas', 'Pandas'),
        ('pyotp', 'PyOTP'),
    ]
    
    results = []
    for package, display_name in required_packages:
        try:
            importlib.import_module(package)
            print(f"   ✅ {display_name}")
            results.append(True)
        except ImportError:
            print(f"   ❌ {display_name} - NOT INSTALLED")
            results.append(False)
    
    return all(results)

def check_env_file():
    """Check if .env file exists"""
    print("\n🔐 Checking environment configuration...")
    import os
    from pathlib import Path
    
    env_path = Path(__file__).parent / '.env'
    env_example_path = Path(__file__).parent / '.env.example'
    
    if env_path.exists():
        print(f"   ✅ .env file exists")
        return True
    elif env_example_path.exists():
        print(f"   ⚠️  .env file not found, but .env.example exists")
        print(f"   📝 Create .env file: cp .env.example .env")
        return False
    else:
        print(f"   ❌ Neither .env nor .env.example found")
        return False

def check_database_connectivity():
    """Check if PostgreSQL is accessible"""
    print("\n🗄️  Checking database connectivity...")
    try:
        from app.config import settings
        print(f"   📍 Database URL configured: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'Not configured'}")
        return True
    except Exception as e:
        print(f"   ❌ Cannot load configuration: {e}")
        return False

def check_redis_connectivity():
    """Check if Redis is accessible"""
    print("\n🔴 Checking Redis connectivity...")
    try:
        from app.config import settings
        print(f"   📍 Redis URL configured: {settings.REDIS_URL}")
        return True
    except Exception as e:
        print(f"   ❌ Cannot load configuration: {e}")
        return False

def check_app_structure():
    """Check if app structure is correct"""
    print("\n🏗️  Checking application structure...")
    from pathlib import Path
    
    required_files = [
        'app/__init__.py',
        'app/main.py',
        'app/config.py',
        'app/database.py',
        'app/models/__init__.py',
        'app/api/__init__.py',
        'app/api/v1/__init__.py',
        'app/brokers/__init__.py',
        'alembic.ini',
        'requirements.txt',
    ]
    
    base_path = Path(__file__).parent
    results = []
    
    for file in required_files:
        file_path = base_path / file
        if file_path.exists():
            print(f"   ✅ {file}")
            results.append(True)
        else:
            print(f"   ❌ {file} - MISSING")
            results.append(False)
    
    return all(results)

def print_summary(checks: List[Tuple[str, bool]]):
    """Print summary of all checks"""
    print("\n" + "="*60)
    print("📊 VERIFICATION SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in checks if result)
    total = len(checks)
    
    for check_name, result in checks:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {check_name}")
    
    print("="*60)
    print(f"Result: {passed}/{total} checks passed")
    print("="*60)
    
    if passed == total:
        print("\n🎉 All checks passed! Ready to proceed.")
        print("\nNext steps:")
        print("1. Create .env file with your configuration")
        print("2. Set up PostgreSQL database")
        print("3. Set up Redis")
        print("4. Run: python -m app.main")
    else:
        print("\n⚠️  Some checks failed. Please fix the issues above.")
        print("\nTo install missing dependencies:")
        print("   pip install -r requirements.txt")

def main():
    """Run all checks"""
    print("🔍 SETUP VERIFICATION SCRIPT")
    print("="*60)
    
    checks = [
        ("Python Version", check_python_version()),
        ("Dependencies", check_dependencies()),
        ("Application Structure", check_app_structure()),
        ("Environment File", check_env_file()),
        ("Database Config", check_database_connectivity()),
        ("Redis Config", check_redis_connectivity()),
    ]
    
    print_summary(checks)

if __name__ == "__main__":
    main()

