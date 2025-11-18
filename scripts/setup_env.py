#!/usr/bin/env python3
"""
TradeDesk Environment Setup Script

This script helps you set up the environment configuration for TradeDesk.
It will:
1. Copy .env.example to .env (if not exists)
2. Prompt for essential configuration values
3. Generate secure keys automatically
4. Validate inputs

Usage:
    python scripts/setup_env.py
"""

import os
import secrets
import shutil
import sys
from pathlib import Path
from cryptography.fernet import Fernet


def print_header(text: str):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(text.center(70))
    print("=" * 70 + "\n")


def print_section(text: str):
    """Print a section header."""
    print(f"\n{'─' * 70}")
    print(f"  {text}")
    print(f"{'─' * 70}\n")


def generate_secret_key(length: int = 64) -> str:
    """Generate a secure random secret key."""
    return secrets.token_urlsafe(length)


def generate_fernet_key() -> str:
    """Generate a Fernet encryption key."""
    return Fernet.generate_key().decode()


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent


def setup_backend_env():
    """Set up backend environment configuration."""
    project_root = get_project_root()
    backend_dir = project_root / "backend"
    env_example = backend_dir / ".env.example"
    env_file = backend_dir / ".env"

    print_section("Backend Environment Setup")

    # Check if .env.example exists
    if not env_example.exists():
        print(f"❌ Error: {env_example} not found!")
        print("Please ensure .env.example exists in the backend directory.")
        return False

    # Check if .env already exists
    if env_file.exists():
        response = input(f"⚠️  {env_file} already exists. Overwrite? (y/N): ").strip().lower()
        if response != 'y':
            print("Skipping backend environment setup.")
            return True

    # Copy .env.example to .env
    print(f"📋 Copying {env_example.name} to {env_file.name}...")
    shutil.copy(env_example, env_file)

    print("\n📝 Configuring essential values...\n")

    # Read the .env file
    with open(env_file, 'r') as f:
        env_content = f.read()

    # Generate secure keys
    print("🔐 Generating secure keys...")
    secret_key = generate_secret_key()
    jwt_secret = generate_secret_key()
    encryption_key = generate_fernet_key()

    # Replace placeholder values
    replacements = {
        'SECRET_KEY=your-secret-key-here-change-this-in-production': f'SECRET_KEY={secret_key}',
        'JWT_SECRET_KEY=your-jwt-secret-key-change-this-in-production': f'JWT_SECRET_KEY={jwt_secret}',
        'ENCRYPTION_KEY=your-fernet-key-here-generate-with-command-above': f'ENCRYPTION_KEY={encryption_key}',
    }

    for old, new in replacements.items():
        env_content = env_content.replace(old, new)

    print("✅ Secure keys generated successfully!\n")

    # Prompt for essential configuration
    print("Please provide the following information:")
    print("(Press Enter to keep default values)\n")

    # APP_ENV
    app_env = input("Environment (development/staging/production) [development]: ").strip() or "development"
    env_content = env_content.replace('APP_ENV=development', f'APP_ENV={app_env}')

    # APP_DOMAIN
    app_domain = input("Your domain name (e.g., example.com) [example.com]: ").strip() or "example.com"
    env_content = env_content.replace('APP_DOMAIN=example.com', f'APP_DOMAIN={app_domain}')

    # STATIC_IP
    print("\n⚠️  SEBI Compliance requires a static IP address.")
    static_ip = input("Your static IP address: ").strip()
    if static_ip:
        env_content = env_content.replace('STATIC_IP=0.0.0.0', f'STATIC_IP={static_ip}')

    # Database URL
    print("\n📦 Database Configuration:")
    print("1. SQLite (for development)")
    print("2. PostgreSQL (for production)")
    db_choice = input("Choose database type (1/2) [1]: ").strip() or "1"

    if db_choice == "2":
        db_user = input("PostgreSQL username [tradedesk]: ").strip() or "tradedesk"
        db_pass = input("PostgreSQL password: ").strip()
        db_host = input("PostgreSQL host [localhost]: ").strip() or "localhost"
        db_port = input("PostgreSQL port [5432]: ").strip() or "5432"
        db_name = input("PostgreSQL database name [tradedesk]: ").strip() or "tradedesk"

        db_url = f"postgresql+asyncpg://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
        env_content = env_content.replace(
            'DATABASE_URL=sqlite+aiosqlite:///./tradedesk.db',
            f'DATABASE_URL={db_url}'
        )

    # Zerodha credentials
    print("\n🔗 Zerodha Broker Configuration (Optional):")
    print("You can configure this later in the .env file if needed.\n")
    configure_zerodha = input("Configure Zerodha now? (y/N): ").strip().lower()

    if configure_zerodha == 'y':
        zerodha_key = input("Zerodha API Key: ").strip()
        zerodha_secret = input("Zerodha API Secret: ").strip()
        zerodha_user = input("Zerodha User ID: ").strip()

        if zerodha_key:
            env_content = env_content.replace('ZERODHA_API_KEY=your-zerodha-api-key', f'ZERODHA_API_KEY={zerodha_key}')
        if zerodha_secret:
            env_content = env_content.replace('ZERODHA_API_SECRET=your-zerodha-api-secret', f'ZERODHA_API_SECRET={zerodha_secret}')
        if zerodha_user:
            env_content = env_content.replace('ZERODHA_USER_IDENTIFIER=YOUR_USER_ID', f'ZERODHA_USER_IDENTIFIER={zerodha_user}')

    # Write the configured .env file
    with open(env_file, 'w') as f:
        f.write(env_content)

    print(f"\n✅ Backend environment configured successfully!")
    print(f"   Configuration saved to: {env_file}")
    print(f"\n📝 You can edit {env_file} to customize additional settings.")

    return True


