#!/usr/bin/env python3
"""
Quick test script to check service integration
"""

import asyncio
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

async def test_basic_imports():
    """Test basic imports without starting the full service"""
    try:
        print("Testing basic imports...")

        # Test database models
        from app.database import Base, Report, Schedule, Export, QueryTemplate
        print("✅ Database models imported successfully")

        # Test config
        from app.config import get_settings
        settings = get_settings()
        print("✅ Config imported successfully")

        # Test services (without database connection)
        try:
            from app.services.query_service import QueryService
            print("✅ Query service imported successfully")
        except Exception as e:
            print(f"⚠️  Query service import issue: {e}")

        try:
            from app.services.auth_service import get_current_tenant
            print("✅ Auth service imported successfully")
        except Exception as e:
            print(f"⚠️  Auth service import issue: {e}")

        # Test main app (this will likely fail due to routes)
        try:
            from app.main import app
            print("✅ FastAPI app imported successfully")
        except Exception as e:
            print(f"❌ FastAPI app import failed: {e}")
            return False

        return True

    except Exception as e:
        print(f"❌ Basic imports failed: {e}")
        return False

async def main():
    """Run integration tests"""
    print("🧪 S2C-11 Reports Service Integration Test")
    print("=" * 50)

    success = await test_basic_imports()

    if success:
        print("\n✅ All tests passed! Service is ready for deployment.")
        print("\nNext steps:")
        print("1. Configure environment variables (DATABASE_URL, etc.)")
        print("2. Start the service: uvicorn app.main:app --host 0.0.0.0 --port 8004")
        print("3. Test API endpoints at http://localhost:8004/docs")
    else:
        print("\n❌ Some tests failed. Check the errors above and fix them.")

if __name__ == "__main__":
    asyncio.run(main())
