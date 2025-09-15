# modules/transaction_handler.py
import logging
from typing import Optional, Dict, List
from datetime import datetime, date
from decimal import Decimal
from ..database.connection import get_db
from .account_management import AccountManager

logger = logging.getLogger(__name__)


class TransactionHandler:
    def __init__(self):
        self.db = get_db()
        self.account_manager = AccountManager()

    def create_transaction(
        self,
        user_id: int,
        account_id: int,
        transaction_type: str,
        amount: Decimal,
        category: str,
        description: str = None,
        transaction_date: str = None,
    ) -> Optional[int]:
        """ایجاد تراکنش جدید"""
        try:
            # تبدیل تاریخ
            if transaction_date:
                if isinstance(transaction_date, str):
                    trans_date = datetime.strptime(transaction_date, "%Y-%m-%d")
                else:
                    trans_date = transaction_date
            else:
                trans_date = datetime.now()

            # ثبت تراکنش
            query = """
                INSERT INTO transactions 
                (user_id, account_id, type, amount, category, description, transaction_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """

            params = (
                user_id,
                account_id,
                transaction_type,
                amount,
                category,
                description,
                trans_date,
            )

            transaction_id = self.db.execute_query(query, params)

            # به‌روزرسانی موجودی حساب
            if transaction_id:
                self.account_manager.update_balance(
                    account_id, amount, transaction_type
                )

                logger.info(f"تراکنش {transaction_id} ثبت شد")

            return transaction_id

        except Exception as e:
            logger.error(f"خطا در ایجاد تراکنش: {e}")
            return None

    def get_user_transactions(
        self,
        user_id: int,
        start_date: date = None,
        end_date: date = None,
        transaction_type: str = None,
        category: str = None,
        account_id: int = None,
        limit: int = None,
    ) -> List[Dict]:
        """دریافت تراکنش‌های کاربر با فیلترهای مختلف"""
        query = """
            SELECT t.*, a.account_name, a.bank_name
            FROM transactions t
            JOIN bank_accounts a ON t.account_id = a.account_id
            WHERE t.user_id = %s
        """

        params = [user_id]

        # اعمال فیلترها
        if start_date:
            query += " AND t.transaction_date >= %s"
            params.append(start_date)

        if end_date:
            query += " AND t.transaction_date <= %s"
            params.append(end_date)

        if transaction_type:
            query += " AND t.type = %s"
            params.append(transaction_type)

        if category:
            query += " AND t.category = %s"
            params.append(category)

        if account_id:
            query += " AND t.account_id = %s"
            params.append(account_id)

        query += " ORDER BY t.transaction_date DESC, t.transaction_id DESC"

        if limit:
            query += f" LIMIT {limit}"

        transactions = self.db.execute_query(query, params, fetch_all=True)

        # تبدیل Decimal به float
        for trans in transactions:
            trans["amount"] = float(trans["amount"])

        return transactions or []

    def get_transaction_by_id(self, transaction_id: int) -> Optional[Dict]:
        """دریافت اطلاعات یک تراکنش"""
        query = """
            SELECT t.*, a.account_name, a.bank_name
            FROM transactions t
            JOIN bank_accounts a ON t.account_id = a.account_id
            WHERE t.transaction_id = %s
        """

        transaction = self.db.execute_query(query, (transaction_id,), fetch_one=True)

        if transaction:
            transaction["amount"] = float(transaction["amount"])

        return transaction

    def update_transaction(self, transaction_id: int, **kwargs) -> bool:
        """به‌روزرسانی تراکنش"""
        try:
            # دریافت تراکنش قبلی برای بازگردانی موجودی
            old_transaction = self.get_transaction_by_id(transaction_id)
            if not old_transaction:
                return False

            allowed_fields = ["amount", "category", "description", "transaction_date"]
            updates = []
            values = []

            for field, value in kwargs.items():
                if field in allowed_fields:
                    updates.append(f"{field} = %s")
                    values.append(value)

            if not updates:
                return True

            # اگر مبلغ تغییر کرده، موجودی را تنظیم کن
            if "amount" in kwargs:
                # بازگردانی موجودی قبلی
                reverse_type = (
                    "expense" if old_transaction["type"] == "income" else "income"
                )
                self.account_manager.update_balance(
                    old_transaction["account_id"],
                    Decimal(str(old_transaction["amount"])),
                    reverse_type,
                )

                # اعمال موجودی جدید
                self.account_manager.update_balance(
                    old_transaction["account_id"],
                    Decimal(str(kwargs["amount"])),
                    old_transaction["type"],
                )

            values.append(transaction_id)
            query = f"UPDATE transactions SET {', '.join(updates)} WHERE transaction_id = %s"

            self.db.execute_query(query, values)
            return True

        except Exception as e:
            logger.error(f"خطا در به‌روزرسانی تراکنش: {e}")
            return False

    def delete_transaction(self, transaction_id: int) -> bool:
        """حذف تراکنش"""
        try:
            # دریافت اطلاعات برای بازگردانی موجودی
            transaction = self.get_transaction_by_id(transaction_id)
            if not transaction:
                return False

            # حذف تراکنش
            query = "DELETE FROM transactions WHERE transaction_id = %s"
            self.db.execute_query(query, (transaction_id,))

            # بازگردانی موجودی حساب
            reverse_type = "expense" if transaction["type"] == "income" else "income"
            self.account_manager.update_balance(
                transaction["account_id"],
                Decimal(str(transaction["amount"])),
                reverse_type,
            )

            logger.info(f"تراکنش {transaction_id} حذف شد")
            return True

        except Exception as e:
            logger.error(f"خطا در حذف تراکنش: {e}")
            return False

    def get_transactions_summary(
        self, user_id: int, start_date: date = None, end_date: date = None
    ) -> Dict:
        """خلاصه تراکنش‌های کاربر در یک بازه زمانی"""

        # Query برای مجموع بر اساس نوع
        query = """
            SELECT 
                type,
                COUNT(*) as count,
                SUM(amount) as total
            FROM transactions
            WHERE user_id = %s
        """

        params = [user_id]

        if start_date:
            query += " AND transaction_date >= %s"
            params.append(start_date)

        if end_date:
            query += " AND transaction_date <= %s"
            params.append(end_date)

        query += " GROUP BY type"

        results = self.db.execute_query(query, params, fetch_all=True)

        summary = {
            "income": {"count": 0, "total": 0},
            "expense": {"count": 0, "total": 0},
            "balance": 0,
        }

        for row in results:
            trans_type = row["type"]
            summary[trans_type]["count"] = row["count"]
            summary[trans_type]["total"] = float(row["total"])

        summary["balance"] = summary["income"]["total"] - summary["expense"]["total"]

        return summary

    def get_category_summary(
        self,
        user_id: int,
        transaction_type: str = None,
        start_date: date = None,
        end_date: date = None,
    ) -> Dict:
        """خلاصه تراکنش‌ها بر اساس دسته‌بندی"""
        query = """
            SELECT 
                category,
                COUNT(*) as count,
                SUM(amount) as total
            FROM transactions
            WHERE user_id = %s
        """

        params = [user_id]

        if transaction_type:
            query += " AND type = %s"
            params.append(transaction_type)

        if start_date:
            query += " AND transaction_date >= %s"
            params.append(start_date)

        if end_date:
            query += " AND transaction_date <= %s"
            params.append(end_date)

        query += " GROUP BY category ORDER BY total DESC"

        results = self.db.execute_query(query, params, fetch_all=True)

        summary = {}
        for row in results:
            summary[row["category"]] = {
                "count": row["count"],
                "total": float(row["total"]),
            }

        return summary

    def search_transactions(self, user_id: int, search_term: str) -> List[Dict]:
        """جستجو در تراکنش‌ها"""
        query = """
            SELECT t.*, a.account_name, a.bank_name
            FROM transactions t
            JOIN bank_accounts a ON t.account_id = a.account_id
            WHERE t.user_id = %s
            AND (t.description LIKE %s OR t.category LIKE %s)
            ORDER BY t.transaction_date DESC
            LIMIT 50
        """

        search_pattern = f"%{search_term}%"
        params = (user_id, search_pattern, search_pattern)

        transactions = self.db.execute_query(query, params, fetch_all=True)

        for trans in transactions:
            trans["amount"] = float(trans["amount"])

        return transactions or []
