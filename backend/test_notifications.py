"""
Quick test script for E-Booklet notifications
Run this to verify your email and SMS setup is working
"""

import requests
import json
import sys

# Configuration
BASE_URL = "http://localhost:8000"
TEST_PHONE = "+918618898432"  # Change this to your phone number

def test_notification_service():
    """Test the notification service"""
    print("🧪 Testing E-Booklet Notification Service\n")
    print("=" * 60)
    
    # Test 1: Health Check
    print("\n1️⃣  Testing API Health...")
    try:
        response = requests.get(f"{BASE_URL}/api/healthz")
        if response.status_code == 200:
            print("✅ API is running!")
            print(f"   Status: {response.json()['status']}")
        else:
            print(f"❌ API health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        print("   Make sure the backend is running: python -m uvicorn app.main:app --reload --port 8000")
        return False
    
    # Test 2: SMS Notification
    print("\n2️⃣  Testing SMS Notification...")
    try:
        payload = {
            "email": "test@example.com",  # Dummy email (required by API)
            "phone": TEST_PHONE
        }
        response = requests.post(
            f"{BASE_URL}/api/notify/test",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("sms", {}).get("success"):
                print(f"✅ SMS sent successfully to {TEST_PHONE}")
                print("   Check your phone!")
            else:
                print(f"⚠️  SMS not sent: {result.get('sms', {}).get('message')}")
                print(f"   Details: {result.get('sms')}")
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ SMS test failed: {e}")
    
    # Test 3: Appointment Notification (example)
    print("\n3️⃣  Example: Appointment Notification")
    print("   To test with authentication, use:")
    print(f"   POST {BASE_URL}/api/notify/appointment")
    print("   Headers: Authorization: Bearer YOUR_FIREBASE_TOKEN")
    print("   Body: See NOTIFICATIONS_SETUP.md for example")
    
    print("\n" + "=" * 60)
    print("✨ Testing complete!")
    print("\n📚 Next steps:")
    print("   1. Check your phone for SMS")
    print("   2. Review NOTIFICATIONS_SETUP.md for full documentation")
    print("   3. Import E-Booklet_Notifications.postman_collection.json to Postman")
    print("\n")

if __name__ == "__main__":
    # Check if phone is configured
    if TEST_PHONE == "+1234567890":
        print("⚠️  Please update TEST_PHONE in this script before running!")
        print("   Edit test_notifications.py and change:")
        print('   TEST_PHONE = "+1234567890"')
        print("   to your actual phone number (with country code)")
        sys.exit(1)
    
    test_notification_service()
