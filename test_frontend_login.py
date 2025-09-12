#!/usr/bin/env python3
"""
Frontend Login Test Script
Tests the exact login flow that the React frontend would use
"""

import requests
import json


def test_frontend_login_flow():
    """Test the complete frontend login flow"""

    # Test with demo user
    telegram_id = 12345

    print("🔐 Testing Frontend Login Flow...")
    print(f"📱 Attempting login with Telegram ID: {telegram_id}")

    # Step 1: Create/Login User
    print("\n1️⃣ Creating/Login user...")

    user_data = {
        "telegram_id": telegram_id,
        "username": f"demo_{telegram_id}",
        "first_name": "احمد",
        "last_name": "تست",
    }

    try:
        response = requests.post(
            "http://localhost:8001/api/users",
            headers={"Content-Type": "application/json"},
            json=user_data,
        )

        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")

        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                token = data.get("token")
                user_id = data.get("user_id")
                print(
                    f"✅ User creation successful! Token: {token}, User ID: {user_id}"
                )

                # Step 2: Verify Authentication
                print("\n2️⃣ Verifying authentication...")

                auth_headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                }

                auth_response = requests.get(
                    "http://localhost:8001/api/users/me", headers=auth_headers
                )

                print(f"Auth Status Code: {auth_response.status_code}")
                print(f"Auth Response: {auth_response.text}")

                if auth_response.status_code == 200:
                    user_data = auth_response.json()
                    print(
                        f"✅ Authentication successful! User: {user_data.get('first_name')} {user_data.get('last_name')}"
                    )

                    # Step 3: Test Dashboard Data Fetching
                    print("\n3️⃣ Testing dashboard data fetching...")

                    endpoints_to_test = [
                        "/api/accounts",
                        "/api/transactions/summary",
                        "/api/checks",
                        "/api/savings-plans",
                    ]

                    for endpoint in endpoints_to_test:
                        try:
                            resp = requests.get(
                                f"http://localhost:8001{endpoint}", headers=auth_headers
                            )
                            print(
                                f"✅ {endpoint}: {resp.status_code} - {len(resp.json()) if resp.status_code == 200 else 'Error'}"
                            )
                        except Exception as e:
                            print(f"❌ {endpoint}: Error - {e}")

                    return True
                else:
                    print(f"❌ Authentication failed: {auth_response.status_code}")
                    return False
            else:
                print(f"❌ User creation failed: success=False")
                return False
        else:
            print(f"❌ User creation failed: Status {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False


def test_cors_preflight():
    """Test CORS preflight requests"""
    print("\n🌐 Testing CORS Preflight...")

    try:
        # Simulate browser OPTIONS request
        response = requests.options(
            "http://localhost:8001/api/users",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )

        print(f"CORS Preflight Status: {response.status_code}")
        print(f"CORS Headers: {dict(response.headers)}")

        if response.status_code == 200:
            print("✅ CORS preflight successful")
            return True
        else:
            print("❌ CORS preflight failed")
            return False

    except Exception as e:
        print(f"❌ CORS test failed: {e}")
        return False


if __name__ == "__main__":
    print("🧪 Frontend Login Flow Test")
    print("=" * 50)

    # Test CORS first
    cors_ok = test_cors_preflight()

    # Test login flow
    login_ok = test_frontend_login_flow()

    print("\n" + "=" * 50)
    print("📋 FINAL RESULTS:")
    print(f"🌐 CORS: {'✅ OK' if cors_ok else '❌ FAILED'}")
    print(f"🔐 Login Flow: {'✅ OK' if login_ok else '❌ FAILED'}")

    if cors_ok and login_ok:
        print("\n🎉 ALL TESTS PASSED! Frontend should work correctly.")
        print("\n💡 Try these steps in the browser:")
        print("1. Open http://localhost:5173")
        print("2. Use demo login: Ahmad (12345) or Sara (67890)")
        print("3. Or enter any Telegram ID (e.g., 12345)")
    else:
        print("\n⚠️  Some tests failed. Check the issues above.")
