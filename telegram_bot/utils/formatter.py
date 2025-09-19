# utils/formatter.py
from typing import List, Dict, Optional, Union
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from .persian_utils import format_amount, english_to_persian_digits
from .calendar_utils import get_persian_date_string
from datetime import date, datetime


def create_inline_keyboard(buttons: List[List[Dict[str, str]]]) -> InlineKeyboardMarkup:
    """ایجاد صفحه کلید inline

    Args:
        buttons: لیستی از ردیف‌ها، هر ردیف شامل دیکشنری‌هایی با 'text' و 'callback_data'
    """
    keyboard = []
    for row in buttons:
        keyboard_row = []
        for button in row:
            keyboard_row.append(
                InlineKeyboardButton(
                    text=button["text"], callback_data=button["callback_data"]
                )
            )
        keyboard.append(keyboard_row)

    return InlineKeyboardMarkup(keyboard)


def format_transaction_message(transaction_data: Dict) -> str:
    """قالب‌بندی پیام تراکنش برای نمایش"""
    msg = "📊 **جزئیات تراکنش:**\n\n"

    # نوع تراکنش
    if transaction_data["type"] == "expense":
        msg += "🔴 **نوع:** هزینه\n"
    else:
        msg += "🟢 **نوع:** درآمد\n"

    # مبلغ
    msg += f"💰 **مبلغ:** {format_amount(transaction_data['amount'])}\n"

    # دسته‌بندی
    msg += f"📁 **دسته‌بندی:** {transaction_data['category']}\n"

    # حساب
    msg += f"🏦 **حساب:** {transaction_data['account_name']}\n"

    # توضیحات
    if transaction_data.get("description"):
        msg += f"📝 **توضیحات:** {transaction_data['description']}\n"

    # تاریخ
    if transaction_data.get("date"):
        date_str = get_persian_date_string(transaction_data["date"])
        msg += f"📅 **تاریخ:** {date_str}\n"

    return msg


def format_account_summary(accounts: List[Dict]) -> str:
    """قالب‌بندی خلاصه حساب‌ها"""
    if not accounts:
        return "❌ هیچ حسابی ثبت نشده است."

    msg = "🏦 **وضعیت حساب‌های شما:**\n\n"

    total_balance = 0
    for account in accounts:
        balance = account["current_balance"]
        total_balance += balance

        # ایموجی بر اساس وضعیت موجودی
        if balance > 0:
            emoji = "💚"
        elif balance < 0:
            emoji = "💔"
        else:
            emoji = "💛"

        msg += f"{emoji} **{account['account_name']}**\n"
        msg += f"   💰 موجودی: {format_amount(balance)}\n\n"

    # مجموع کل
    msg += "➖➖➖➖➖➖➖➖➖\n"
    if total_balance > 0:
        total_emoji = "✅"
    elif total_balance < 0:
        total_emoji = "⚠️"
    else:
        total_emoji = "ℹ️"

    msg += f"{total_emoji} **مجموع کل:** {format_amount(total_balance)}"

    return msg


def format_check_reminder(checks: List[Dict]) -> str:
    """قالب‌بندی یادآوری چک‌ها"""
    if not checks:
        return "✅ چک سررسید شده‌ای ندارید."

    msg = "📋 **چک‌های سررسید نزدیک:**\n\n"

    for check in checks:
        # نوع چک
        if check["type"] == "issued":
            msg += "🔴 **چک صادره**\n"
        else:
            msg += "🟢 **چک دریافتی**\n"

        # مبلغ و تاریخ
        msg += f"💰 مبلغ: {format_amount(check['amount'])}\n"
        msg += f"📅 سررسید: {get_persian_date_string(check['due_date'])}\n"

        # طرف حساب
        if check.get("recipient_issuer"):
            msg += f"👤 {check['recipient_issuer']}\n"

        msg += "\n"

    return msg


