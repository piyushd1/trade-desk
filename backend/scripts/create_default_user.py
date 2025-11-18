"""
Create Default User Script

This script creates a default admin user for initial login.
Run this once to set up the first user account.

The script will:
1. Check for credentials in environment variables (ADMIN_USERNAME, ADMIN_EMAIL, ADMIN_PASSWORD)
2. If not found, prompt interactively for secure credential entry
3. Validate password strength
4. Create the admin user in the database
"""

import asyncio
import getpass
import re
import sys
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings
from app.database import get_db_context
from app.models.user import User, UserRole
from app.services.auth_service import auth_service


def validate_email(email: str) -> bool:
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_password(password: str) -> tuple[bool, str]:
    """
    Validate password strength.

    Requirements:
    - At least 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one number
    - At least one special character

    Returns:
        tuple: (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"

    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"

    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"

    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"

    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character (!@#$%^&*(),.?\":{}|<>)"

    return True, ""


def get_user_credentials() -> tuple[str, str, str, str]:
    """
    Get user credentials from environment variables or interactive prompt.

    Returns:
        tuple: (username, email, password, full_name)
    """
    # Try to get from environment variables first
    username = settings.ADMIN_USERNAME
    email = settings.ADMIN_EMAIL
    password = settings.ADMIN_PASSWORD

    if username and email and password:
        print("📝 Using admin credentials from environment variables...")
        return username, email, password, "Admin User"

    # Interactive prompt
    print("📝 No credentials found in environment variables.")
    print("Please enter admin user details:\n")

    # Get username
    while True:
        username = input("Enter username (default: admin): ").strip() or "admin"
        if len(username) >= 3:
            break
        print("❌ Username must be at least 3 characters long\n")

    # Get email
    while True:
        email = input("Enter email address: ").strip()
        if validate_email(email):
            break
        print("❌ Invalid email format. Please try again.\n")

    # Get full name
    full_name = input("Enter full name (default: Admin User): ").strip() or "Admin User"

    # Get password with validation
    while True:
        password = getpass.getpass("Enter password: ")
        is_valid, error_msg = validate_password(password)

        if not is_valid:
            print(f"❌ {error_msg}")
            print("Password requirements:")
            print("  - At least 8 characters")
            print("  - At least one uppercase letter")
            print("  - At least one lowercase letter")
            print("  - At least one number")
            print("  - At least one special character\n")
            continue

        # Confirm password
        password_confirm = getpass.getpass("Confirm password: ")
        if password == password_confirm:
            break

        print("❌ Passwords do not match. Please try again.\n")

    print()
    return username, email, password, full_name


async def create_default_user():
    """Create a default admin user for initial login."""

    # Get credentials
    username, email, password, full_name = get_user_credentials()

    print("🔐 Creating admin user...")
    print(f"Username: {username}")
    print(f"Email: {email}")
    print(f"Full Name: {full_name}\n")
    
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
            
            print("✅ Admin user created successfully!")
            print(f"   User ID: {new_user.id}")
            print(f"   Username: {new_user.username}")
            print(f"   Email: {new_user.email}")
            print(f"   Role: {new_user.role.value}")
            print(f"\n📝 You can now login with the credentials you provided.")
            print(f"\n⚠️  Keep your credentials secure and never share them!")
            
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
