# database/models.py
from dataclasses import dataclass
from datetime import datetime, date
from decimal import Decimal
from typing import Optional


@dataclass
class User:
    """مدل کاربر"""

    user_id: int
    telegram_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    registration_date: datetime = None
    trial_end_date: datetime = None
    subscription_end_date: Optional[datetime] = None
    is_active: bool = True

    def __post_init__(self):
        if self.registration_date is None:
            self.registration_date = datetime.now()

    @property
    def full_name(self) -> str:
        """نام کامل کاربر"""
        parts = []
        if self.first_name:
            parts.append(self.first_name)
        if self.last_name:
            parts.append(self.last_name)
        return " ".join(parts) or self.username or f"User {self.telegram_id}"

    @property
    def is_trial(self) -> bool:
        """آیا در دوره آزمایشی است"""
        if self.trial_end_date and self.trial_end_date > datetime.now():
            return True
        return False

    @property
    def is_subscribed(self) -> bool:
        """آیا اشتراک فعال دارد"""
        if self.subscription_end_date and self.subscription_end_date > datetime.now():
            return True
        return False


@dataclass
class BankAccount:
    """مدل حساب بانکی"""

    account_id: int
    user_id: int
    bank_name: str
    account_name: str
    initial_balance: Decimal = Decimal("0")
    current_balance: Decimal = Decimal("0")
    is_active: bool = True
    created_at: datetime = None
    updated_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.current_balance is None:
            self.current_balance = self.initial_balance

    @property
    def balance_status(self) -> str:
        """وضعیت موجودی"""
        if self.current_balance > 0:
            return "positive"
        elif self.current_balance < 0:
            return "negative"
        return "zero"

    def can_withdraw(self, amount: Decimal) -> bool:
        """آیا می‌توان مبلغ را برداشت کرد"""
        return self.current_balance >= amount


@dataclass
class Transaction:
    """مدل تراکنش"""

    transaction_id: int
    user_id: int
    account_id: int
    type: str  # 'income' or 'expense'
    amount: Decimal
    category: str
    description: Optional[str] = None
    transaction_date: datetime = None
    created_at: datetime = None

    # فیلدهای اضافی برای join
    account_name: Optional[str] = None
    bank_name: Optional[str] = None

    def __post_init__(self):
        if self.transaction_date is None:
            self.transaction_date = datetime.now()
        if self.created_at is None:
            self.created_at = datetime.now()

    @property
    def is_income(self) -> bool:
        return self.type == "income"

    @property
    def is_expense(self) -> bool:
        return self.type == "expense"

    @property
    def formatted_amount(self) -> str:
        """مبلغ فرمت‌شده"""
        from utils.persian_utils import format_amount

        return format_amount(self.amount)


@dataclass
class Check:
    """مدل چک"""

    check_id: int
    user_id: int
    account_id: int
    type: str  # 'issued' or 'received'
    amount: Decimal
    due_date: date
    recipient_issuer: Optional[str] = None
    description: Optional[str] = None
    status: str = "pending"  # 'pending', 'cleared', 'bounced', 'cancelled'
    created_at: datetime = None

    # فیلدهای اضافی برای join
    account_name: Optional[str] = None
    bank_name: Optional[str] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

    @property
    def is_overdue(self) -> bool:
        """آیا سررسید گذشته است"""
        return self.status == "pending" and self.due_date < date.today()

    @property
    def days_until_due(self) -> int:
        """روزهای باقی‌مانده تا سررسید"""
        if self.status != "pending":
            return 0
        delta = self.due_date - date.today()
        return delta.days


@dataclass
class SavingsPlan:
    """مدل طرح پس‌انداز"""

    plan_id: int
    user_id: int
    plan_name: str
    plan_type: Optional[str] = None
    target_amount: Optional[Decimal] = None
    current_amount: Decimal = Decimal("0")
    monthly_contribution: Optional[Decimal] = None
    start_date: date = None
    end_date: Optional[date] = None
    status: str = "active"  # 'active', 'completed', 'cancelled', 'paused'
    created_at: datetime = None

    def __post_init__(self):
        if self.start_date is None:
            self.start_date = date.today()
        if self.created_at is None:
            self.created_at = datetime.now()

    @property
    def progress_percentage(self) -> float:
        """درصد پیشرفت"""
        if not self.target_amount or self.target_amount == 0:
            return 0.0
        return float((self.current_amount / self.target_amount) * 100)

    @property
    def remaining_amount(self) -> Decimal:
        """مبلغ باقی‌مانده"""
        if not self.target_amount:
            return Decimal("0")
        return max(self.target_amount - self.current_amount, Decimal("0"))

    @property
    def is_completed(self) -> bool:
        """آیا تکمیل شده"""
        return self.status == "completed" or (
            self.target_amount and self.current_amount >= self.target_amount
        )


@dataclass
class Subscription:
    """مدل اشتراک"""

    subscription_id: int
    user_id: int
    plan_type: str
    amount_paid: Decimal
    start_date: datetime
    end_date: datetime
    payment_reference: Optional[str] = None
    status: str = "active"  # 'active', 'expired', 'cancelled'
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

    @property
    def is_active(self) -> bool:
        """آیا فعال است"""
        return self.status == "active" and self.end_date > datetime.now()

    @property
    def days_remaining(self) -> int:
        """روزهای باقی‌مانده"""
        if not self.is_active:
            return 0
        delta = self.end_date - datetime.now()
        return delta.days

    @property
    def is_expiring_soon(self, days: int = 7) -> bool:
        """آیا به زودی منقضی می‌شود"""
        return 0 < self.days_remaining <= days


@dataclass
class UserSettings:
    """مدل تنظیمات کاربر"""

    user_id: int
    notification_enabled: bool = True
    daily_reminder_time: Optional[str] = None
    currency: str = "تومان"
    language: str = "fa"
    created_at: datetime = None
    updated_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()


@dataclass
class Category:
    """مدل دسته‌بندی"""

    category_id: int
    name: str
    type: str  # 'income' or 'expense'
    parent_id: Optional[int] = None
    icon: Optional[str] = None
    is_default: bool = False
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class Reminder:
    """مدل یادآوری"""

    reminder_id: int
    user_id: int
    type: str
    title: str
    description: Optional[str] = None
    reminder_date: date
    is_sent: bool = False
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

    @property
    def is_due(self) -> bool:
        """آیا زمان یادآوری رسیده"""
        return not self.is_sent and self.reminder_date <= date.today()
