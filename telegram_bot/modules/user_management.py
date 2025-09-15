# modules/user_management.py
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from ..database.connection import get_db
from ..config import TRIAL_DAYS

logger = logging.getLogger(__name__)


class UserManager:
    def __init__(self):
        self.db = get_db()

    def create_user(
        self,
        telegram_id: int,
        username: str = None,
        first_name: str = None,
        last_name: str = None,
    ) -> Optional[int]:
        """ایجاد کاربر جدید"""
        try:
            # بررسی وجود کاربر
            existing = self.get_user_by_telegram_id(telegram_id)
            if existing:
                return existing["user_id"]

            # محاسبه تاریخ پایان دوره آزمایشی
            trial_end = datetime.now() + timedelta(days=TRIAL_DAYS)

            query = """
                INSERT INTO users (telegram_id, username, first_name, last_name, 
                                 registration_date, trial_end_date, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
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

            # ایجاد تنظیمات پیش‌فرض
            self._create_default_settings(user_id)

            logger.info(f"کاربر جدید ایجاد شد: {user_id}")
            return user_id

        except Exception as e:
            logger.error(f"خطا در ایجاد کاربر: {e}")
            return None

    def get_user_by_telegram_id(self, telegram_id: int) -> Optional[Dict]:
        """دریافت اطلاعات کاربر با telegram_id"""
        query = """
            SELECT user_id, telegram_id, username, first_name, last_name,
                   registration_date, trial_end_date, subscription_end_date, is_active
            FROM users
            WHERE telegram_id = %s
        """

        return self.db.execute_query(query, (telegram_id,), fetch_one=True)

    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """دریافت اطلاعات کاربر با user_id"""
        query = """
            SELECT user_id, telegram_id, username, first_name, last_name,
                   registration_date, trial_end_date, subscription_end_date, is_active
            FROM users
            WHERE user_id = %s
        """

        return self.db.execute_query(query, (user_id,), fetch_one=True)

    def update_user(self, user_id: int, **kwargs) -> bool:
        """به‌روزرسانی اطلاعات کاربر"""
        try:
            allowed_fields = ["username", "first_name", "last_name", "is_active"]
            updates = []
            values = []

            for field, value in kwargs.items():
                if field in allowed_fields:
                    updates.append(f"{field} = %s")
                    values.append(value)

            if not updates:
                return True

            values.append(user_id)
            query = f"UPDATE users SET {', '.join(updates)} WHERE user_id = %s"

            self.db.execute_query(query, values)
            return True

        except Exception as e:
            logger.error(f"خطا در به‌روزرسانی کاربر: {e}")
            return False

    def check_subscription_status(self, user_id: int) -> Dict:
        """بررسی وضعیت اشتراک کاربر"""
        user = self.get_user_by_id(user_id)
        if not user:
            return {"is_active": False, "is_trial": False}

        now = datetime.now()
        result = {
            "is_active": False,
            "is_trial": False,
            "is_expired": False,
            "days_remaining": 0,
        }

        # بررسی دوره آزمایشی
        if user["trial_end_date"] and user["trial_end_date"] > now:
            result["is_active"] = True
            result["is_trial"] = True
            result["days_remaining"] = (user["trial_end_date"] - now).days
            result["trial_end_date"] = user["trial_end_date"]

        # بررسی اشتراک پولی
        elif user["subscription_end_date"] and user["subscription_end_date"] > now:
            result["is_active"] = True
            result["is_trial"] = False
            result["days_remaining"] = (user["subscription_end_date"] - now).days
            result["subscription_end_date"] = user["subscription_end_date"]

        # منقضی شده
        else:
            result["is_expired"] = True

        return result

    def extend_subscription(self, user_id: int, days: int) -> bool:
        """تمدید اشتراک کاربر"""
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return False

            # محاسبه تاریخ جدید
            current_end = user["subscription_end_date"]
            if current_end and current_end > datetime.now():
                # اضافه کردن به اشتراک فعلی
                new_end = current_end + timedelta(days=days)
            else:
                # شروع از امروز
                new_end = datetime.now() + timedelta(days=days)

            query = """
                UPDATE users 
                SET subscription_end_date = %s, is_active = %s
                WHERE user_id = %s
            """

            self.db.execute_query(query, (new_end, True, user_id))
            return True

        except Exception as e:
            logger.error(f"خطا در تمدید اشتراک: {e}")
            return False

    def get_user_settings(self, user_id: int) -> Dict:
        """دریافت تنظیمات کاربر"""
        query = """
            SELECT notification_enabled, daily_reminder_time, currency, language
            FROM user_settings
            WHERE user_id = %s
        """

        settings = self.db.execute_query(query, (user_id,), fetch_one=True)

        if not settings:
            # ایجاد تنظیمات پیش‌فرض
            self._create_default_settings(user_id)
            return {
                "notification_enabled": True,
                "daily_reminder_time": None,
                "currency": "تومان",
                "language": "fa",
            }

        return settings

    def update_user_settings(self, user_id: int, **kwargs) -> bool:
        """به‌روزرسانی تنظیمات کاربر"""
        try:
            allowed_fields = [
                "notification_enabled",
                "daily_reminder_time",
                "currency",
                "language",
            ]
            updates = []
            values = []

            for field, value in kwargs.items():
                if field in allowed_fields:
                    updates.append(f"{field} = %s")
                    values.append(value)

            if not updates:
                return True

            values.append(user_id)

            # بررسی وجود رکورد
            check_query = "SELECT user_id FROM user_settings WHERE user_id = %s"
            exists = self.db.execute_query(check_query, (user_id,), fetch_one=True)

            if exists:
                query = (
                    f"UPDATE user_settings SET {', '.join(updates)} WHERE user_id = %s"
                )
                self.db.execute_query(query, values)
            else:
                # ایجاد رکورد جدید
                self._create_default_settings(user_id)
                # سپس آپدیت
                query = (
                    f"UPDATE user_settings SET {', '.join(updates)} WHERE user_id = %s"
                )
                self.db.execute_query(query, values)

            return True

        except Exception as e:
            logger.error(f"خطا در به‌روزرسانی تنظیمات: {e}")
            return False

    def _create_default_settings(self, user_id: int):
        """ایجاد تنظیمات پیش‌فرض برای کاربر"""
        try:
            query = """
                INSERT INTO user_settings (user_id, notification_enabled, 
                                         currency, language)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE user_id = user_id
            """

            self.db.execute_query(query, (user_id, True, "تومان", "fa"))

        except Exception as e:
            logger.error(f"خطا در ایجاد تنظیمات پیش‌فرض: {e}")

    def get_all_active_users(self) -> List[Dict]:
        """دریافت لیست کاربران فعال"""
        query = """
            SELECT u.*, s.notification_enabled, s.daily_reminder_time
            FROM users u
            LEFT JOIN user_settings s ON u.user_id = s.user_id
            WHERE u.is_active = TRUE
            AND (u.trial_end_date > NOW() OR u.subscription_end_date > NOW())
        """

        return self.db.execute_query(query, fetch_all=True) or []

    def get_users_for_reminder(self, reminder_time: str = None) -> List[Dict]:
        """دریافت کاربرانی که باید یادآوری دریافت کنند"""
        query = """
            SELECT u.*, s.daily_reminder_time
            FROM users u
            INNER JOIN user_settings s ON u.user_id = s.user_id
            WHERE u.is_active = TRUE
            AND s.notification_enabled = TRUE
            AND (u.trial_end_date > NOW() OR u.subscription_end_date > NOW())
        """

        if reminder_time:
            query += " AND s.daily_reminder_time = %s"
            users = self.db.execute_query(query, (reminder_time,), fetch_all=True)
        else:
            users = self.db.execute_query(query, fetch_all=True)

        return users or []

    def log_activity(self, user_id: int, activity_type: str, details: str = None):
        """ثبت فعالیت کاربر (برای آمار)"""
        # این متد می‌تواند برای ثبت آمار استفاده کاربران استفاده شود
        # فعلاً پیاده‌سازی نشده
        pass

    def get_user_statistics(self, user_id: int) -> Dict:
        """دریافت آمار کاربر"""
        stats = {
            "total_transactions": 0,
            "total_income": 0,
            "total_expense": 0,
            "accounts_count": 0,
            "active_checks": 0,
            "savings_plans": 0,
        }

        try:
            # تعداد تراکنش‌ها
            query = """
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) as income,
                    SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) as expense
                FROM transactions
                WHERE user_id = %s
            """

            result = self.db.execute_query(query, (user_id,), fetch_one=True)
            if result:
                stats["total_transactions"] = result["total"] or 0
                stats["total_income"] = float(result["income"] or 0)
                stats["total_expense"] = float(result["expense"] or 0)

            # تعداد حساب‌ها
            query = "SELECT COUNT(*) as count FROM bank_accounts WHERE user_id = %s AND is_active = TRUE"
            result = self.db.execute_query(query, (user_id,), fetch_one=True)
            stats["accounts_count"] = result["count"] if result else 0

            # چک‌های فعال
            query = "SELECT COUNT(*) as count FROM checks WHERE user_id = %s AND status = 'pending'"
            result = self.db.execute_query(query, (user_id,), fetch_one=True)
            stats["active_checks"] = result["count"] if result else 0

            # طرح‌های پس‌انداز
            query = "SELECT COUNT(*) as count FROM savings_plans WHERE user_id = %s AND status = 'active'"
            result = self.db.execute_query(query, (user_id,), fetch_one=True)
            stats["savings_plans"] = result["count"] if result else 0

        except Exception as e:
            logger.error(f"خطا در دریافت آمار کاربر: {e}")

        return stats
