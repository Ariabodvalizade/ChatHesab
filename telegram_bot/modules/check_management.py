# modules/check_management.py
import logging
from typing import Optional, Dict, List
from datetime import datetime, date, timedelta
from decimal import Decimal
from ..database.connection import get_db

logger = logging.getLogger(__name__)


class CheckManager:
    def __init__(self):
        self.db = get_db()

    def create_check(
        self,
        user_id: int,
        account_id: int,
        check_type: str,
        amount: Decimal,
        due_date: date,
        recipient_issuer: str = None,
        description: str = None,
    ) -> Optional[int]:
        """ثبت چک جدید"""
        try:
            query = """
                INSERT INTO checks 
                (user_id, account_id, type, amount, due_date, 
                 recipient_issuer, description, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """

            params = (
                user_id,
                account_id,
                check_type,
                amount,
                due_date,
                recipient_issuer,
                description,
                "pending",
            )

            check_id = self.db.execute_query(query, params)

            if check_id:
                logger.info(f"چک {check_id} ثبت شد")

            return check_id

        except Exception as e:
            logger.error(f"خطا در ثبت چک: {e}")
            return None

    def get_user_checks(
        self,
        user_id: int,
        check_type: str = None,
        status: str = None,
        start_date: date = None,
        end_date: date = None,
    ) -> List[Dict]:
        """دریافت چک‌های کاربر"""
        query = """
            SELECT c.*, a.account_name, a.bank_name
            FROM checks c
            JOIN bank_accounts a ON c.account_id = a.account_id
            WHERE c.user_id = %s
        """

        params = [user_id]

        if check_type:
            query += " AND c.type = %s"
            params.append(check_type)

        if status:
            query += " AND c.status = %s"
            params.append(status)

        if start_date:
            query += " AND c.due_date >= %s"
            params.append(start_date)

        if end_date:
            query += " AND c.due_date <= %s"
            params.append(end_date)

        query += " ORDER BY c.due_date ASC"

        checks = self.db.execute_query(query, params, fetch_all=True)

        # تبدیل Decimal به float
        for check in checks:
            check["amount"] = float(check["amount"])

        return checks or []

    def get_upcoming_checks(self, user_id: int, days_ahead: int = 7) -> List[Dict]:
        """دریافت چک‌های نزدیک به سررسید"""
        end_date = date.today() + timedelta(days=days_ahead)

        return self.get_user_checks(
            user_id=user_id,
            status="pending",
            start_date=date.today(),
            end_date=end_date,
        )

    def get_overdue_checks(self, user_id: int) -> List[Dict]:
        """دریافت چک‌های سررسید گذشته"""
        query = """
            SELECT c.*, a.account_name, a.bank_name
            FROM checks c
            JOIN bank_accounts a ON c.account_id = a.account_id
            WHERE c.user_id = %s
            AND c.status = 'pending'
            AND c.due_date < %s
            ORDER BY c.due_date ASC
        """

        checks = self.db.execute_query(query, (user_id, date.today()), fetch_all=True)

        for check in checks:
            check["amount"] = float(check["amount"])

        return checks or []

    def update_check_status(self, check_id: int, new_status: str) -> bool:
        """به‌روزرسانی وضعیت چک"""
        try:
            valid_statuses = ["pending", "cleared", "bounced", "cancelled"]
            if new_status not in valid_statuses:
                return False

            query = "UPDATE checks SET status = %s WHERE check_id = %s"
            self.db.execute_query(query, (new_status, check_id))

            logger.info(f"وضعیت چک {check_id} به {new_status} تغییر کرد")
            return True

        except Exception as e:
            logger.error(f"خطا در به‌روزرسانی وضعیت چک: {e}")
            return False

    def clear_check(self, check_id: int, create_transaction: bool = True) -> bool:
        """پاس کردن چک و ایجاد تراکنش مربوطه"""
        try:
            # دریافت اطلاعات چک
            check = self.get_check_by_id(check_id)
            if not check or check["status"] != "pending":
                return False

            # به‌روزرسانی وضعیت
            self.update_check_status(check_id, "cleared")

            # ایجاد تراکنش اگر درخواست شده
            if create_transaction:
                from .transaction_handler import TransactionHandler

                trans_handler = TransactionHandler()

                # تعیین نوع تراکنش
                trans_type = "expense" if check["type"] == "issued" else "income"

                # توضیحات
                description = (
                    f"چک {check['type']} - {check.get('recipient_issuer', '')}"
                )
                if check.get("description"):
                    description += f" - {check['description']}"

                trans_handler.create_transaction(
                    user_id=check["user_id"],
                    account_id=check["account_id"],
                    transaction_type=trans_type,
                    amount=Decimal(str(check["amount"])),
                    category="چک",
                    description=description,
                    transaction_date=datetime.now(),
                )

            return True

        except Exception as e:
            logger.error(f"خطا در پاس کردن چک: {e}")
            return False

    def get_check_by_id(self, check_id: int) -> Optional[Dict]:
        """دریافت اطلاعات یک چک"""
        query = """
            SELECT c.*, a.account_name, a.bank_name
            FROM checks c
            JOIN bank_accounts a ON c.account_id = a.account_id
            WHERE c.check_id = %s
        """

        check = self.db.execute_query(query, (check_id,), fetch_one=True)

        if check:
            check["amount"] = float(check["amount"])

        return check

    def update_check(self, check_id: int, **kwargs) -> bool:
        """به‌روزرسانی اطلاعات چک"""
        try:
            allowed_fields = [
                "amount",
                "due_date",
                "recipient_issuer",
                "description",
                "status",
            ]
            updates = []
            values = []

            for field, value in kwargs.items():
                if field in allowed_fields:
                    updates.append(f"{field} = %s")
                    values.append(value)

            if not updates:
                return True

            values.append(check_id)
            query = f"UPDATE checks SET {', '.join(updates)} WHERE check_id = %s"

            self.db.execute_query(query, values)
            return True

        except Exception as e:
            logger.error(f"خطا در به‌روزرسانی چک: {e}")
            return False

    def delete_check(self, check_id: int) -> bool:
        """حذف چک"""
        try:
            query = "DELETE FROM checks WHERE check_id = %s"
            self.db.execute_query(query, (check_id,))

            logger.info(f"چک {check_id} حذف شد")
            return True

        except Exception as e:
            logger.error(f"خطا در حذف چک: {e}")
            return False

    def get_checks_summary(self, user_id: int) -> Dict:
        """خلاصه وضعیت چک‌های کاربر"""
        query = """
            SELECT 
                type,
                status,
                COUNT(*) as count,
                SUM(amount) as total
            FROM checks
            WHERE user_id = %s
            GROUP BY type, status
        """

        results = self.db.execute_query(query, (user_id,), fetch_all=True)

        summary = {
            "issued": {
                "pending": {"count": 0, "total": 0},
                "cleared": {"count": 0, "total": 0},
                "bounced": {"count": 0, "total": 0},
                "cancelled": {"count": 0, "total": 0},
            },
            "received": {
                "pending": {"count": 0, "total": 0},
                "cleared": {"count": 0, "total": 0},
                "bounced": {"count": 0, "total": 0},
                "cancelled": {"count": 0, "total": 0},
            },
        }

        for row in results:
            check_type = row["type"]
            status = row["status"]
            summary[check_type][status]["count"] = row["count"]
            summary[check_type][status]["total"] = float(row["total"])

        return summary

    def create_reminder(self, check_id: int, reminder_date: date) -> bool:
        """ایجاد یادآوری برای چک"""
        try:
            check = self.get_check_by_id(check_id)
            if not check:
                return False

            query = """
                INSERT INTO reminders 
                (user_id, type, title, description, reminder_date)
                VALUES (%s, %s, %s, %s, %s)
            """

            title = f"چک {check['type']} - {check['amount']:,.0f} تومان"
            description = f"سررسید: {check['due_date']}"
            if check.get("recipient_issuer"):
                description += f" - {check['recipient_issuer']}"

            params = (check["user_id"], "check", title, description, reminder_date)

            self.db.execute_query(query, params)
            return True

        except Exception as e:
            logger.error(f"خطا در ایجاد یادآوری: {e}")
            return False
