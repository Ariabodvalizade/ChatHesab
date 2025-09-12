# modules/account_management.py
import logging
from typing import Optional, Dict, List
from decimal import Decimal
from database.connection import get_db

logger = logging.getLogger(__name__)


class AccountManager:
    def __init__(self):
        self.db = get_db()

    def create_account(
        self,
        user_id: int,
        bank_name: str,
        account_name: str,
        initial_balance: Decimal = 0,
    ) -> Optional[int]:
        """ایجاد حساب بانکی جدید"""
        try:
            # بررسی تکراری نبودن
            existing = self.get_account_by_name(user_id, account_name)
            if existing:
                logger.warning(f"حساب با نام {account_name} قبلاً وجود دارد")
                return None

            query = """
                INSERT INTO bank_accounts 
                (user_id, bank_name, account_name, initial_balance, current_balance)
                VALUES (%s, %s, %s, %s, %s)
            """

            params = (
                user_id,
                bank_name,
                account_name,
                initial_balance,
                initial_balance,
            )
            account_id = self.db.execute_query(query, params)

            logger.info(f"حساب جدید ایجاد شد: {account_id}")
            return account_id

        except Exception as e:
            logger.error(f"خطا در ایجاد حساب: {e}")
            return None

    def get_user_accounts(self, user_id: int, active_only: bool = True) -> List[Dict]:
        """دریافت لیست حساب‌های کاربر"""
        query = """
            SELECT account_id, bank_name, account_name, 
                   initial_balance, current_balance, is_active,
                   created_at, updated_at
            FROM bank_accounts
            WHERE user_id = %s
        """

        if active_only:
            query += " AND is_active = TRUE"

        query += " ORDER BY created_at ASC"

        accounts = self.db.execute_query(query, (user_id,), fetch_all=True)

        # تبدیل Decimal به float برای سهولت کار
        for account in accounts:
            account["initial_balance"] = float(account["initial_balance"])
            account["current_balance"] = float(account["current_balance"])

        return accounts or []

    def get_account_by_id(self, account_id: int) -> Optional[Dict]:
        """دریافت اطلاعات حساب با ID"""
        query = """
            SELECT account_id, user_id, bank_name, account_name,
                   initial_balance, current_balance, is_active
            FROM bank_accounts
            WHERE account_id = %s
        """

        account = self.db.execute_query(query, (account_id,), fetch_one=True)

        if account:
            account["initial_balance"] = float(account["initial_balance"])
            account["current_balance"] = float(account["current_balance"])

        return account

    def get_account_by_name(self, user_id: int, account_name: str) -> Optional[Dict]:
        """دریافت اطلاعات حساب با نام"""
        query = """
            SELECT account_id, bank_name, account_name,
                   initial_balance, current_balance, is_active
            FROM bank_accounts
            WHERE user_id = %s AND account_name = %s AND is_active = TRUE
        """

        account = self.db.execute_query(query, (user_id, account_name), fetch_one=True)

        if account:
            account["initial_balance"] = float(account["initial_balance"])
            account["current_balance"] = float(account["current_balance"])

        return account

    def update_balance(
        self, account_id: int, amount: Decimal, transaction_type: str = "expense"
    ) -> bool:
        """به‌روزرسانی موجودی حساب"""
        try:
            # دریافت موجودی فعلی
            account = self.get_account_by_id(account_id)
            if not account:
                return False

            current_balance = Decimal(str(account["current_balance"]))

            # محاسبه موجودی جدید
            if transaction_type == "income":
                new_balance = current_balance + amount
            else:  # expense
                new_balance = current_balance - amount

            # به‌روزرسانی
            query = """
                UPDATE bank_accounts
                SET current_balance = %s
                WHERE account_id = %s
            """

            self.db.execute_query(query, (new_balance, account_id))

            logger.info(f"موجودی حساب {account_id} به‌روزرسانی شد: {new_balance}")
            return True

        except Exception as e:
            logger.error(f"خطا در به‌روزرسانی موجودی: {e}")
            return False

    def update_account(self, account_id: int, **kwargs) -> bool:
        """به‌روزرسانی اطلاعات حساب"""
        try:
            allowed_fields = [
                "bank_name",
                "account_name",
                "initial_balance",
                "current_balance",
                "is_active",
            ]
            updates = []
            values = []

            for field, value in kwargs.items():
                if field in allowed_fields:
                    updates.append(f"{field} = %s")
                    values.append(value)

            if not updates:
                return True

            values.append(account_id)
            query = (
                f"UPDATE bank_accounts SET {', '.join(updates)} WHERE account_id = %s"
            )

            self.db.execute_query(query, values)
            return True

        except Exception as e:
            logger.error(f"خطا در به‌روزرسانی حساب: {e}")
            return False

    def delete_account(self, account_id: int, soft_delete: bool = True) -> bool:
        """حذف حساب (soft delete پیش‌فرض)"""
        try:
            if soft_delete:
                query = (
                    "UPDATE bank_accounts SET is_active = FALSE WHERE account_id = %s"
                )
            else:
                # ابتدا بررسی تراکنش‌ها
                check_query = (
                    "SELECT COUNT(*) as count FROM transactions WHERE account_id = %s"
                )
                result = self.db.execute_query(
                    check_query, (account_id,), fetch_one=True
                )

                if result and result["count"] > 0:
                    logger.warning(
                        f"حساب {account_id} دارای تراکنش است و نمی‌تواند حذف شود"
                    )
                    return False

                query = "DELETE FROM bank_accounts WHERE account_id = %s"

            self.db.execute_query(query, (account_id,))
            return True

        except Exception as e:
            logger.error(f"خطا در حذف حساب: {e}")
            return False

    def get_total_balance(self, user_id: int) -> Decimal:
        """محاسبه مجموع موجودی تمام حساب‌ها"""
        query = """
            SELECT SUM(current_balance) as total
            FROM bank_accounts
            WHERE user_id = %s AND is_active = TRUE
        """

        result = self.db.execute_query(query, (user_id,), fetch_one=True)
        return (
            Decimal(str(result["total"]))
            if result and result["total"]
            else Decimal("0")
        )

    def transfer_between_accounts(
        self, from_account_id: int, to_account_id: int, amount: Decimal
    ) -> bool:
        """انتقال وجه بین حساب‌ها"""
        try:
            # بررسی موجودی حساب مبدأ
            from_account = self.get_account_by_id(from_account_id)
            if not from_account or from_account["current_balance"] < amount:
                logger.warning("موجودی حساب مبدأ کافی نیست")
                return False

            # کسر از حساب مبدأ
            self.update_balance(from_account_id, amount, "expense")

            # اضافه به حساب مقصد
            self.update_balance(to_account_id, amount, "income")

            logger.info(f"انتقال {amount} از حساب {from_account_id} به {to_account_id}")
            return True

        except Exception as e:
            logger.error(f"خطا در انتقال وجه: {e}")
            return False

    def get_account_summary(self, user_id: int) -> Dict:
        """خلاصه وضعیت حساب‌های کاربر"""
        accounts = self.get_user_accounts(user_id)

        summary = {
            "total_accounts": len(accounts),
            "total_balance": 0,
            "positive_accounts": 0,
            "negative_accounts": 0,
            "zero_accounts": 0,
            "accounts_detail": [],
        }

        for account in accounts:
            balance = account["current_balance"]
            summary["total_balance"] += balance

            if balance > 0:
                summary["positive_accounts"] += 1
            elif balance < 0:
                summary["negative_accounts"] += 1
            else:
                summary["zero_accounts"] += 1

            summary["accounts_detail"].append(
                {
                    "name": account["account_name"],
                    "bank": account["bank_name"],
                    "balance": balance,
                }
            )

        return summary

    def find_account_by_bank(self, user_id: int, bank_name: str) -> Optional[Dict]:
        """جستجوی حساب بر اساس نام بانک"""
        query = """
            SELECT account_id, bank_name, account_name, current_balance
            FROM bank_accounts
            WHERE user_id = %s AND bank_name LIKE %s AND is_active = TRUE
            ORDER BY created_at ASC
            LIMIT 1
        """

        account = self.db.execute_query(
            query, (user_id, f"%{bank_name}%"), fetch_one=True
        )

        if account:
            account["current_balance"] = float(account["current_balance"])

        return account
