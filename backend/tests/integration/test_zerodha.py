#!/usr/bin/env python3
"""
Zerodha API Integration Test Script
Tests if Zerodha API credentials are working
"""

import sys
from kiteconnect import KiteConnect
from app.config import settings


def test_zerodha_config():
    """Test if Zerodha configuration is loaded"""
    print("🔍 Testing Zerodha Configuration...")
    print("="*60)
    
    if not settings.ZERODHA_API_KEY:
        print("❌ ZERODHA_API_KEY is not set in .env")
        return False
    
    if not settings.ZERODHA_API_SECRET:
        print("❌ ZERODHA_API_SECRET is not set in .env")
        return False
    
    if not settings.ZERODHA_REDIRECT_URL:
        print("❌ ZERODHA_REDIRECT_URL is not set in .env")
        return False
    
    print(f"✅ API Key: {settings.ZERODHA_API_KEY[:8]}..." + "*" * 8)
    print(f"✅ API Secret: " + "*" * 16 + " (hidden)")
    print(f"✅ Redirect URL: {settings.ZERODHA_REDIRECT_URL}")
    print()
    return True


def test_kite_connect_initialization():
    """Test if KiteConnect can be initialized"""
    print("🔧 Testing KiteConnect Initialization...")
    print("="*60)
    
    try:
        kite = KiteConnect(api_key=settings.ZERODHA_API_KEY)
        print("✅ KiteConnect object created successfully")
        print()
        return kite
    except Exception as e:
        print(f"❌ Failed to create KiteConnect object: {e}")
        return None


def test_login_url_generation(kite):
    """Test if login URL can be generated"""
    print("🔗 Testing Login URL Generation...")
    print("="*60)
    
    try:
        login_url = kite.login_url()
        print(f"✅ Login URL generated successfully:")
        print(f"   {login_url}")
        print()
        print("📋 To test OAuth flow:")
        print(f"   1. Visit this URL in your browser: {login_url}")
        print("   2. Login with your Zerodha credentials")
        print("   3. You'll be redirected to your callback URL with request_token")
        print()
        return True
    except Exception as e:
        print(f"❌ Failed to generate login URL: {e}")
        return False


def main():
    """Run all Zerodha tests"""
    print()
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║           ZERODHA API INTEGRATION TEST                       ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()
    
    results = []
    
    # Test 1: Configuration
    results.append(("Configuration Loaded", test_zerodha_config()))
    
    # Test 2: KiteConnect Initialization
    kite = test_kite_connect_initialization()
    results.append(("KiteConnect Initialization", kite is not None))
    
    # Test 3: Login URL Generation
    if kite:
        results.append(("Login URL Generation", test_login_url_generation(kite)))
    else:
        results.append(("Login URL Generation", False))
    
    # Summary
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║                      TEST SUMMARY                            ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print()
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    if passed == total:
        print(f"🎉 All {total}/{total} tests passed!")
        print()
        print("✅ Your Zerodha integration is configured correctly!")
        print()
        print("📋 Next Steps:")
        print("   1. Test the OAuth flow (visit the login URL above)")
        print("   2. Implement OAuth callback handler")
        print("   3. Test API authentication")
        print()
    else:
        print(f"⚠️  {passed}/{total} tests passed")
        print()
        print("Please fix the failed tests before proceeding.")
        print()


if __name__ == "__main__":
    main()

