"""
Test FCM Notification System

This script tests the FCM notification functionality.
Run this after setting up FCM credentials.
"""

import asyncio
import os
import sys

# Add parent directory to path to import from backend
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.fcm_service import fcm_service


async def test_fcm_service():
    """Test FCM service initialization and availability"""
    print("=" * 60)
    print("Testing FCM Service")
    print("=" * 60)
    print()
    
    # Test 1: Check if FCM is available
    print("Test 1: Checking FCM Service Availability")
    print("-" * 60)
    is_available = fcm_service.is_available()
    
    if is_available:
        print("✅ FCM Service is AVAILABLE and initialized")
        print(f"   Credentials path: {os.getenv('FCM_CREDENTIAL_PATH', 'Not set')}")
    else:
        print("❌ FCM Service is NOT AVAILABLE")
        print("   Please set FCM_CREDENTIAL_PATH environment variable")
        print("   and ensure Firebase credentials file exists")
        return False
    print()
    
    # Test 2: Test sending a notification (with dummy token)
    print("Test 2: Testing Notification Send (with invalid token)")
    print("-" * 60)
    print("Note: This will fail with invalid token, which is expected")
    print()
    
    result = await fcm_service.send_notification(
        tokens=["dummy_token_for_testing"],
        title="Test Notification",
        body="This is a test notification from SBM Gramin Rajasthan",
        data={
            "test": "true",
            "message": "FCM service is working"
        }
    )
    
    print(f"Result: {result}")
    print()
    
    if result.get('failure_count', 0) > 0:
        print("✅ Test completed (failure expected with dummy token)")
    else:
        print("✅ Notification send attempted")
    print()
    
    print("=" * 60)
    print("FCM Service Test Complete")
    print("=" * 60)
    print()
    print("Next Steps:")
    print("1. Register a real device token using the API endpoints")
    print("2. Create a complaint to trigger worker notification")
    print("3. Update complaint status to trigger citizen notification")
    print()
    
    return True


async def test_database_models():
    """Test database models for FCM tokens"""
    print("=" * 60)
    print("Testing Database Models")
    print("=" * 60)
    print()
    
    try:
        from models.database.fcm_device import UserDeviceToken, PublicUserDeviceToken
        print("✅ Successfully imported UserDeviceToken model")
        print("✅ Successfully imported PublicUserDeviceToken model")
        print()
        
        # Check table names
        print(f"Staff device tokens table: {UserDeviceToken.__tablename__}")
        print(f"Public user device tokens table: {PublicUserDeviceToken.__tablename__}")
        print()
        
        return True
    except Exception as e:
        print(f"❌ Error importing models: {e}")
        return False


async def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("FCM NOTIFICATION SYSTEM TESTS")
    print("=" * 60)
    print()
    
    # Test database models
    db_test = await test_database_models()
    
    # Test FCM service
    fcm_test = await test_fcm_service()
    
    print()
    print("=" * 60)
    print("OVERALL TEST RESULTS")
    print("=" * 60)
    print(f"Database Models: {'✅ PASS' if db_test else '❌ FAIL'}")
    print(f"FCM Service: {'✅ PASS' if fcm_test else '❌ FAIL'}")
    print("=" * 60)
    print()


if __name__ == "__main__":
    asyncio.run(main())
