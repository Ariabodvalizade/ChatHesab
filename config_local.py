# config_local.py - Local testing configuration
import os
import sqlite3
from datetime import timedelta

# Telegram Bot Token (same as production)
BOT_TOKEN = "7625504738:AAG4uaKg2t9dH-iUi5e_NhBMgmM4aa-xt9g"

# Local SQLite Database Configuration
DB_CONFIG = {"database": "local_finance_bot.db", "check_same_thread": False}

# Use SQLite instead of MySQL for local testing
USE_SQLITE = True

# Google Gemini API (updated for chat functionality)
GEMINI_API_KEY = "AIzaSyCqZHAZBCnXxpwoFP0VChO66W-AFo8Mi04"
GEMINI_MODEL = "gemini-2.0-flash-exp"

# Trial and Subscription (same as production)
TRIAL_DAYS = 30
SUBSCRIPTION_PLANS = {
    "1_month": {"price": 50000, "days": 30, "label": "۱ ماهه - ۵۰ هزار تومان"},
    "2_months": {"price": 80000, "days": 60, "label": "۲ ماهه - ۸۰ هزار تومان"},
    "3_months": {"price": 100000, "days": 90, "label": "۳ ماهه - ۱۰۰ هزار تومان"},
    "6_months": {"price": 200000, "days": 180, "label": "۶ ماهه - ۲۰۰ هزار تومان"},
    "12_months": {"price": 250000, "days": 365, "label": "۱۲ ماهه - ۲۵۰ هزار تومان"},
}

# Payment Gateway (for future)
PAYMENT_GATEWAY = {
    "merchant_id": "",
    "callback_url": "",
}

# Categories (same as production)
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

# Amount shortcuts (same as production)
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

# Message Templates (same as production)
WELCOME_MESSAGE = """
🌟 به ربات حسابدار هوشمند خوش آمدید! (حالت تست محلی)

🔐 **نکته امنیتی مهم:**
تمامی اطلاعات شما کاملاً رمزنگاری شده و محافظت می‌شوند. این اطلاعات فقط در محیط امن تلگرام تبادل می‌شوند و هیچ‌کس، حتی تیم سازنده ربات، نمی‌تواند به اطلاعات محرمانه شما دسترسی داشته باشد.

حساب کاربری شما وابسته به همین آیدی تلگرامی است و امکان دسترسی با آیدی‌های دیگر وجود ندارد.

💎 شما از دوره آزمایشی رایگان ۳۰ روزه برخوردار هستید.

برای شروع، لطفاً اطلاعات حساب‌های بانکی خود را وارد کنید.

🧪 **در حال اجرا در حالت تست محلی**
"""

# Logging
LOG_LEVEL = "INFO"
LOG_FILE = "bot_local.log"