def format_report_summary(data: Dict) -> str:
    """قالب‌بندی گزارش خلاصه مالی"""
    msg = f"📊 **گزارش مالی**\n"
    msg += f"📅 {data['period_name']}\n\n"

    # درآمدها
    msg += "💚 **درآمدها:**\n"
    total_income = 0
    for category, amount in data["incomes"].items():
        if amount > 0:
            msg += f"   • {category}: {format_amount(amount)}\n"
            total_income += amount

    if total_income == 0:
        msg += "   ندارید\n"
    else:
        msg += f"   **مجموع:** {format_amount(total_income)}\n"

    msg += "\n"

    # هزینه‌ها
    msg += "💔 **هزینه‌ها:**\n"
    total_expense = 0
    for category, amount in data["expenses"].items():
        if amount > 0:
            msg += f"   • {category}: {format_amount(amount)}\n"
            total_expense += amount

    if total_expense == 0:
        msg += "   ندارید\n"
    else:
        msg += f"   **مجموع:** {format_amount(total_expense)}\n"

    msg += "\n➖➖➖➖➖➖➖➖➖\n"

    # خلاصه
    balance = total_income - total_expense
    if balance > 0:
        emoji = "✅"
        status = "مثبت"
    elif balance < 0:
        emoji = "⚠️"
        status = "منفی"
    else:
        emoji = "ℹ️"
        status = "صفر"

    msg += f"{emoji} **تراز:** {format_amount(abs(balance))} {status}\n"

    # نسبت‌ها
    if total_income > 0:
        savings_rate = ((total_income - total_expense) / total_income) * 100
        msg += (
            f"💎 **نرخ پس‌انداز:** {english_to_persian_digits(f'{savings_rate:.1f}')}٪\n"
        )

    return msg


def format_ai_analysis(analysis: Dict) -> str:
    """قالب‌بندی تحلیل هوش مصنوعی"""
    msg = "🤖 **تحلیل هوشمند مالی:**\n\n"

    # نقاط قوت
    if analysis.get("strengths"):
        msg += "✅ **نقاط قوت:**\n"
        for point in analysis["strengths"]:
            msg += f"   • {point}\n"
        msg += "\n"

    # نقاط ضعف
    if analysis.get("weaknesses"):
        msg += "⚠️ **نقاط قابل بهبود:**\n"
        for point in analysis["weaknesses"]:
            msg += f"   • {point}\n"
        msg += "\n"

    # پیشنهادات
    if analysis.get("suggestions"):
        msg += "💡 **پیشنهادات:**\n"
        for suggestion in analysis["suggestions"]:
            msg += f"   • {suggestion}\n"
        msg += "\n"

    # اهداف
    if analysis.get("goals"):
        msg += "🎯 **اهداف پیشنهادی:**\n"
        for goal in analysis["goals"]:
            msg += f"   • {goal}\n"

    return msg


def format_subscription_status(user_data: Dict) -> str:
    """قالب‌بندی وضعیت اشتراک"""
    msg = "💳 **وضعیت اشتراک:**\n\n"

    if user_data.get("is_trial"):
        remaining_days = user_data["trial_remaining_days"]
        msg += f"🎁 **دوره آزمایشی رایگان**\n"
        msg += f"⏳ {english_to_persian_digits(str(remaining_days))} روز باقی‌مانده\n"

    elif user_data.get("is_active"):
        end_date = get_persian_date_string(user_data["subscription_end_date"])
        msg += f"✅ **اشتراک فعال**\n"
        msg += f"📅 تا تاریخ: {end_date}\n"

    else:
        msg += "❌ **اشتراک غیرفعال**\n"
        msg += "لطفاً برای ادامه استفاده، اشتراک خود را تمدید کنید.\n"

    return msg


def format_error_message(error_type: str = "general") -> str:
    """قالب‌بندی پیام‌های خطا"""
    errors = {
        "general": "❌ متأسفانه خطایی رخ داد. لطفاً دوباره تلاش کنید.",
        "invalid_amount": "❌ مبلغ وارد شده نامعتبر است. لطفاً یک عدد صحیح وارد کنید.",
        "invalid_date": "❌ تاریخ وارد شده نامعتبر است.",
        "no_account": "❌ ابتدا باید حساب‌های بانکی خود را ثبت کنید.",
        "insufficient_balance": "❌ موجودی حساب کافی نیست.",
        "ai_error": "❌ خطا در پردازش هوش مصنوعی. لطفاً پیام را واضح‌تر بنویسید.",
        "subscription_expired": "❌ اشتراک شما منقضی شده است. لطفاً تمدید کنید.",
        "database_error": "❌ خطا در ذخیره اطلاعات. لطفاً مجدداً تلاش کنید.",
    }

    return errors.get(error_type, errors["general"])


