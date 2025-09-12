# main.py
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
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

# واردات ماژول‌ها
from config import BOT_TOKEN, WELCOME_MESSAGE
from database.connection import init_database
from modules.user_management import UserManager
from modules.account_management import AccountManager
from modules.transaction_handler import TransactionHandler
from modules.ai_processor import AIProcessor
from modules.check_management import CheckManager
from modules.reports import ReportGenerator
from modules.savings_plans import SavingsManager
from modules.subscription import SubscriptionManager
from modules.voice_handler import VoiceHandler
from utils.formatter import (
    create_main_menu,
    create_help_message,
    format_error_message,
    create_inline_keyboard,
)

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


class FinanceBot:
    def __init__(self):
        self.user_manager = UserManager()
        self.account_manager = AccountManager()
        self.transaction_handler = TransactionHandler()
        self.ai_processor = AIProcessor()
        self.check_manager = CheckManager()
        self.report_generator = ReportGenerator()
        self.savings_manager = SavingsManager()
        self.subscription_manager = SubscriptionManager()
        self.voice_handler = VoiceHandler()

    async def start(self, update: Update, context):
        """دستور /start"""
        user = update.effective_user

        # ایجاد یا دریافت کاربر
        user_id = self.user_manager.create_user(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
        )

        if user_id:
            context.user_data["user_id"] = user_id

            # بررسی وضعیت اشتراک
            subscription_status = self.user_manager.check_subscription_status(user_id)

            # ارسال پیام خوش‌آمدگویی
            await update.message.reply_text(WELCOME_MESSAGE, parse_mode="Markdown")

            # نمایش منوی اصلی
            await update.message.reply_text(create_main_menu(), parse_mode="Markdown")

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
            await update.message.reply_text(format_error_message("general"))

        return ConversationHandler.END

    async def help_command(self, update: Update, context):
        """دستور /help"""
        await update.message.reply_text(create_help_message(), parse_mode="Markdown")

    async def accounts_command(self, update: Update, context):
        """دستور /accounts - مدیریت حساب‌ها"""
        user_id = context.user_data.get("user_id")
        if not user_id:
            await update.message.reply_text("لطفاً ابتدا /start را بزنید.")
            return

        # دکمه‌های مدیریت حساب
        keyboard = [
            [
                InlineKeyboardButton(
                    "➕ افزودن حساب جدید", callback_data="add_account"
                ),
                InlineKeyboardButton("📋 لیست حساب‌ها", callback_data="list_accounts"),
            ],
            [
                InlineKeyboardButton("✏️ ویرایش موجودی", callback_data="edit_balance"),
                InlineKeyboardButton("🔄 انتقال بین حساب‌ها", callback_data="transfer"),
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

        # بررسی اشتراک
        subscription = self.user_manager.check_subscription_status(user_id)
        if not subscription["is_active"]:
            await self.show_subscription_options(update, context)
            return

        # دریافت لیست حساب‌های کاربر
        accounts = self.account_manager.get_user_accounts(user_id)
        if not accounts:
            await update.message.reply_text(
                "❌ ابتدا باید حساب‌های بانکی خود را ثبت کنید.\n"
                "از دستور /accounts استفاده کنید."
            )
            return

        # پردازش پیام با AI
        message_text = update.message.text

        await update.message.reply_text("🤖 در حال پردازش پیام شما...")

        # آماده‌سازی context برای AI
        user_context = {"accounts": accounts}

        # پردازش با AI
        result = self.ai_processor.process_message(message_text, user_context)

        if not result.get("success"):
            await update.message.reply_text(format_error_message("ai_error"))
            return

        # ذخیره نتیجه در context
        context.user_data["ai_result"] = result

        # نمایش نتیجه و درخواست تأیید
        if result["type"] == "transaction":
            await self.show_transaction_confirmation(update, context, result)
        elif result["type"] == "check":
            await self.show_check_confirmation(update, context, result)
        else:
            await update.message.reply_text(
                "❌ نتوانستم پیام شما را به درستی پردازش کنم.\n" "لطفاً واضح‌تر بنویسید."
            )

    async def show_transaction_confirmation(self, update: Update, context, data):
        """نمایش تأیید تراکنش"""
        from utils.formatter import format_amount
        from utils.calendar_utils import get_persian_date_string

        # آماده‌سازی پیام تأیید
        if data["transaction_type"] == "expense":
            msg = "🔴 **ثبت هزینه**\n\n"
        else:
            msg = "🟢 **ثبت درآمد**\n\n"

        msg += f"💰 **مبلغ:** {format_amount(data['amount'])}\n"

        if data.get("category"):
            msg += f"📁 **دسته‌بندی:** {data['category']}\n"

        if data.get("account_name"):
            msg += f"🏦 **حساب:** {data['account_name']}\n"

        if data.get("description"):
            msg += f"📝 **توضیحات:** {data['description']}\n"

        if data.get("date"):
            try:
                from datetime import datetime

                date_obj = datetime.strptime(data["date"], "%Y-%m-%d").date()
                msg += f"📅 **تاریخ:** {get_persian_date_string(date_obj)}\n"
            except:
                pass

        msg += "\n✅ آیا اطلاعات فوق صحیح است؟"

        # دکمه‌های تأیید
        keyboard = [
            [
                InlineKeyboardButton("✅ تأیید", callback_data="confirm_transaction"),
                InlineKeyboardButton("✏️ ویرایش مبلغ", callback_data="edit_amount"),
            ],
            [InlineKeyboardButton("❌ لغو", callback_data="cancel")],
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

        if data == "main_menu":
            await query.edit_message_text(create_main_menu(), parse_mode="Markdown")

        elif data == "confirm_transaction":
            await self.save_transaction(update, context)

        elif data == "cancel":
            await query.edit_message_text("❌ عملیات لغو شد.")
            context.user_data.pop("ai_result", None)

        # سایر callback ها
        elif data == "add_account":
            await query.edit_message_text(
                "🏦 **افزودن حساب جدید**\n\n"
                "نام بانک را وارد کنید (مثلاً: ملت، ملی، صادرات):",
                parse_mode="Markdown",
            )
            return ACCOUNT_BANK_NAME

        elif data == "list_accounts":
            await self.show_accounts_list(update, context)

        elif data == "edit_amount":
            await query.edit_message_text("💰 مبلغ جدید را وارد کنید (به تومان):")
            return EDIT_AMOUNT

        elif data.startswith("subscribe_"):
            plan_type = data.replace("subscribe_", "")
            await self.show_payment_link(update, context, plan_type)

        elif data == "payment_help":
            await self.show_payment_help(update, context)

    async def save_transaction(self, update: Update, context):
        """ذخیره تراکنش تأیید شده"""
        query = update.callback_query
        user_id = context.user_data.get("user_id")
        ai_result = context.user_data.get("ai_result")

        if not ai_result:
            await query.edit_message_text("❌ خطا در دریافت اطلاعات")
            return

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
                "✅ تراکنش با موفقیت ثبت شد!", parse_mode="Markdown"
            )
        else:
            await query.edit_message_text(format_error_message("database_error"))

        # پاک کردن داده‌های موقت
        context.user_data.pop("ai_result", None)

    async def show_accounts_list(self, update: Update, context):
        """نمایش لیست حساب‌ها"""
        from utils.formatter import format_account_summary

        query = update.callback_query
        user_id = context.user_data.get("user_id")

        accounts = self.account_manager.get_user_accounts(user_id)

        if not accounts:
            await query.edit_message_text(
                "❌ هیچ حسابی ثبت نشده است.", parse_mode="Markdown"
            )
        else:
            msg = format_account_summary(accounts)
            await query.edit_message_text(msg, parse_mode="Markdown")

    async def show_subscription_options(self, update: Update, context):
        """نمایش گزینه‌های اشتراک"""
        from config import SUBSCRIPTION_PLANS

        msg = "⏰ **دوره آزمایشی شما به پایان رسیده است!**\n\n"
        msg += "برای ادامه استفاده از ربات، لطفاً یکی از پلن‌های زیر را انتخاب کنید:\n\n"

        keyboard = []
        for plan_id, plan_info in SUBSCRIPTION_PLANS.items():
            keyboard.append(
                [
                    InlineKeyboardButton(
                        plan_info["label"], callback_data=f"subscribe_{plan_id}"
                    )
                ]
            )

        keyboard.append(
            [InlineKeyboardButton("❓ راهنمای پرداخت", callback_data="payment_help")]
        )

        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            msg, parse_mode="Markdown", reply_markup=reply_markup
        )

    # هندلرهای ConversationHandler برای ثبت حساب
    async def get_bank_name(self, update: Update, context):
        """دریافت نام بانک"""
        bank_name = update.message.text.strip()
        context.user_data["new_account_bank"] = bank_name

        await update.message.reply_text(
            "نام حساب را وارد کنید\n"
            "(مثلاً: حساب اصلی، پس‌انداز، جاری، یا 4 رقم آخر کارت):"
        )
        return ACCOUNT_NAME

    async def get_account_name(self, update: Update, context):
        """دریافت نام حساب"""
        account_name = update.message.text.strip()
        context.user_data["new_account_name"] = account_name

        await update.message.reply_text(
            "موجودی اولیه حساب را وارد کنید (به تومان):\n" "مثلاً: 5000000 یا 5 میلیون"
        )
        return ACCOUNT_BALANCE

    async def get_account_balance(self, update: Update, context):
        """دریافت موجودی اولیه"""
        from utils.persian_utils import parse_amount

        balance_text = update.message.text
        balance = parse_amount(balance_text)

        if balance is None:
            await update.message.reply_text(
                "❌ مبلغ نامعتبر است. لطفاً دوباره وارد کنید:"
            )
            return ACCOUNT_BALANCE

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
                f"✅ حساب {account_name} در {bank_name} با موفقیت ثبت شد!",
                parse_mode="Markdown",
            )
        else:
            await update.message.reply_text(format_error_message("database_error"))

        # پاک کردن داده‌های موقت
        context.user_data.pop("new_account_bank", None)
        context.user_data.pop("new_account_name", None)

        return ConversationHandler.END

    async def cancel(self, update: Update, context):
        """لغو عملیات"""
        await update.message.reply_text("❌ عملیات لغو شد.", parse_mode="Markdown")
        return ConversationHandler.END

    async def handle_voice(self, update: Update, context):
        """پردازش پیام‌های صوتی"""
        user_id = context.user_data.get("user_id")
        if not user_id:
            await update.message.reply_text("لطفاً ابتدا /start را بزنید.")
            return

        await update.message.reply_text("🎤 در حال پردازش پیام صوتی...")

        # دانلود و پردازش فایل صوتی
        voice_file = await update.message.voice.get_file()
        text = await self.voice_handler.process_voice(voice_file)

        if text:
            # ارسال متن به همان فرآیند پردازش پیام
            update.message.text = text
            await self.handle_message(update, context)
        else:
            await update.message.reply_text(
                "❌ متأسفانه نتوانستم پیام صوتی را پردازش کنم."
            )

    async def show_payment_link(self, update: Update, context, plan_type: str):
        """نمایش لینک پرداخت"""
        query = update.callback_query
        user_id = context.user_data.get("user_id")

        # تولید لینک پرداخت
        payment_info = self.subscription_manager.generate_payment_link(
            user_id, plan_type
        )

        if payment_info["success"]:
            msg = f"💳 **پرداخت اشتراک**\n\n"
            msg += f"🔸 {payment_info['description']}\n"
            msg += f"💰 مبلغ: {payment_info['amount']:,} تومان\n\n"
            msg += f"{payment_info['message']}\n"
            msg += f"🔗 {payment_info['payment_url']}\n\n"
            msg += payment_info["instructions"]

            keyboard = [
                [
                    InlineKeyboardButton(
                        "✅ پرداخت کردم", callback_data="verify_payment"
                    )
                ],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="subscription_menu")],
            ]

            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                msg,
                parse_mode="Markdown",
                reply_markup=reply_markup,
                disable_web_page_preview=True,
            )
        else:
            await query.edit_message_text(
                f"❌ خطا: {payment_info['error']}", parse_mode="Markdown"
            )

    async def show_payment_help(self, update: Update, context):
        """نمایش راهنمای پرداخت"""
        query = update.callback_query

        help_text = """
📚 **راهنمای پرداخت**

1️⃣ **انتخاب پلن**: یکی از پلن‌های اشتراک را انتخاب کنید

2️⃣ **پرداخت**: 
   • روی لینک پرداخت کلیک کنید
   • به درگاه زرین‌پال منتقل می‌شوید
   • اطلاعات کارت خود را وارد کنید
   • پرداخت را تکمیل کنید

3️⃣ **فعال‌سازی**:
   • کد پیگیری را یادداشت کنید
   • به ربات برگردید
   • دستور /verify را همراه با کد پیگیری ارسال کنید
   
⚠️ **نکات مهم**:
• پرداخت از طریق درگاه امن زرین‌پال انجام می‌شود
• اطلاعات کارت شما نزد ما ذخیره نمی‌شود
• در صورت بروز مشکل با پشتیبانی تماس بگیرید

📞 پشتیبانی: @your_support_id
"""

        keyboard = [
            [InlineKeyboardButton("🔙 بازگشت", callback_data="subscription_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            help_text, parse_mode="Markdown", reply_markup=reply_markup
        )

    async def verify_payment_command(self, update: Update, context):
        """دستور /verify برای تأیید پرداخت"""
        if not context.args:
            await update.message.reply_text(
                "❌ لطفاً کد پیگیری را همراه با دستور ارسال کنید:\n" "/verify کد_پیگیری"
            )
            return

        payment_reference = context.args[0]
        user_id = context.user_data.get("user_id")

        if not user_id:
            await update.message.reply_text("لطفاً ابتدا /start را بزنید.")
            return

        # در اینجا باید پرداخت را با زرین‌پال چک کنید
        # فعلاً به صورت دستی تأیید می‌کنیم

        await update.message.reply_text(
            "✅ پرداخت شما در حال بررسی است...\n" "لطفاً کمی صبر کنید."
        )

        # TODO: اینجا باید API زرین‌پال را صدا بزنید
        # فعلاً فرض می‌کنیم پرداخت موفق بوده

        # ثبت اشتراک (باید plan_type را از جایی دریافت کنید)
        # می‌توانید از payment_reference برای شناسایی استفاده کنید

        await update.message.reply_text(
            "✅ اشتراک شما با موفقیت فعال شد!\n\n"
            "از اعتماد شما سپاسگزاریم. 🙏\n"
            "اکنون می‌توانید از تمام امکانات ربات استفاده کنید."
        )


def main():
    """تابع اصلی اجرای ربات"""
    # راه‌اندازی دیتابیس
    try:
        init_database()
        logger.info("دیتابیس با موفقیت راه‌اندازی شد")
    except Exception as e:
        logger.error(f"خطا در راه‌اندازی دیتابیس: {e}")
        return

    # ایجاد نمونه از ربات
    bot = FinanceBot()

    # ایجاد Application
    application = Application.builder().token(BOT_TOKEN).build()

    # ConversationHandler برای ثبت حساب
    account_conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(lambda u, c: u.callback_query.data == "add_account"),
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
    application.add_handler(CommandHandler("verify", bot.verify_payment_command))
    application.add_handler(account_conv_handler)
    application.add_handler(CallbackQueryHandler(bot.handle_callback))
    application.add_handler(MessageHandler(filters.VOICE, bot.handle_voice))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message)
    )

    # شروع ربات
    logger.info("ربات شروع به کار کرد...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