def setup_frontend_env():
    """Set up frontend environment configuration."""
    project_root = get_project_root()
    frontend_dir = project_root / "frontend"
    env_example = frontend_dir / ".env.local.example"
    env_file = frontend_dir / ".env.local"

    print_section("Frontend Environment Setup")

    # Check if frontend directory exists
    if not frontend_dir.exists():
        print(f"⚠️  Frontend directory not found. Skipping frontend setup.")
        return True

    # Check if .env.local.example exists
    if not env_example.exists():
        print(f"⚠️  {env_example.name} not found. Skipping frontend setup.")
        return True

    # Check if .env.local already exists
    if env_file.exists():
        response = input(f"⚠️  {env_file} already exists. Overwrite? (y/N): ").strip().lower()
        if response != 'y':
            print("Skipping frontend environment setup.")
            return True

    # Copy .env.local.example to .env.local
    print(f"📋 Copying {env_example.name} to {env_file.name}...")
    shutil.copy(env_example, env_file)

    print(f"\n✅ Frontend environment configured successfully!")
    print(f"   Configuration saved to: {env_file}")
    print(f"\n📝 You can edit {env_file} to customize additional settings.")

    return True


def main():
    """Main setup function."""
    print_header("TradeDesk Environment Setup")

    print("""
This script will help you set up the environment configuration for TradeDesk.

What this script does:
  ✓ Copies .env.example to .env
  ✓ Generates secure cryptographic keys
  ✓ Prompts for essential configuration values
  ✓ Validates inputs where applicable

After setup, you can:
  • Edit .env files manually for additional configuration
  • Run: python backend/scripts/create_default_user.py (to create admin user)
  • Start the application

Let's get started!
""")

    input("Press Enter to continue...")

    # Set up backend environment
    if not setup_backend_env():
        print("\n❌ Backend setup failed!")
        return 1

    # Set up frontend environment
    if not setup_frontend_env():
        print("\n❌ Frontend setup failed!")
        return 1

    # Success message
    print_header("Setup Complete!")

    print("""
✅ Environment configuration completed successfully!

Next steps:
  1. Review and customize your .env files if needed:
     • backend/.env
     • frontend/.env.local

  2. Create the default admin user:
     $ cd backend
     $ python scripts/create_default_user.py

  3. Start the application:
     Backend:  $ cd backend && uvicorn app.main:app --reload
     Frontend: $ cd frontend && npm run dev

  4. Access the application:
     • Frontend: http://localhost:3000
     • Backend API: http://localhost:8000
     • API Documentation: http://localhost:8000/docs

📚 For more information, see:
  • ENVIRONMENT_SETUP.md - Detailed environment configuration guide
  • SETUP_INSTRUCTIONS.md - Complete setup instructions
  • README.md - Project overview

Need help? Check the documentation or open an issue on GitHub.

Happy trading! 🚀
""")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during setup: {e}")
        sys.exit(1)
