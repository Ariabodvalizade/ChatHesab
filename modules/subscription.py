# modules/subscription.py
import logging
from typing import Optional, Dict, List
from datetime import datetime, timedelta
from decimal import Decimal
from database.connection import get_db
from config import SUBSCRIPTION_PLANS
from modules.user_management import UserManager

logger = logging.getLogger(__name__)


class SubscriptionManager:
    def __init__(self):
        self.db = get_db()
        self.user_manager = UserManager()

    def create_subscription(
        self, user_id: int, plan_type: str, payment_reference: str = None
    ) -> Optional[int]:
        """ایجاد اشتراک جدید"""
        try:
            if plan_type not in SUBSCRIPTION_PLANS:
                logger.error(f"نوع اشتراک نامعتبر: {plan_type}")
                return None

            plan = SUBSCRIPTION_PLANS[plan_type]
            start_date = datetime.now()
            end_date = start_date + timedelta(days=plan["days"])

            query = """
                INSERT INTO subscriptions
                (user_id, plan_type, amount_paid, start_date, 
                 end_date, payment_reference, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """

            params = (
                user_id,
                plan_type,
                plan["price"],
                start_date,
                end_date,
                payment_reference,
                "active",
            )

            subscription_id = self.db.execute_query(query, params)

            if subscription_id:
                # به‌روزرسانی تاریخ انقضای کاربر
                self.user_manager.extend_subscription(user_id, plan["days"])
                logger.info(f"اشتراک {subscription_id} ایجاد شد")

            return subscription_id

        except Exception as e:
            logger.error(f"خطا در ایجاد اشتراک: {e}")
            return None

    def get_user_subscriptions(self, user_id: int) -> List[Dict]:
        """دریافت تاریخچه اشتراک‌های کاربر"""
        query = """
            SELECT * FROM subscriptions
            WHERE user_id = %s
            ORDER BY created_at DESC
        """

        subscriptions = self.db.execute_query(query, (user_id,), fetch_all=True)

        # اضافه کردن اطلاعات پلن
        for sub in subscriptions:
            if sub["plan_type"] in SUBSCRIPTION_PLANS:
                sub["plan_info"] = SUBSCRIPTION_PLANS[sub["plan_type"]]
            sub["amount_paid"] = float(sub["amount_paid"])

        return subscriptions or []

    def get_active_subscription(self, user_id: int) -> Optional[Dict]:
        """دریافت اشتراک فعال کاربر"""
        query = """
            SELECT * FROM subscriptions
            WHERE user_id = %s 
            AND status = 'active'
            AND end_date > NOW()
            ORDER BY end_date DESC
            LIMIT 1
        """

        subscription = self.db.execute_query(query, (user_id,), fetch_one=True)

        if subscription:
            subscription["amount_paid"] = float(subscription["amount_paid"])
            if subscription["plan_type"] in SUBSCRIPTION_PLANS:
                subscription["plan_info"] = SUBSCRIPTION_PLANS[
                    subscription["plan_type"]
                ]

        return subscription

    def cancel_subscription(self, subscription_id: int) -> bool:
        """لغو اشتراک"""
        try:
            query = """
                UPDATE subscriptions 
                SET status = 'cancelled'
                WHERE subscription_id = %s
            """

            self.db.execute_query(query, (subscription_id,))
            return True

        except Exception as e:
            logger.error(f"خطا در لغو اشتراک: {e}")
            return False

    def check_expiring_subscriptions(self, days_ahead: int = 3) -> List[Dict]:
        """بررسی اشتراک‌های در حال انقضا"""
        query = """
            SELECT s.*, u.telegram_id, u.first_name
            FROM subscriptions s
            JOIN users u ON s.user_id = u.user_id
            WHERE s.status = 'active'
            AND s.end_date BETWEEN NOW() AND DATE_ADD(NOW(), INTERVAL %s DAY)
        """

        subscriptions = self.db.execute_query(query, (days_ahead,), fetch_all=True)

        for sub in subscriptions:
            sub["amount_paid"] = float(sub["amount_paid"])
            sub["days_remaining"] = (sub["end_date"] - datetime.now()).days

        return subscriptions or []

    def update_expired_subscriptions(self) -> int:
        """به‌روزرسانی وضعیت اشتراک‌های منقضی شده"""
        try:
            query = """
                UPDATE subscriptions
                SET status = 'expired'
                WHERE status = 'active'
                AND end_date < NOW()
            """

            affected_rows = self.db.execute_query(query)

            # غیرفعال کردن کاربران با اشتراک منقضی
            user_query = """
                UPDATE users u
                SET u.is_active = FALSE
                WHERE NOT EXISTS (
                    SELECT 1 FROM subscriptions s
                    WHERE s.user_id = u.user_id
                    AND s.status = 'active'
                    AND s.end_date > NOW()
                )
                AND u.trial_end_date < NOW()
            """

            self.db.execute_query(user_query)

            return affected_rows

        except Exception as e:
            logger.error(f"خطا در به‌روزرسانی اشتراک‌های منقضی: {e}")
            return 0

    def generate_payment_link(self, user_id: int, plan_type: str) -> Dict:
        """تولید لینک پرداخت زرین‌پال"""

        # لینک‌های پرداخت زرین‌پال
        ZARINPAL_LINKS = {
            "1_month": "https://zarinp.al/724182",
            "2_months": "https://zarinp.al/725463",
            "3_months": "https://zarinp.al/725464",
            "6_months": "https://zarinp.al/725465",
            "12_months": "https://zarinp.al/725466",
        }

        if plan_type not in SUBSCRIPTION_PLANS:
            return {"success": False, "error": "نوع اشتراک نامعتبر"}

        if plan_type not in ZARINPAL_LINKS:
            return {"success": False, "error": "لینک پرداخت برای این پلن موجود نیست"}

        plan = SUBSCRIPTION_PLANS[plan_type]

        # ذخیره اطلاعات پرداخت در حال انجام
        self._save_pending_payment(user_id, plan_type)

        return {
            "success": True,
            "amount": plan["price"],
            "description": plan["label"],
            "payment_url": ZARINPAL_LINKS[plan_type],
            "message": "لطفاً از طریق لینک زیر پرداخت را انجام دهید:",
            "instructions": (
                "⚠️ توجه:\n"
                "1. پس از پرداخت موفق، کد پیگیری را ذخیره کنید\n"
                "2. کد پیگیری را با دستور /verify ارسال کنید\n"
                "3. اشتراک شما بلافاصله فعال خواهد شد"
            ),
        }

    def _save_pending_payment(self, user_id: int, plan_type: str) -> bool:
        """ذخیره اطلاعات پرداخت در حال انجام"""
        try:
            # می‌توانید این اطلاعات را در یک جدول جداگانه ذخیره کنید
            # یا در حافظه موقت نگه دارید
            # فعلاً به صورت ساده در لاگ ثبت می‌کنیم
            logger.info(f"Pending payment: user_id={user_id}, plan={plan_type}")
            return True
        except Exception as e:
            logger.error(f"خطا در ذخیره پرداخت در حال انجام: {e}")
            return False

    def verify_payment(self, user_id: int, payment_reference: str) -> bool:
        """تأیید پرداخت (برای آینده)"""
        # این تابع برای تأیید پرداخت از درگاه استفاده خواهد شد
        # فعلاً فقط True برمی‌گرداند
        return True

    def get_revenue_report(
        self, start_date: datetime = None, end_date: datetime = None
    ) -> Dict:
        """گزارش درآمد از اشتراک‌ها"""
        query = """
            SELECT 
                COUNT(*) as total_subscriptions,
                SUM(amount_paid) as total_revenue,
                plan_type,
                COUNT(*) as count_by_type
            FROM subscriptions
            WHERE status != 'cancelled'
        """

        params = []

        if start_date:
            query += " AND created_at >= %s"
            params.append(start_date)

        if end_date:
            query += " AND created_at <= %s"
            params.append(end_date)

        query += " GROUP BY plan_type"

        results = self.db.execute_query(query, params, fetch_all=True)

        report = {"total_subscriptions": 0, "total_revenue": 0, "by_plan_type": {}}

        for row in results:
            report["total_subscriptions"] += row["count_by_type"]
            report["total_revenue"] += float(row["total_revenue"] or 0)
            report["by_plan_type"][row["plan_type"]] = {
                "count": row["count_by_type"],
                "revenue": float(row["total_revenue"] or 0),
            }

        return report

    def send_renewal_reminder(self, user_id: int, days_remaining: int) -> Dict:
        """ارسال یادآوری تمدید (برای استفاده در ربات)"""
        from utils.formatter import format_amount, english_to_persian_digits

        subscription = self.get_active_subscription(user_id)

        if not subscription:
            return {"message": "اشتراک فعالی یافت نشد.", "success": False}

        message = f"""
⏰ **یادآوری تمدید اشتراک**

اشتراک شما {english_to_persian_digits(str(days_remaining))} روز دیگر به پایان می‌رسد.

برای ادامه استفاده بدون وقفه از امکانات ربات، لطفاً اشتراک خود را تمدید کنید.

💎 **پیشنهاد ویژه:** با تمدید ۶ ماهه یا سالانه از تخفیف ویژه بهره‌مند شوید!
"""

        return {"message": message, "success": True, "show_plans": True}
