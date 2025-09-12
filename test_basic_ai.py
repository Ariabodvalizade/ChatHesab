#!/usr/bin/env python3
"""
Simple test to check if Google AI API is working
"""

import google.generativeai as genai
import sys


def test_basic_ai():
    """Test basic AI functionality"""
    try:
        print("🔧 Testing Google AI API...")

        # Configure API
        api_key = "AIzaSyCqZHAZBCnXxpwoFP0VChO66W-AFo8Mi04"
        genai.configure(api_key=api_key)

        # Create model
        model = genai.GenerativeModel("gemini-2.0-flash-exp")

        # Simple test
        print("📤 Sending simple test message...")
        response = model.generate_content("Hello, respond with just 'OK'")

        print(f"📥 Response: {response.text}")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    success = test_basic_ai()
    if success:
        print("✅ AI API is working!")
    else:
        print("❌ AI API has issues!")
        sys.exit(1)
