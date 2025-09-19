# main_local.py - Local testing version
import logging
import sys
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
)

# تنظیمات لاگ
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler("bot_local.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

# واردات ماژول‌ها - نسخه محلی
from .config_local import BOT_TOKEN, WELCOME_MESSAGE
from .database.connection_local import init_local_database, get_local_db

# ایجاد کلاس‌های محلی برای تست
class LocalUserManager:
    def __init__(self):
        self.db = get_local_db()

    def create_user(self, telegram_id: int, username: str = None, first_name: str = None, last_name: str = None):
        try:
            # بررسی وجود کاربر
            existing = self.get_user_by_telegram_id(telegram_id)
            if existing:
                return existing["user_id"]

            # محاسبه تاریخ پایان دوره آزمایشی
            from datetime import datetime, timedelta
            from .config_local import TRIAL_DAYS
            trial_end = datetime.now() + timedelta(days=TRIAL_DAYS)

            query = """
                INSERT INTO users (telegram_id, username, first_name, last_name, 
                                 registration_date, trial_end_date, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """

            params = (
                telegram_id,
                username,
                first_name,
                last_name,
                datetime.now(),
                trial_end,
                True,
            )

            user_id = self.db.execute_query(query, params)
            logger.info(f"کاربر جدید ایجاد شد: {user_id}")
            return user_id

        except Exception as e:
            logger.error(f"خطا در ایجاد کاربر: {e}")
            return None

    def get_user_by_telegram_id(self, telegram_id: int):
        query = """
            SELECT user_id, telegram_id, username, first_name, last_name,
                   registration_date, trial_end_date, subscription_end_date, is_active
            FROM users
            WHERE telegram_id = ?
        """
        return self.db.execute_query(query, (telegram_id,), fetch_one=True)

    def check_subscription_status(self, user_id: int):
        from datetime import datetime
        user = self.db.execute_query("SELECT * FROM users WHERE user_id = ?", (user_id,), fetch_one=True)
        if not user:
            return {"is_active": False, "is_trial": False}

        now = datetime.now()
        result = {
            "is_active": True,  # برای تست همیشه فعال
            "is_trial": True,
            "is_expired": False,
            "days_remaining": 30,
        }
        return result


class LocalAccountManager:
    def __init__(self):
        self.db = get_local_db()

    def get_user_accounts(self, user_id: int):
        query = """
            SELECT account_id, user_id, bank_name, account_name, 
                   initial_balance, current_balance, is_active
            FROM bank_accounts
            WHERE user_id = ? AND is_active = 1
        """
        return self.db.execute_query(query, (user_id,), fetch_all=True)

    def create_account(self, user_id: int, bank_name: str, account_name: str, initial_balance: float):
        try:
            query = """
                INSERT INTO bank_accounts (user_id, bank_name, account_name, 
                                         initial_balance, current_balance, is_active)
                VALUES (?, ?, ?, ?, ?, ?)
            """
            params = (user_id, bank_name, account_name, initial_balance, initial_balance, True)
            account_id = self.db.execute_query(query, params)
            logger.info(f"حساب جدید ایجاد شد: {account_id}")
            return account_id
        except Exception as e:
            logger.error(f"خطا در ایجاد حساب: {e}")
            return None


class LocalTransactionHandler:
    def __init__(self):
        self.db = get_local_db()

    def create_transaction(self, user_id: int, account_id: int, transaction_type: str, 
                          amount: float, category: str, description: str = None, transaction_date: str = None):
        try:
            from datetime import datetime
            if not transaction_date:
                transaction_date = datetime.now()
            
            query = """
                INSERT INTO transactions (user_id, account_id, type, amount, category, 
                                        description, transaction_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            params = (user_id, account_id, transaction_type, amount, category, description, transaction_date)
            transaction_id = self.db.execute_query(query, params)
            logger.info(f"تراکنش جدید ایجاد شد: {transaction_id}")
            return transaction_id
        except Exception as e:
            logger.error(f"خطا در ایجاد تراکنش: {e}")
            return None


class LocalAIProcessor:
    def __init__(self):
        pass

    def process_message(self, message: str, user_context: dict = None):
        # پردازش ساده برای تست
        logger.info(f"پردازش پیام: {message}")
        
        # تشخیص ساده مبلغ
        import re
        
        # جستجوی عدد در متن
        numbers = re.findall(r'\d+', message)
        if not numbers:
            return {"success": False, "error": "مبلغ مشخص نیست"}
        
        amount = int(numbers[0])
        if amount < 1000:  # احتمالاً هزار تومان
            amount *= 1000
        
        # تشخیص ساده نوع تراکنش
        expense_keywords = ["خرید", "پرداخت", "هزینه", "خریدم", "دادم"]
        income_keywords = ["دریافت", "حقوق", "درآمد", "گرفتم"]
        
        transaction_type = "expense"  # پیش‌فرض
        for keyword in income_keywords:
            if keyword in message:
                transaction_type = "income"
                break
        
        # دسته‌بندی ساده
        category = "سایر"
        if "غذا" in message or "رستوران" in message:
            category = "رستوران و کافی‌شاپ"
        elif "بنزین" in message or "تاکسی" in message:
            category = "حمل و نقل"
        elif "خرید" in message:
            category = "خواربار"
        
        # انتخاب حساب پیش‌فرض
        account_id = None
        account_name = None
        if user_context and user_context.get("accounts"):
            account = user_context["accounts"][0]
            account_id = account["account_id"]
            account_name = account["account_name"]
        
        return {
            "success": True,
            "type": "transaction",
            "transaction_type": transaction_type,
            "amount": amount,
            "category": category,
            "description": message,
            "account_id": account_id,
            "account_name": account_name,
            "date": None
        }


# سایر کلاس‌های خالی برای تست
class LocalCheckManager:
    def __init__(self):
        pass

class LocalReportGenerator:
    def __init__(self):
        pass

class LocalSavingsManager:
    def __init__(self):
        pass

class LocalSubscriptionManager:
    def __init__(self):
        pass

class LocalVoiceHandler:
    def __init__(self):
        pass

# مراحل مکالمه
(
    ACCOUNT_BANK_NAME,
    ACCOUNT_NAME,
    ACCOUNT_BALANCE,
    CONFIRM_TRANSACTION,
    EDIT_AMOUNT,
    CHECK_AMOUNT,
    CHECK_DATE,
    CHECK_RECIPIENT,
    SUBSCRIPTION_PLAN,
) = range(9)


class LocalFinanceBot:
    def __init__(self):
        self.user_manager = LocalUserManager()
        self.account_manager = LocalAccountManager()
        self.transaction_handler = LocalTransactionHandler()
        self.ai_processor = LocalAIProcessor()
        self.check_manager = LocalCheckManager()
        self.report_generator = LocalReportGenerator()
        self.savings_manager = LocalSavingsManager()
        self.subscription_manager = LocalSubscriptionManager()
        self.voice_handler = LocalVoiceHandler()

    async def start(self, update: Update, context):
        """دستور /start"""
        user = update.effective_user
        
        print(f"🔄 کاربر {user.first_name} ({user.id}) شروع کرد")
        
        # ایجاد یا دریافت کاربر
        user_id = self.user_manager.create_user(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
        )

        if user_id:
            context.user_data["user_id"] = user_id
            print(f"✅ کاربر ثبت شد با ID: {user_id}")

            # ارسال پیام خوش‌آمدگویی
            await update.message.reply_text(WELCOME_MESSAGE, parse_mode="Markdown")

            # نمایش منوی ساده
            menu_text = """
🏠 **منوی اصلی**

شما می‌توانید:
• تراکنش‌های خود را به صورت متنی بنویسید (مثل: "50 هزار تومان برای خرید نان دادم")
• از دستور /accounts برای مدیریت حساب‌ها استفاده کنید
• از دستور /help برای راهنمایی استفاده کنید

**نمونه پیام‌ها:**
- "100 هزار تومان حقوق گرفتم"
- "25 هزار تومان برای بنزین دادم"
- "50 هزار تومان غذا خریدم"
            """
            
            await update.message.reply_text(menu_text, parse_mode="Markdown")

            # اگر حساب ندارد، شروع فرآیند ثبت حساب
            accounts = self.account_manager.get_user_accounts(user_id)
            if not accounts:
                await update.message.reply_text(
                    "برای شروع، لطفاً اولین حساب بانکی خود را ثبت کنید.\n"
                    "نام بانک را وارد کنید (مثلاً: ملت، ملی، صادرات):",
                    parse_mode="Markdown",
                )
                return ACCOUNT_BANK_NAME
        else:
            await update.message.reply_text("❌ خطا در ثبت کاربر")

        return ConversationHandler.END

    async def help_command(self, update: Update, context):
        """دستور /help"""
        help_text = """
🤖 **راهنمای ربات حسابدار (نسخه تست)**

**دستورات:**
• /start - شروع کار با ربات
• /accounts - مدیریت حساب‌های بانکی
• /help - نمایش این راهنما

**نحوه استفاده:**
1️⃣ ابتدا حساب بانکی خود را ثبت کنید
2️⃣ تراکنش‌هایتان را به صورت متن بنویسید
3️⃣ ربات به صورت هوشمند آن‌ها را پردازش می‌کند

**نمونه‌های پیام:**
• "50 هزار تومان نان خریدم"
• "200 هزار تومان حقوق گرفتم"
• "30 هزار تومان بنزین زدم"

**ویژگی‌های تست:**
✅ ثبت حساب‌های بانکی
✅ پردازش تراکنش‌های ساده
✅ ذخیره‌سازی محلی با SQLite
⚠️ برخی ویژگی‌ها در حالت تست محدود هستند
        """
        await update.message.reply_text(help_text, parse_mode="Markdown")

    async def accounts_command(self, update: Update, context):
        """دستور /accounts - مدیریت حساب‌ها"""
        user_id = context.user_data.get("user_id")
        if not user_id:
            await update.message.reply_text("لطفاً ابتدا /start را بزنید.")
            return

        # دکمه‌های مدیریت حساب
        keyboard = [
            [
                InlineKeyboardButton("➕ افزودن حساب جدید", callback_data="add_account"),
                InlineKeyboardButton("📋 لیست حساب‌ها", callback_data="list_accounts"),
            ],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")],
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "🏦 **مدیریت حساب‌های بانکی**\n\n" "یک گزینه را انتخاب کنید:",
            parse_mode="Markdown",
            reply_markup=reply_markup,
        )

    async def handle_message(self, update: Update, context):
        """پردازش پیام‌های عادی کاربر"""
        user_id = context.user_data.get("user_id")
        if not user_id:
            await update.message.reply_text("لطفاً ابتدا /start را بزنید.")
            return

        print(f"💬 پیام از کاربر {user_id}: {update.message.text}")

        # دریافت لیست حساب‌های کاربر
        accounts = self.account_manager.get_user_accounts(user_id)
        if not accounts:
            await update.message.reply_text(
                "❌ ابتدا باید حساب‌های بانکی خود را ثبت کنید.\n"
                "از دستور /accounts استفاده کنید."
            )
            return

        # پردازش پیام
        message_text = update.message.text
        await update.message.reply_text("🤖 در حال پردازش پیام شما...")

        # آماده‌سازی context برای AI
        user_context = {"accounts": accounts}

        # پردازش با AI
        result = self.ai_processor.process_message(message_text, user_context)
        
        print(f"🧠 نتیجه پردازش: {result}")

        if not result.get("success"):
            await update.message.reply_text("❌ متوانستم پیام شما را پردازش کنم.")
            return

        # ذخیره نتیجه در context
        context.user_data["ai_result"] = result

        # نمایش نتیجه و درخواست تأیید
        if result["type"] == "transaction":
            await self.show_transaction_confirmation(update, context, result)
        else:
            await update.message.reply_text("❌ نوع پیام پشتیبانی نمی‌شود.")

    async def show_transaction_confirmation(self, update: Update, context, data):
        """نمایش تأیید تراکنش"""
        # آماده‌سازی پیام تأیید
        if data["transaction_type"] == "expense":
            msg = "🔴 **ثبت هزینه**\n\n"
        else:
            msg = "🟢 **ثبت درآمد**\n\n"

        msg += f"💰 **مبلغ:** {data['amount']:,} تومان\n"

        if data.get("category"):
            msg += f"📁 **دسته‌بندی:** {data['category']}\n"

        if data.get("account_name"):
            msg += f"🏦 **حساب:** {data['account_name']}\n"

        if data.get("description"):
            msg += f"📝 **توضیحات:** {data['description']}\n"

        msg += "\n✅ آیا اطلاعات فوق صحیح است؟"

        # دکمه‌های تأیید
        keyboard = [
            [
                InlineKeyboardButton("✅ تأیید", callback_data="confirm_transaction"),
                InlineKeyboardButton("❌ لغو", callback_data="cancel"),
            ],
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            msg, parse_mode="Markdown", reply_markup=reply_markup
        )

    async def handle_callback(self, update: Update, context):
        """پردازش callback های دکمه‌ها"""
        query = update.callback_query
        await query.answer()

        data = query.data
        user_id = context.user_data.get("user_id")

        print(f"🔘 Callback: {data} از کاربر {user_id}")

        if data == "main_menu":
            menu_text = """
🏠 **منوی اصلی**

برای ثبت تراکنش، پیام خود را بنویسید.
مثال: "50 هزار تومان نان خریدم"
            """
            await query.edit_message_text(menu_text, parse_mode="Markdown")

        elif data == "confirm_transaction":
            await self.save_transaction(update, context)

        elif data == "cancel":
            await query.edit_message_text("❌ عملیات لغو شد.")
            context.user_data.pop("ai_result", None)

        elif data == "add_account":
            await query.edit_message_text(
                "🏦 **افزودن حساب جدید**\n\n"
                "نام بانک را وارد کنید (مثلاً: ملت، ملی، صادرات):",
                parse_mode="Markdown",
            )
            return ACCOUNT_BANK_NAME

        elif data == "list_accounts":
            await self.show_accounts_list(update, context)

    async def save_transaction(self, update: Update, context):
        """ذخیره تراکنش تأیید شده"""
        query = update.callback_query
        user_id = context.user_data.get("user_id")
        ai_result = context.user_data.get("ai_result")

        if not ai_result:
            await query.edit_message_text("❌ خطا در دریافت اطلاعات")
            return

        print(f"💾 ذخیره تراکنش: {ai_result}")

        # ذخیره تراکنش
        success = self.transaction_handler.create_transaction(
            user_id=user_id,
            account_id=ai_result.get("account_id"),
            transaction_type=ai_result["transaction_type"],
            amount=ai_result["amount"],
            category=ai_result.get("category", "سایر"),
            description=ai_result.get("description"),
            transaction_date=ai_result.get("date"),
        )

        if success:
            await query.edit_message_text(
                "✅ تراکنش با موفقیت ثبت شد!\n\n"
                "برای ثبت تراکنش بعدی، پیام جدید بفرستید.",
                parse_mode="Markdown"
            )
            print(f"✅ تراکنش {success} ذخیره شد")
        else:
            await query.edit_message_text("❌ خطا در ذخیره تراکنش")

        # پاک کردن داده‌های موقت
        context.user_data.pop("ai_result", None)

    async def show_accounts_list(self, update: Update, context):
        """نمایش لیست حساب‌ها"""
        query = update.callback_query
        user_id = context.user_data.get("user_id")

        accounts = self.account_manager.get_user_accounts(user_id)

        if not accounts:
            await query.edit_message_text(
                "❌ هیچ حسابی ثبت نشده است.", parse_mode="Markdown"
            )
        else:
            msg = "🏦 **حساب‌های شما:**\n\n"
            for acc in accounts:
                msg += f"• {acc['bank_name']} - {acc['account_name']}\n"
                msg += f"  💰 موجودی: {acc['current_balance']:,} تومان\n\n"
            
            await query.edit_message_text(msg, parse_mode="Markdown")

    # هندلرهای ConversationHandler برای ثبت حساب
    async def get_bank_name(self, update: Update, context):
        """دریافت نام بانک"""
        bank_name = update.message.text.strip()
        context.user_data["new_account_bank"] = bank_name
        
        print(f"🏦 نام بانک: {bank_name}")

        await update.message.reply_text(
            "نام حساب را وارد کنید\n"
            "(مثلاً: حساب اصلی، پس‌انداز، جاری، یا 4 رقم آخر کارت):"
        )
        return ACCOUNT_NAME

    async def get_account_name(self, update: Update, context):
        """دریافت نام حساب"""
        account_name = update.message.text.strip()
        context.user_data["new_account_name"] = account_name
        
        print(f"📝 نام حساب: {account_name}")

        await update.message.reply_text(
            "موجودی اولیه حساب را وارد کنید (به تومان):\n" "مثلاً: 5000000 یا 5 میلیون"
        )
        return ACCOUNT_BALANCE

    async def get_account_balance(self, update: Update, context):
        """دریافت موجودی اولیه"""
        balance_text = update.message.text
        
        # پارس ساده مبلغ
        import re
        numbers = re.findall(r'\d+', balance_text)
        if not numbers:
            await update.message.reply_text(
                "❌ مبلغ نامعتبر است. لطفاً دوباره وارد کنید:"
            )
            return ACCOUNT_BALANCE
        
        balance = int(numbers[0])
        if balance < 1000:  # احتمالاً میلیون
            balance *= 1000000
        elif balance < 1000000:  # احتمالاً هزار
            balance *= 1000

        print(f"💰 موجودی: {balance}")

        # ذخیره حساب
        user_id = context.user_data.get("user_id")
        bank_name = context.user_data.get("new_account_bank")
        account_name = context.user_data.get("new_account_name")

        account_id = self.account_manager.create_account(
            user_id=user_id,
            bank_name=bank_name,
            account_name=account_name,
            initial_balance=balance,
        )

        if account_id:
            await update.message.reply_text(
                f"✅ حساب {account_name} در {bank_name} با موفقیت ثبت شد!\n\n"
                f"موجودی اولیه: {balance:,} تومان\n\n"
                "حالا می‌توانید تراکنش‌هایتان را ثبت کنید.",
                parse_mode="Markdown",
            )
            print(f"✅ حساب {account_id} ایجاد شد")
        else:
            await update.message.reply_text("❌ خطا در ثبت حساب")

        # پاک کردن داده‌های موقت
        context.user_data.pop("new_account_bank", None)
        context.user_data.pop("new_account_name", None)

        return ConversationHandler.END

    async def cancel(self, update: Update, context):
        """لغو عملیات"""
        await update.message.reply_text("❌ عملیات لغو شد.", parse_mode="Markdown")
        return ConversationHandler.END


def main():
    """تابع اصلی اجرای ربات محلی"""
    print("🚀 شروع ربات محلی...")
    
    # راه‌اندازی دیتابیس محلی
    try:
        init_local_database()
        print("✅ دیتابیس محلی آماده شد")
    except Exception as e:
        print(f"❌ خطا در راه‌اندازی دیتابیس: {e}")
        return

    # ایجاد نمونه از ربات
    bot = LocalFinanceBot()

    # ایجاد Application
    application = Application.builder().token(BOT_TOKEN).build()

    # ConversationHandler برای ثبت حساب
    async def add_account_callback(update, context):
        return update.callback_query.data == "add_account"
    
    account_conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(add_account_callback),
            CommandHandler("start", bot.start),
        ],
        states={
            ACCOUNT_BANK_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, bot.get_bank_name)
            ],
            ACCOUNT_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, bot.get_account_name)
            ],
            ACCOUNT_BALANCE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, bot.get_account_balance)
            ],
        },
        fallbacks=[CommandHandler("cancel", bot.cancel)],
    )

    # اضافه کردن هندلرها
    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(CommandHandler("help", bot.help_command))
    application.add_handler(CommandHandler("accounts", bot.accounts_command))
    application.add_handler(account_conv_handler)
    application.add_handler(CallbackQueryHandler(bot.handle_callback))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message)
    )

    # شروع ربات
    print("✅ ربات محلی آماده است!")
    print("💬 برای تست، به ربات @FinanceAppReminderBot پیام بدهید")
    print("🛑 برای توقف، Ctrl+C را فشار دهید")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()