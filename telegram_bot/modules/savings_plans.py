# modules/savings_plans.py
import logging
from typing import Optional, Dict, List
from datetime import datetime, date, timedelta
from decimal import Decimal
from ..database.connection import get_db

logger = logging.getLogger(__name__)


class SavingsManager:
    def __init__(self):
        self.db = get_db()

        # طرح‌های پس‌انداز پیش‌فرض
        self.predefined_plans = {
            "50_30_20": {
                "name": "قانون 50-30-20",
                "description": "50% نیازها، 30% خواسته‌ها، 20% پس‌انداز",
                "savings_rate": 0.20,
            },
            "envelope": {
                "name": "روش پاکت",
                "description": "تقسیم درآمد در پاکت‌های مختلف",
                "categories": ["ضروری", "تفریح", "پس‌انداز", "اضطراری"],
            },
            "pay_yourself_first": {
                "name": "اول به خودت بپرداز",
                "description": "ابتدا مبلغ پس‌انداز را کنار بگذار",
                "savings_rate": 0.15,
            },
            "zero_based": {
                "name": "بودجه‌بندی صفر",
                "description": "تخصیص تمام درآمد به دسته‌های مختلف",
                "requires_planning": True,
            },
            "gold_savings": {
                "name": "پس‌انداز طلا",
                "description": "خرید ماهانه طلای آب‌شده",
                "unit": "گرم",
            },
        }

    def create_savings_plan(
        self,
        user_id: int,
        plan_name: str,
        plan_type: str = None,
        target_amount: Decimal = None,
        monthly_contribution: Decimal = None,
        end_date: date = None,
    ) -> Optional[int]:
        """ایجاد طرح پس‌انداز جدید"""
        try:
            query = """
                INSERT INTO savings_plans
                (user_id, plan_name, plan_type, target_amount, 
                 current_amount, monthly_contribution, start_date, end_date, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            params = (
                user_id,
                plan_name,
                plan_type,
                target_amount,
                0,
                monthly_contribution,
                date.today(),
                end_date,
                "active",
            )

            plan_id = self.db.execute_query(query, params)

            if plan_id:
                logger.info(f"طرح پس‌انداز {plan_id} ایجاد شد")

            return plan_id

        except Exception as e:
            logger.error(f"خطا در ایجاد طرح پس‌انداز: {e}")
            return None

    def get_user_plans(self, user_id: int, status: str = None) -> List[Dict]:
        """دریافت طرح‌های پس‌انداز کاربر"""
        query = """
            SELECT * FROM savings_plans
            WHERE user_id = %s
        """

        params = [user_id]

        if status:
            query += " AND status = %s"
            params.append(status)

        query += " ORDER BY created_at DESC"

        plans = self.db.execute_query(query, params, fetch_all=True)

        # تبدیل Decimal به float و محاسبه پیشرفت
        for plan in plans:
            plan["target_amount"] = (
                float(plan["target_amount"]) if plan["target_amount"] else 0
            )
            plan["current_amount"] = float(plan["current_amount"])
            plan["monthly_contribution"] = (
                float(plan["monthly_contribution"])
                if plan["monthly_contribution"]
                else 0
            )

            # محاسبه درصد پیشرفت
            if plan["target_amount"] > 0:
                plan["progress_percentage"] = (
                    plan["current_amount"] / plan["target_amount"]
                ) * 100
            else:
                plan["progress_percentage"] = 0

            # محاسبه ماه‌های باقی‌مانده
            if (
                plan["monthly_contribution"] > 0
                and plan["target_amount"] > plan["current_amount"]
            ):
                remaining = plan["target_amount"] - plan["current_amount"]
                plan["months_remaining"] = int(remaining / plan["monthly_contribution"])
            else:
                plan["months_remaining"] = None

        return plans or []

    def update_plan_amount(
        self, plan_id: int, amount: Decimal, operation: str = "add"
    ) -> bool:
        """به‌روزرسانی مبلغ طرح پس‌انداز"""
        try:
            # دریافت اطلاعات فعلی
            plan = self.get_plan_by_id(plan_id)
            if not plan:
                return False

            current_amount = Decimal(str(plan["current_amount"]))

            # محاسبه مبلغ جدید
            if operation == "add":
                new_amount = current_amount + amount
            elif operation == "subtract":
                new_amount = current_amount - amount
                if new_amount < 0:
                    new_amount = Decimal("0")
            else:
                new_amount = amount

            # به‌روزرسانی
            query = "UPDATE savings_plans SET current_amount = %s WHERE plan_id = %s"
            self.db.execute_query(query, (new_amount, plan_id))

            # بررسی تکمیل طرح
            if plan["target_amount"] and new_amount >= Decimal(
                str(plan["target_amount"])
            ):
                self.update_plan_status(plan_id, "completed")

            return True

        except Exception as e:
            logger.error(f"خطا در به‌روزرسانی مبلغ طرح: {e}")
            return False

    def get_plan_by_id(self, plan_id: int) -> Optional[Dict]:
        """دریافت اطلاعات یک طرح"""
        query = "SELECT * FROM savings_plans WHERE plan_id = %s"

        plan = self.db.execute_query(query, (plan_id,), fetch_one=True)

        if plan:
            plan["target_amount"] = (
                float(plan["target_amount"]) if plan["target_amount"] else 0
            )
            plan["current_amount"] = float(plan["current_amount"])
            plan["monthly_contribution"] = (
                float(plan["monthly_contribution"])
                if plan["monthly_contribution"]
                else 0
            )

        return plan

    def update_plan_status(self, plan_id: int, status: str) -> bool:
        """به‌روزرسانی وضعیت طرح"""
        try:
            valid_statuses = ["active", "completed", "cancelled", "paused"]
            if status not in valid_statuses:
                return False

            query = "UPDATE savings_plans SET status = %s WHERE plan_id = %s"
            self.db.execute_query(query, (status, plan_id))

            return True

        except Exception as e:
            logger.error(f"خطا در به‌روزرسانی وضعیت طرح: {e}")
            return False

    def calculate_savings_suggestion(
        self, user_id: int, income: Decimal, method: str = "50_30_20"
    ) -> Dict:
        """محاسبه پیشنهاد پس‌انداز بر اساس روش انتخابی"""
        if method not in self.predefined_plans:
            method = "50_30_20"

        plan_info = self.predefined_plans[method]

        if method == "50_30_20":
            return {
                "method": plan_info["name"],
                "needs": float(income) * 0.50,
                "wants": float(income) * 0.30,
                "savings": float(income) * 0.20,
                "description": plan_info["description"],
            }

        elif method == "pay_yourself_first":
            return {
                "method": plan_info["name"],
                "savings": float(income) * plan_info["savings_rate"],
                "remaining": float(income) * (1 - plan_info["savings_rate"]),
                "description": plan_info["description"],
            }

        else:
            return {
                "method": plan_info["name"],
                "description": plan_info["description"],
                "requires_custom_planning": True,
            }

    def get_savings_performance(self, user_id: int) -> Dict:
        """ارزیابی عملکرد پس‌انداز کاربر"""
        # دریافت طرح‌های فعال
        active_plans = self.get_user_plans(user_id, status="active")
        completed_plans = self.get_user_plans(user_id, status="completed")

        # محاسبه آمار
        total_saved = sum(p["current_amount"] for p in active_plans)
        total_saved += sum(p["current_amount"] for p in completed_plans)

        total_target = sum(
            p["target_amount"] for p in active_plans if p["target_amount"]
        )

        # میانگین پیشرفت
        if active_plans:
            avg_progress = sum(p["progress_percentage"] for p in active_plans) / len(
                active_plans
            )
        else:
            avg_progress = 0

        return {
            "active_plans_count": len(active_plans),
            "completed_plans_count": len(completed_plans),
            "total_saved": total_saved,
            "total_target": total_target,
            "average_progress": avg_progress,
            "performance_score": self._calculate_performance_score(
                active_plans, completed_plans
            ),
        }

    def _calculate_performance_score(
        self, active_plans: List[Dict], completed_plans: List[Dict]
    ) -> float:
        """محاسبه امتیاز عملکرد پس‌انداز"""
        score = 0

        # امتیاز برای طرح‌های تکمیل شده
        score += len(completed_plans) * 20

        # امتیاز برای پیشرفت طرح‌های فعال
        for plan in active_plans:
            if plan["progress_percentage"] >= 80:
                score += 15
            elif plan["progress_percentage"] >= 60:
                score += 10
            elif plan["progress_percentage"] >= 40:
                score += 5
            elif plan["progress_percentage"] >= 20:
                score += 2

        # حداکثر امتیاز 100
        return min(score, 100)

    def create_automated_savings(
        self, user_id: int, source_account_id: int, plan_id: int, amount: Decimal
    ) -> bool:
        """ایجاد پس‌انداز خودکار از حساب به طرح"""
        try:
            from .transaction_handler import TransactionHandler
            from .account_management import AccountManager

            trans_handler = TransactionHandler()
            account_manager = AccountManager()

            # بررسی موجودی حساب
            account = account_manager.get_account_by_id(source_account_id)
            if not account or account["current_balance"] < float(amount):
                return False

            # ایجاد تراکنش
            trans_id = trans_handler.create_transaction(
                user_id=user_id,
                account_id=source_account_id,
                transaction_type="expense",
                amount=amount,
                category="پس‌انداز",
                description=f"پس‌انداز خودکار - طرح {plan_id}",
            )

            if trans_id:
                # به‌روزرسانی طرح پس‌انداز
                self.update_plan_amount(plan_id, amount, "add")
                return True

            return False

        except Exception as e:
            logger.error(f"خطا در پس‌انداز خودکار: {e}")
            return False
