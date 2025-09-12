# web_config.py
"""
Configuration for web API with local SQLite database
"""

import os
from datetime import datetime, timedelta

# Database configuration for local development
DB_CONFIG = {
    "database": "finance_web_app.db",
    "check_same_thread": False,  # Allow multi-threaded access for web API
}

# Bot configuration
BOT_TOKEN = "demo_token_for_web"
WELCOME_MESSAGE = """
🎉 **خوش آمدید به دستیار مالی هوشمند!**

این ربات به شما کمک می‌کند تا:
💰 مدیریت درآمد و هزینه‌ها
📊 تولید گزارش‌های مالی
📈 برنامه‌ریزی پس‌انداز
🔔 یادآوری‌های مالی

از دستور /help برای راهنمای کامل استفاده کنید.
"""

# Subscription plans (for demo)
SUBSCRIPTION_PLANS = {
    "monthly": {
        "label": "📅 اشتراک یک ماهه - 50,000 تومان",
        "price": 50000,
        "duration_days": 30,
        "description": "دسترسی کامل به تمام امکانات برای یک ماه",
    },
    "yearly": {
        "label": "📅 اشتراک سالانه - 500,000 تومان",
        "price": 500000,
        "duration_days": 365,
        "description": "دسترسی کامل به تمام امکانات برای یک سال (2 ماه رایگان!)",
    },
}

# AI configuration (demo mode)
GOOGLE_API_KEY = "demo_key"  # For local testing without actual AI

# Voice processing
VOICE_ENABLED = False  # Disable for web demo initially

# Trial period
TRIAL_DAYS = 7


def get_trial_end_date():
    """محاسبه تاریخ پایان دوره آزمایشی"""
    return datetime.now() + timedelta(days=TRIAL_DAYS)
