#!/usr/bin/env python3
"""
Simple AI test script - standalone
"""

import google.generativeai as genai
import json

# Configure API
genai.configure(api_key="AIzaSyCqZHAZBCnXxpwoFP0VChO66W-AFo8Mi04")
model = genai.GenerativeModel("gemini-2.0-flash-exp")


def test_ai_directly():
    """Test AI directly without web API"""

    message = "50 هزار تومان قهوه خریدم"

    prompt = f"""
تو یک دستیار مالی هوشمند هستی که پیام‌های فارسی کاربران را تحلیل می‌کنی.

حساب‌های کاربر:
- ملت (حساب اصلی) - ID: 1

پیام کاربر: "{message}"

این پیام را تحلیل کن و اطلاعات زیر را به صورت JSON استخراج کن:

{{
    "type": "transaction" یا "check" یا "query" یا "unknown",
    "transaction_type": "income" یا "expense" (اگر نوع transaction باشد),
    "amount": عدد (مثلاً ۱۵۰ هزار = 150000),
    "amount_text": متن اصلی مبلغ که کاربر نوشته,
    "category": دسته‌بندی مناسب به فارسی,
    "account_id": 1,
    "account_name": "حساب اصلی",
    "description": توضیحات تراکنش,
    "date": تاریخ امروز به فرمت YYYY-MM-DD,
    "response_message": پیام پاسخ مناسب به فارسی برای کاربر,
    "confidence": میزان اطمینان از 0 تا 1
}}

نکات مهم:
1. اگر کاربر "تومن" یا "تومان" گفته و عدد کمتر از 10000 است، احتمالاً منظورش هزار تومان است
2. دسته‌بندی‌های رایج: خانه، خواربار، رستوران و کافی‌شاپ، حمل و نقل، پوشاک، درمان و سلامت، آموزش، سرگرمی، موبایل و اینترنت، تعمیرات، هدیه، اقساط و وام، مالیات، سفر، حقوق، کسب و کار، سرمایه‌گذاری، اجاره، پروژه، سایر
3. برای تشخیص نوع (درآمد/هزینه) به کلمات کلیدی مثل: خرید، پرداخت، هزینه، برداشت (expense) یا دریافت، حقوق، درآمد، واریز (income) توجه کن
4. در response_message پاسخ مناسب و دوستانه به فارسی بنویس

فقط JSON را برگردان، توضیح اضافی نده.
"""

    try:
        print(f"🤖 Testing message: '{message}'")
        print("⏳ Sending to Google AI...")

        response = model.generate_content(prompt)
        response_text = response.text.strip()

        print(f"📋 Raw response: {response_text}")

        # Parse JSON
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]

        result = json.loads(response_text.strip())

        print("✅ Parsed result:")
        print(json.dumps(result, ensure_ascii=False, indent=2))

        return result

    except Exception as e:
        print(f"❌ Error: {e}")
        return None


if __name__ == "__main__":
    test_ai_directly()
