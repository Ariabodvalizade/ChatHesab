# modules/ai_processor.py
import google.generativeai as genai
import json
import logging
from typing import Dict, Optional, List
from datetime import datetime, date
from config import GEMINI_API_KEY, GEMINI_MODEL
from utils.persian_utils import parse_amount, extract_bank_name, normalize_persian_text
from utils.calendar_utils import parse_persian_date, get_persian_date_string

logger = logging.getLogger(__name__)


class AIProcessor:
    def __init__(self):
        """راه‌اندازی Gemini API"""
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel(GEMINI_MODEL)

    def process_message(self, message: str, user_context: Dict = None) -> Dict:
        """پردازش پیام کاربر و استخراج اطلاعات مالی

        Args:
            message: پیام کاربر
            user_context: اطلاعات حساب‌های کاربر

        Returns:
            دیکشنری حاوی اطلاعات استخراج شده
        """
        try:
            # آماده‌سازی prompt
            prompt = self._create_prompt(message, user_context)

            # ارسال به Gemini
            response = self.model.generate_content(prompt)

            # پارس کردن پاسخ JSON
            result = self._parse_response(response.text)

            # اعتبارسنجی و تکمیل اطلاعات
            result = self._validate_and_complete(result, user_context)

            return result

        except Exception as e:
            logger.error(f"خطا در پردازش AI: {e}")
            return {"success": False, "error": "خطا در پردازش پیام"}

    def _create_prompt(self, message: str, user_context: Dict = None) -> str:
        """ایجاد prompt برای Gemini"""

        accounts_info = ""
        if user_context and user_context.get("accounts"):
            accounts_info = "حساب‌های کاربر:\n"
            for acc in user_context["accounts"]:
                accounts_info += f"- {acc['bank_name']} ({acc['account_name']})\n"

        prompt = f"""
تو یک دستیار مالی هوشمند هستی که پیام‌های فارسی کاربران را تحلیل می‌کنی.

{accounts_info}

پیام کاربر: "{message}"

این پیام را تحلیل کن و اطلاعات زیر را به صورت JSON استخراج کن:

{{
    "type": "transaction" یا "check" یا "query" یا "unknown",
    "transaction_type": "income" یا "expense" (اگر نوع transaction باشد),
    "amount": عدد به ریال (مثلاً ۱۵۰ تومان = 1500000),
    "amount_text": متن اصلی مبلغ که کاربر نوشته,
    "category": دسته‌بندی مناسب به فارسی,
    "bank_name": نام بانک (اگر ذکر شده),
    "account_name": نام حساب (اگر ذکر شده),
    "description": توضیحات تراکنش,
    "date": تاریخ به فرمت YYYY-MM-DD (اگر ذکر شده),
    "check_type": "issued" یا "received" (اگر نوع check باشد),
    "recipient_issuer": نام گیرنده یا صادرکننده چک,
    "confidence": میزان اطمینان از 0 تا 1
}}

نکات مهم:
1. اگر کاربر "تومن" یا "تومان" گفته و عدد کمتر از 10000 است، احتمالاً منظورش هزار تومان است
2. دسته‌بندی‌های رایج: خانه، خواربار، رستوران و کافی‌شاپ، حمل و نقل، پوشاک، درمان و سلامت، آموزش، سرگرمی، موبایل و اینترنت، تعمیرات، هدیه، اقساط و وام، مالیات، سفر، حقوق، کسب و کار، سرمایه‌گذاری، اجاره، پروژه
3. برای تشخیص نوع (درآمد/هزینه) به کلمات کلیدی مثل: خرید، پرداخت، هزینه (expense) یا دریافت، حقوق، درآمد (income) توجه کن
4. اگر اطلاعاتی مشخص نیست، null بگذار

فقط JSON را برگردان، توضیح اضافی نده.
"""

        return prompt

    def _parse_response(self, response_text: str) -> Dict:
        """پارس کردن پاسخ JSON از Gemini"""
        try:
            # حذف کاراکترهای اضافی
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]

            return json.loads(response_text.strip())

        except json.JSONDecodeError as e:
            logger.error(f"خطا در پارس JSON: {e}")
            logger.error(f"Response text: {response_text}")
            return {"success": False, "error": "خطا در پارس پاسخ"}

    def _validate_and_complete(self, data: Dict, user_context: Dict = None) -> Dict:
        """اعتبارسنجی و تکمیل اطلاعات"""

        # بررسی نوع
        if data.get("type") not in ["transaction", "check", "query", "unknown"]:
            data["type"] = "unknown"

        # اگر نوع مشخص نیست
        if data["type"] == "unknown":
            data["success"] = False
            data["error"] = "نوع پیام تشخیص داده نشد"
            return data

        # برای تراکنش
        if data["type"] == "transaction":
            # بررسی مبلغ
            if not data.get("amount"):
                # تلاش برای استخراج مبلغ از متن اصلی
                amount = parse_amount(data.get("amount_text", ""))
                if amount:
                    data["amount"] = amount
                else:
                    data["success"] = False
                    data["error"] = "مبلغ مشخص نیست"
                    return data

            # تعیین نوع تراکنش اگر مشخص نیست
            if not data.get("transaction_type"):
                # بر اساس دسته‌بندی حدس بزن
                income_categories = [
                    "حقوق",
                    "کسب و کار",
                    "سرمایه‌گذاری",
                    "اجاره",
                    "پروژه",
                    "هدیه دریافتی",
                ]
                if data.get("category") in income_categories:
                    data["transaction_type"] = "income"
                else:
                    data["transaction_type"] = "expense"

            # انتخاب حساب پیش‌فرض اگر مشخص نیست
            if (
                not data.get("account_name")
                and user_context
                and user_context.get("accounts")
            ):
                # اگر بانک مشخص شده
                if data.get("bank_name"):
                    for acc in user_context["accounts"]:
                        if acc["bank_name"] == data["bank_name"]:
                            data["account_name"] = acc["account_name"]
                            data["account_id"] = acc["account_id"]
                            break
                else:
                    # اولین حساب به عنوان پیش‌فرض
                    data["account_name"] = user_context["accounts"][0]["account_name"]
                    data["account_id"] = user_context["accounts"][0]["account_id"]

            # تاریخ پیش‌فرض: امروز
            if not data.get("date"):
                data["date"] = datetime.now().strftime("%Y-%m-%d")

        # برای چک
        elif data["type"] == "check":
            # بررسی مبلغ
            if not data.get("amount"):
                data["success"] = False
                data["error"] = "مبلغ چک مشخص نیست"
                return data

            # بررسی تاریخ سررسید
            if not data.get("date"):
                data["success"] = False
                data["error"] = "تاریخ سررسید چک مشخص نیست"
                return data

            # نوع چک پیش‌فرض
            if not data.get("check_type"):
                data["check_type"] = "issued"

        data["success"] = True
        return data

    def analyze_financial_data(self, financial_data: Dict) -> Dict:
        """تحلیل هوشمند داده‌های مالی"""
        try:
            prompt = f"""
بر اساس داده‌های مالی زیر، یک تحلیل جامع ارائه بده:

درآمدها: {json.dumps(financial_data.get('incomes', {}), ensure_ascii=False)}
هزینه‌ها: {json.dumps(financial_data.get('expenses', {}), ensure_ascii=False)}
دوره زمانی: {financial_data.get('period', '')}

لطفاً تحلیل را به صورت JSON با ساختار زیر برگردان:

{{
    "strengths": ["نقاط قوت مدیریت مالی"],
    "weaknesses": ["نقاط ضعف و مشکلات"],
    "suggestions": ["پیشنهادات عملی برای بهبود"],
    "goals": ["اهداف پیشنهادی"],
    "savings_potential": عدد (پتانسیل پس‌انداز ماهانه),
    "risk_level": "low" یا "medium" یا "high"
}}

نکات:
- پیشنهادات باید عملی و قابل اجرا باشند
- به زبان فارسی و دوستانه بنویس
- اعداد را به ریال در نظر بگیر
"""

            response = self.model.generate_content(prompt)
            result = self._parse_response(response.text)

            if isinstance(result, dict) and not result.get("error"):
                result["success"] = True
                return result
            else:
                return {"success": False, "error": "خطا در تحلیل داده‌ها"}

        except Exception as e:
            logger.error(f"خطا در تحلیل مالی: {e}")
            return {"success": False, "error": "خطا در تحلیل هوشمند"}

    def suggest_category(
        self, description: str, transaction_type: str = "expense"
    ) -> str:
        """پیشنهاد دسته‌بندی بر اساس توضیحات"""
        try:
            categories = {
                "expense": [
                    "خانه",
                    "خواربار",
                    "رستوران و کافی‌شاپ",
                    "حمل و نقل",
                    "پوشاک",
                    "درمان و سلامت",
                    "آموزش",
                    "سرگرمی",
                    "موبایل و اینترنت",
                    "تعمیرات",
                    "هدیه",
                    "اقساط و وام",
                    "مالیات",
                    "سفر",
                    "سایر",
                ],
                "income": [
                    "حقوق",
                    "کسب و کار",
                    "سرمایه‌گذاری",
                    "اجاره",
                    "پروژه",
                    "هدیه",
                    "سایر",
                ],
            }

            prompt = f"""
برای این توضیحات: "{description}"
نوع تراکنش: {transaction_type}

مناسب‌ترین دسته‌بندی را از لیست زیر انتخاب کن و فقط نام دسته را برگردان:
{', '.join(categories[transaction_type])}
"""

            response = self.model.generate_content(prompt)
            category = response.text.strip().strip('"').strip("'")

            # بررسی معتبر بودن دسته
            if category in categories[transaction_type]:
                return category
            else:
                return "سایر"

        except Exception as e:
            logger.error(f"خطا در پیشنهاد دسته‌بندی: {e}")
            return "سایر"