def format_success_message(action_type: str) -> str:
    """قالب‌بندی پیام‌های موفقیت"""
    messages = {
        "transaction_saved": "✅ تراکنش با موفقیت ثبت شد!",
        "account_added": "✅ حساب بانکی با موفقیت اضافه شد!",
        "account_updated": "✅ اطلاعات حساب با موفقیت به‌روزرسانی شد!",
        "check_saved": "✅ چک با موفقیت ثبت شد!",
        "plan_created": "✅ طرح پس‌انداز با موفقیت ایجاد شد!",
        "subscription_renewed": "✅ اشتراک با موفقیت تمدید شد!",
        "settings_updated": "✅ تنظیمات با موفقیت ذخیره شد!",
    }

    return messages.get(action_type, "✅ عملیات با موفقیت انجام شد!")


def format_confirmation_message(data: Dict) -> str:
    """قالب‌بندی پیام تأیید برای کاربر"""
    msg = "❓ **لطفاً اطلاعات زیر را تأیید کنید:**\n\n"

    # بر اساس نوع داده
    if data.get("type") == "transaction":
        if data["transaction_type"] == "expense":
            msg += "🔴 **هزینه**\n"
        else:
            msg += "🟢 **درآمد**\n"

        msg += f"💰 **مبلغ:** {format_amount(data['amount'])}\n"
        msg += f"📁 **دسته:** {data['category']}\n"
        msg += f"🏦 **از حساب:** {data['account']}\n"

        if data.get("description"):
            msg += f"📝 **توضیحات:** {data['description']}\n"

    elif data.get("type") == "check":
        if data["check_type"] == "issued":
            msg += "🔴 **چک صادره**\n"
        else:
            msg += "🟢 **چک دریافتی**\n"

        msg += f"💰 **مبلغ:** {format_amount(data['amount'])}\n"
        msg += f"📅 **سررسید:** {get_persian_date_string(data['due_date'])}\n"
        msg += f"🏦 **از حساب:** {data['account']}\n"

        if data.get("recipient"):
            msg += f"👤 **گیرنده:** {data['recipient']}\n"

    msg += "\n✅ برای تأیید روی دکمه «تأیید» کلیک کنید."
    msg += "\n❌ برای لغو روی دکمه «لغو» کلیک کنید."

    return msg


def create_main_menu() -> str:
    """ایجاد منوی اصلی"""
    menu = """
🏠 **منوی اصلی**

لطفاً یکی از گزینه‌های زیر را انتخاب کنید:

💳 /accounts - مدیریت حساب‌ها
💰 /transaction - ثبت تراکنش جدید
📊 /report - گزارش‌گیری
📋 /checks - مدیریت چک‌ها
💎 /savings - طرح‌های پس‌انداز
⚙️ /settings - تنظیمات
❓ /help - راهنما

یا می‌توانید مستقیماً پیام خود را بنویسید:
مثلاً: «۲۵۰ تومن قهوه خریدم از ملت»
"""
    return menu


def create_help_message() -> str:
    """ایجاد پیام راهنما"""
    help_text = """
📚 **راهنمای استفاده از ربات**

🔸 **ثبت سریع تراکنش:**
کافیست پیام خود را به صورت طبیعی بنویسید:
• «۱۵۰ تومن نهار خوردم»
• «حقوق ۵ میلیون گرفتم»
• «۸۹۰ هزار تومان قسط وام دادم»

🔸 **مدیریت حساب‌ها:**
از دستور /accounts برای:
• افزودن حساب جدید
• ویرایش موجودی
• مشاهده وضعیت حساب‌ها

🔸 **گزارش‌گیری:**
با /report می‌توانید:
• گزارش روزانه تا سالانه
• تحلیل هوشمند مالی
• نمودار هزینه و درآمد

🔸 **چک‌ها:**
دستور /checks برای:
• ثبت چک جدید
• یادآوری سررسید
• مشاهده چک‌های فعال

🔸 **نکات:**
• اعداد فارسی و انگلیسی هر دو پشتیبانی می‌شوند
• می‌توانید پیام صوتی هم بفرستید
• برای حذف سه صفر از مبالغ کافیست «تومن» بنویسید

💡 **مثال‌های بیشتر:**
• «از حساب سینا ۲ میلیون و ۳۵۰ هزار تومان برداشت کردم»
• «چک ۵ میلیونی برای ۱۵ مرداد دادم»
• «درآمد پروژه سایت ۸ میلیون»

❓ سوالی دارید؟ @your_support_id
"""
    return help_text
