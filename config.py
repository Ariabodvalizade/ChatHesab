# config.py
import os
from datetime import timedelta

# Telegram Bot Token
BOT_TOKEN = "7625504738:AAG4uaKg2t9dH-iUi5e_NhBMgmM4aa-xt9g"

# Database Configuration
DB_CONFIG = {
    "host": "localhost",
    "user": "moshaver_financebotuser",
    "password": "Apple09366864544",
    "database": "moshaver_finance_bot",
    "charset": "utf8mb4",
    "collation": "utf8mb4_unicode_ci",
}

# Google Gemini API
GEMINI_API_KEY = "AIzaSyBHJFbODPcml9MCXaxWY5F8RBto08QuGVY"
GEMINI_MODEL = "gemini-2.0-flash-exp"

# Trial and Subscription
TRIAL_DAYS = 30
SUBSCRIPTION_PLANS = {
    "1_month": {"price": 50000, "days": 30, "label": "۱ ماهه - ۵۰ هزار تومان"},
    "2_months": {"price": 80000, "days": 60, "label": "۲ ماهه - ۸۰ هزار تومان"},
    "3_months": {"price": 100000, "days": 90, "label": "۳ ماهه - ۱۰۰ هزار تومان"},
    "6_months": {"price": 200000, "days": 180, "label": "۶ ماهه - ۲۰۰ هزار تومان"},
    "12_months": {"price": 250000, "days": 365, "label": "۱۲ ماهه - ۲۵۰ هزار تومان"},
}

# Payment Gateway (برای آینده)
PAYMENT_GATEWAY = {
    "merchant_id": "",  # باید از درگاه پرداخت دریافت شود
    "callback_url": "",
}

# Categories
EXPENSE_CATEGORIES = {
    "home": {"name": "خانه", "icon": "🏠"},
    "grocery": {"name": "خواربار", "icon": "🛒"},
    "restaurant": {"name": "رستوران و کافی‌شاپ", "icon": "🍔"},
    "transport": {"name": "حمل و نقل", "icon": "🚗"},
    "clothing": {"name": "پوشاک", "icon": "👕"},
    "health": {"name": "درمان و سلامت", "icon": "🏥"},
    "education": {"name": "آموزش", "icon": "📚"},
    "entertainment": {"name": "سرگرمی", "icon": "🎮"},
    "communication": {"name": "موبایل و اینترنت", "icon": "📱"},
    "maintenance": {"name": "تعمیرات", "icon": "🔧"},
    "gift": {"name": "هدیه", "icon": "🎁"},
    "loan": {"name": "اقساط و وام", "icon": "💳"},
    "tax": {"name": "مالیات", "icon": "🏢"},
    "travel": {"name": "سفر", "icon": "✈️"},
    "other": {"name": "سایر", "icon": "💰"},
}

INCOME_CATEGORIES = {
    "salary": {"name": "حقوق", "icon": "💼"},
    "business": {"name": "کسب و کار", "icon": "🏪"},
    "investment": {"name": "سرمایه‌گذاری", "icon": "💹"},
    "rent": {"name": "اجاره", "icon": "🏠"},
    "project": {"name": "پروژه", "icon": "🎯"},
    "gift": {"name": "هدیه", "icon": "🎁"},
    "other": {"name": "سایر", "icon": "💸"},
}

# Common amount shortcuts in Iran
AMOUNT_SHORTCUTS = {
    "تومن": 1,
    "تومان": 1,
    "هزار": 1000,
    "هزارتومان": 1000,
    "هزار تومان": 1000,
    "میلیون": 1000000,
    "میلیون تومان": 1000000,
    "میلیارد": 1000000000,
}

# Message Templates
WELCOME_MESSAGE = """
🌟 به ربات حسابدار هوشمند خوش آمدید!

🔐 **نکته امنیتی مهم:**
تمامی اطلاعات شما کاملاً رمزنگاری شده و محافظت می‌شوند. این اطلاعات فقط در محیط امن تلگرام تبادل می‌شوند و هیچ‌کس، حتی تیم سازنده ربات، نمی‌تواند به اطلاعات محرمانه شما دسترسی داشته باشد.

حساب کاربری شما وابسته به همین آیدی تلگرامی است و امکان دسترسی با آیدی‌های دیگر وجود ندارد.

💎 شما از دوره آزمایشی رایگان ۳۰ روزه برخوردار هستید.

برای شروع، لطفاً اطلاعات حساب‌های بانکی خود را وارد کنید.
"""

# Logging
LOG_LEVEL = "INFO"
LOG_FILE = "bot.log"
