#!/usr/bin/env python3
"""
One-time Instagram authentication script
Run this on the VM to authenticate and save session
"""
import asyncio
import sys
from app.services.instagram_service import InstagramService

async def main():
    print("=" * 60)
    print("Instagram Authentication")
    print("=" * 60)
    print()

    service = InstagramService()

    try:
        await service.login()
        print()
        print("✅ Authentication successful!")
        print("✅ Session saved to instagram_session.json")
        print()
        print("You can now use the analysis API.")
        return 0
    except Exception as e:
        print()
        print(f"❌ Authentication failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
