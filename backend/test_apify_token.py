"""Test script to verify Apify token is loaded correctly."""
from config import settings

print("=" * 50)
print("Apify Token Configuration Test")
print("=" * 50)
print(f"Token loaded: {settings.apify_token is not None}")
if settings.apify_token:
    print(f"Token (first 10 chars): {settings.apify_token[:10]}...")
    print(f"Token (last 4 chars): ...{settings.apify_token[-4:]}")
    print("✅ Token is configured!")
else:
    print("❌ Token is NOT configured!")
    print("\nTroubleshooting:")
    print("1. Check if backend/.env file exists")
    print("2. Verify APIFY_TOKEN is set in the .env file")
    print("3. Check the .env file path in settings.py")
print("=" * 50)

