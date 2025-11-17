"""
Create Default User Script

This script creates a default user for initial login.
Run this once to set up the first user account.
"""

import asyncio
import sys
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings
from app.database import get_db_context
from app.models.user import User, UserRole
from app.services.auth_service import auth_service


async def create_default_user():
    """Create a default user for initial login."""
    
    # Default user credentials
    username = "admin"
    email = "admin@tradedesk.local"
    password = "Admin@123"  # Change this after first login!
    full_name = "Admin User"
    
    print("🔐 Creating default user...")
    print(f"Username: {username}")
    print(f"Email: {email}")
    print(f"Password: {password}")
    print(f"⚠️  IMPORTANT: Change this password after first login!\n")
    
    try:
        async with get_db_context() as db:
            # Check if user already exists
            existing_user = await auth_service.get_user_by_username(username, db)
            if existing_user:
                print(f"❌ User '{username}' already exists!")
                print(f"   User ID: {existing_user.id}")
                print(f"   Email: {existing_user.email}")
                print(f"   Role: {existing_user.role.value}")
                return
            
            # Create new user
            hashed_password = auth_service.hash_password(password)
            
            new_user = User(
                username=username,
                email=email,
                password_hash=hashed_password,
                full_name=full_name,
                role=UserRole.ADMIN,
                is_active=True,
            )
            
            db.add(new_user)
            await db.commit()
            await db.refresh(new_user)
            
            print("✅ Default user created successfully!")
            print(f"   User ID: {new_user.id}")
            print(f"   Username: {new_user.username}")
            print(f"   Email: {new_user.email}")
            print(f"   Role: {new_user.role.value}")
            print(f"\n📝 You can now login with:")
            print(f"   Username: {username}")
            print(f"   Password: {password}")
            print(f"\n⚠️  Remember to change the password after first login!")
            
    except Exception as e:
        print(f"❌ Error creating user: {e}")
        raise


if __name__ == "__main__":
    print("=" * 60)
    print("TradeDesk - Create Default User")
    print("=" * 60)
    print()
    
    asyncio.run(create_default_user())
    
    print()
    print("=" * 60)
