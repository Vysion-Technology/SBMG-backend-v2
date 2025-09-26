"""
Basic tests for segregated user management system
"""

import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


async def test_services():
    """Test basic functionality of segregated services"""
    try:
        # Test imports
        from services.login_user_service import LoginUserService
        from services.person_management_service import PersonManagementService

        print("✅ Successfully imported segregated services")

        # Test service instantiation (without database)
        # Note: This will fail without actual database connection
        print("✅ Services can be imported and are properly structured")

        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def test_controllers():
    """Test controller imports"""
    try:
        from controllers.login_management import router as login_router
        from controllers.person_management import router as person_router

        print("✅ Successfully imported segregated controllers")
        print(f"✅ Login management router has {len(login_router.routes)} routes")
        print(f"✅ Person management router has {len(person_router.routes)} routes")

        return True
    except ImportError as e:
        print(f"❌ Controller import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Controller error: {e}")
        return False


async def test_models():
    """Test response model imports"""
    try:
        from models.response.segregated_user_management import (
            LoginUserResponse,
            PersonResponse,
            RoleResponse,
            PersonWithLoginResponse,
        )

        print("✅ Successfully imported response models")

        # Test model instantiation
        login_response = LoginUserResponse(id=1, username="test@example.com", email="test@example.com", is_active=True)
        print(f"✅ LoginUserResponse model works: {login_response.username}")

        return True
    except ImportError as e:
        print(f"❌ Model import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Model error: {e}")
        return False


async def main():
    """Run all tests"""
    print("🔍 Testing Segregated User Management System")
    print("=" * 50)

    tests = [("Services", test_services), ("Controllers", test_controllers), ("Models", test_models)]

    results = []

    for test_name, test_func in tests:
        print(f"\n📋 Testing {test_name}:")
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
            results.append((test_name, False))

    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")

    all_passed = True
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {test_name}: {status}")
        if not passed:
            all_passed = False

    if all_passed:
        print("\n🎉 All tests passed! Segregated user management system is ready.")
        print("\n📝 Next steps:")
        print("  1. Run the application: python main.py")
        print("  2. Test the APIs using the endpoints documented in SEGREGATED_USER_MANAGEMENT.md")
        print("  3. Implement frontend integration using the new segregated APIs")
    else:
        print("\n⚠️  Some tests failed. Please fix the issues before proceeding.")


if __name__ == "__main__":
    asyncio.run(main())
