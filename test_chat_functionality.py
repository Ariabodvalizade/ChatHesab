#!/usr/bin/env python3
"""
Test the enhanced chat functionality with fallback
"""

import requests
import json

API_BASE_URL = "http://localhost:8001"


def test_chat_with_fallback():
    """Test the chat processing with fallback system"""

    # First login
    login_data = {
        "telegram_id": 12345,
        "username": "test_user",
        "first_name": "Ahmad",
        "last_name": "Test",
    }

    response = requests.post(f"{API_BASE_URL}/api/users", json=login_data)
    if response.status_code == 200:
        data = response.json()
        token = data.get("token")
        print(f"✅ Login successful, token: {token}")
    else:
        print(f"❌ Login failed: {response.status_code}")
        return

    # Test messages
    test_messages = [
        "50 هزار تومان قهوه خریدم",
        "2 میلیون حقوق گرفتم",
        "200 تومان اتوبوس",
        "100 هزار بنزین",
        "خرید لباس 300 هزار",
    ]

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    print("\n🤖 Testing Enhanced Chat Processing:")
    print("=" * 50)

    for message in test_messages:
        print(f"\n📝 Message: '{message}'")

        try:
            response = requests.post(
                f"{API_BASE_URL}/api/ai/process-message",
                json={"message": message},
                headers=headers,
                timeout=15,  # 15 second timeout
            )

            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    print(f"✅ Success!")
                    print(f"   Type: {result.get('transaction_type')}")
                    print(f"   Amount: {result.get('amount')} تومان")
                    print(f"   Category: {result.get('category')}")
                    print(f"   Response: {result.get('response_message')}")
                    print(f"   Confidence: {result.get('confidence', 'N/A')}")
                else:
                    print(f"❌ Failed: {result.get('error')}")
                    print(
                        f"   Response: {result.get('response_message', 'No response')}"
                    )
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Error: {response.text}")
        except requests.exceptions.Timeout:
            print("⏱️ Request timed out (likely using fallback system)")
        except Exception as e:
            print(f"❌ Exception: {e}")


if __name__ == "__main__":
    print("🚀 Starting Enhanced Chat Test...")
    test_chat_with_fallback()
    print("\n✨ Test completed!")
