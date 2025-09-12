# modules/reports.py
import logging
from typing import Dict, List, Optional
from datetime import date, datetime, timedelta
from database.connection import get_db
from modules.transaction_handler import TransactionHandler
from modules.account_management import AccountManager
from modules.check_management import CheckManager
from modules.ai_processor import AIProcessor
from utils.calendar_utils import get_date_range, format_date_range

logger = logging.getLogger(__name__)


class ReportGenerator:
    def __init__(self):
        self.db = get_db()
        self.transaction_handler = TransactionHandler()
        self.account_manager = AccountManager()
        self.check_manager = CheckManager()
        self.ai_processor = AIProcessor()

    def generate_period_report(self, user_id: int, period: str) -> Dict:
        """تولید گزارش برای یک دوره زمانی مشخص

        period: 'today', 'yesterday', 'this_week', 'last_week',
                'this_month', 'last_month', 'last_3_months', etc.
        """
        # دریافت بازه تاریخی
        start_date, end_date = get_date_range(period)

        # دریافت تراکنش‌ها
        transactions = self.transaction_handler.get_user_transactions(
            user_id=user_id, start_date=start_date, end_date=end_date
        )

        # خلاصه تراکنش‌ها
        summary = self.transaction_handler.get_transactions_summary(
            user_id=user_id, start_date=start_date, end_date=end_date
        )

        # خلاصه بر اساس دسته‌بندی
        income_by_category = self.transaction_handler.get_category_summary(
            user_id=user_id,
            transaction_type="income",
            start_date=start_date,
            end_date=end_date,
        )

        expense_by_category = self.transaction_handler.get_category_summary(
            user_id=user_id,
            transaction_type="expense",
            start_date=start_date,
            end_date=end_date,
        )

        # آمار حساب‌ها
        accounts = self.account_manager.get_user_accounts(user_id)
        total_balance = sum(acc["current_balance"] for acc in accounts)

        # آمار چک‌ها
        checks = self.check_manager.get_user_checks(
            user_id=user_id, start_date=start_date, end_date=end_date
        )

        report = {
            "period": period,
            "period_name": format_date_range(start_date, end_date),
            "start_date": start_date,
            "end_date": end_date,
            "summary": summary,
            "incomes": income_by_category,
            "expenses": expense_by_category,
            "transactions": transactions,
            "total_balance": total_balance,
            "checks_count": len(checks),
            "top_expenses": self._get_top_categories(expense_by_category, 5),
            "top_incomes": self._get_top_categories(income_by_category, 5),
        }

        return report

    def generate_comparative_report(
        self, user_id: int, current_period: str, previous_period: str = None
    ) -> Dict:
        """تولید گزارش مقایسه‌ای بین دو دوره"""
        # گزارش دوره جاری
        current_report = self.generate_period_report(user_id, current_period)

        # تعیین دوره قبلی اگر مشخص نشده
        if not previous_period:
            period_mapping = {
                "this_week": "last_week",
                "this_month": "last_month",
                "last_month": "last_2_months",
                "last_3_months": "last_6_months",
            }
            previous_period = period_mapping.get(current_period, "last_month")

        # گزارش دوره قبلی
        previous_report = self.generate_period_report(user_id, previous_period)

        # محاسبه تغییرات
        comparison = {
            "current": current_report,
            "previous": previous_report,
            "changes": {
                "income": {
                    "amount": current_report["summary"]["income"]["total"]
                    - previous_report["summary"]["income"]["total"],
                    "percentage": self._calculate_percentage_change(
                        previous_report["summary"]["income"]["total"],
                        current_report["summary"]["income"]["total"],
                    ),
                },
                "expense": {
                    "amount": current_report["summary"]["expense"]["total"]
                    - previous_report["summary"]["expense"]["total"],
                    "percentage": self._calculate_percentage_change(
                        previous_report["summary"]["expense"]["total"],
                        current_report["summary"]["expense"]["total"],
                    ),
                },
                "balance": {
                    "amount": current_report["summary"]["balance"]
                    - previous_report["summary"]["balance"],
                    "percentage": self._calculate_percentage_change(
                        previous_report["summary"]["balance"],
                        current_report["summary"]["balance"],
                    ),
                },
            },
        }

        return comparison

    def generate_ai_analysis(self, user_id: int, period: str = "last_month") -> Dict:
        """تولید تحلیل هوشمند با استفاده از AI"""
        # دریافت گزارش دوره
        report = self.generate_period_report(user_id, period)

        # آماده‌سازی داده‌ها برای AI
        financial_data = {
            "period": report["period_name"],
            "incomes": report["incomes"],
            "expenses": report["expenses"],
            "total_income": report["summary"]["income"]["total"],
            "total_expense": report["summary"]["expense"]["total"],
            "balance": report["summary"]["balance"],
            "savings_rate": self._calculate_savings_rate(
                report["summary"]["income"]["total"],
                report["summary"]["expense"]["total"],
            ),
        }

        # دریافت تحلیل از AI
        ai_analysis = self.ai_processor.analyze_financial_data(financial_data)

        # ترکیب با گزارش
        report["ai_analysis"] = ai_analysis

        return report

    def generate_monthly_summary(self, user_id: int, year: int, month: int) -> Dict:
        """گزارش خلاصه ماهانه"""
        # محاسبه اول و آخر ماه
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)

        # دریافت داده‌ها
        transactions = self.transaction_handler.get_user_transactions(
            user_id=user_id, start_date=start_date, end_date=end_date
        )

        # گروه‌بندی بر اساس روز
        daily_summary = {}
        for trans in transactions:
            day = trans["transaction_date"].day
            if day not in daily_summary:
                daily_summary[day] = {"income": 0, "expense": 0}

            if trans["type"] == "income":
                daily_summary[day]["income"] += trans["amount"]
            else:
                daily_summary[day]["expense"] += trans["amount"]

        # خلاصه ماهانه
        summary = self.transaction_handler.get_transactions_summary(
            user_id=user_id, start_date=start_date, end_date=end_date
        )

        return {
            "year": year,
            "month": month,
            "summary": summary,
            "daily_summary": daily_summary,
            "transactions_count": len(transactions),
        }

    def generate_category_trend(
        self, user_id: int, category: str, months: int = 6
    ) -> Dict:
        """روند یک دسته‌بندی در چند ماه اخیر"""
        trends = []
        today = date.today()

        for i in range(months):
            # محاسبه ماه
            month_offset = today.month - i
            year = today.year

            if month_offset <= 0:
                month_offset += 12
                year -= 1

            # بازه ماه
            start_date = date(year, month_offset, 1)
            if month_offset == 12:
                end_date = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = date(year, month_offset + 1, 1) - timedelta(days=1)

            # دریافت تراکنش‌های دسته
            transactions = self.transaction_handler.get_user_transactions(
                user_id=user_id,
                start_date=start_date,
                end_date=end_date,
                category=category,
            )

            total = sum(t["amount"] for t in transactions)
            count = len(transactions)

            trends.append(
                {
                    "year": year,
                    "month": month_offset,
                    "total": total,
                    "count": count,
                    "average": total / count if count > 0 else 0,
                }
            )

        # معکوس کردن برای نمایش از قدیم به جدید
        trends.reverse()

        return {"category": category, "months": months, "trends": trends}

    def _get_top_categories(self, categories: Dict, limit: int = 5) -> List[Dict]:
        """دریافت دسته‌بندی‌های برتر"""
        sorted_categories = sorted(
            categories.items(), key=lambda x: x[1]["total"], reverse=True
        )[:limit]

        return [
            {"category": cat[0], "total": cat[1]["total"], "count": cat[1]["count"]}
            for cat in sorted_categories
        ]

    def _calculate_percentage_change(self, old_value: float, new_value: float) -> float:
        """محاسبه درصد تغییر"""
        if old_value == 0:
            return 100.0 if new_value > 0 else 0.0

        return ((new_value - old_value) / abs(old_value)) * 100

    def _calculate_savings_rate(self, income: float, expense: float) -> float:
        """محاسبه نرخ پس‌انداز"""
        if income == 0:
            return 0.0

        return ((income - expense) / income) * 100
