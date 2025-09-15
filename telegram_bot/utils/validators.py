# utils/validators.py
import re
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, date
from decimal import Decimal, InvalidOperation

# الگوهای regex
PERSIAN_TEXT_PATTERN = re.compile(r"[\u0600-\u06FF]")
CARD_NUMBER_PATTERN = re.compile(r"^\d{4}$")
PHONE_NUMBER_PATTERN = re.compile(r"^(\+98|0)?9\d{9}$")
EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_]{3,32}$")

# محدودیت‌ها
MIN_AMOUNT = Decimal("1000")  # حداقل مبلغ: 1000 ریال
MAX_AMOUNT = Decimal("10000000000")  # حداکثر مبلغ: 10 میلیارد ریال
MAX_ACCOUNTS_PER_USER = 20
MAX_TRANSACTIONS_PER_DAY = 100
MAX_ACTIVE_CHECKS = 50
MAX_ACTIVE_SAVINGS_PLANS = 10

# لیست بانک‌های معتبر
VALID_BANKS = [
    "بانک ملی",
    "بانک ملت",
    "بانک صادرات",
    "بانک تجارت",
    "بانک سپه",
    "بانک کشاورزی",
    "بانک مسکن",
    "بانک رفاه",
    "بانک پارسیان",
    "بانک پاسارگاد",
    "بانک سامان",
    "بانک سینا",
    "بانک کارآفرین",
    "بانک اقتصاد نوین",
    "بانک انصار",
    "بانک ایران زمین",
    "بانک شهر",
    "بانک دی",
    "بانک آینده",
    "بانک توسعه صادرات",
    "بانک صنعت و معدن",
    "بانک توسعه تعاون",
    "پست بانک",
    "بانک قرض‌الحسنه رسالت",
    "بانک قرض‌الحسنه مهر",
    "بانک خاورمیانه",
    "بانک حکمت",
    "بلوبانک",
]

# دسته‌بندی‌های معتبر
VALID_EXPENSE_CATEGORIES = [
    "خانه",
    "خواربار",
    "رستوران و کافی‌شاپ",
    "حمل و نقل",
    "پوشاک",
    "درمان و سلامت",
    "آموزش",
    "سرگرمی",
    "موبایل و اینترنت",
    "تعمیرات",
    "هدیه",
    "اقساط و وام",
    "مالیات",
    "سفر",
    "سایر",
]

VALID_INCOME_CATEGORIES = [
    "حقوق",
    "کسب و کار",
    "سرمایه‌گذاری",
    "اجاره",
    "پروژه",
    "هدیه",
    "سایر",
]


def validate_amount(
    amount: Any, min_amount: Decimal = MIN_AMOUNT, max_amount: Decimal = MAX_AMOUNT
) -> Tuple[bool, Optional[str]]:
    """اعتبارسنجی مبلغ

    Returns:
        (is_valid, error_message)
    """
    try:
        # تبدیل به Decimal
        if isinstance(amount, (int, float)):
            amount = Decimal(str(amount))
        elif isinstance(amount, str):
            amount = Decimal(amount)
        elif not isinstance(amount, Decimal):
            return False, "مبلغ باید عدد باشد"

        # بررسی محدوده
        if amount < min_amount:
            return False, f"مبلغ نمی‌تواند کمتر از {min_amount:,.0f} ریال باشد"

        if amount > max_amount:
            return False, f"مبلغ نمی‌تواند بیشتر از {max_amount:,.0f} ریال باشد"

        # بررسی عدد صحیح بودن (بدون اعشار)
        if amount % 1 != 0:
            return False, "مبلغ نباید اعشار داشته باشد"

        return True, None

    except (InvalidOperation, ValueError):
        return False, "مبلغ نامعتبر است"


def validate_bank_name(bank_name: str) -> Tuple[bool, Optional[str]]:
    """اعتبارسنجی نام بانک"""
    if not bank_name or not isinstance(bank_name, str):
        return False, "نام بانک الزامی است"

    bank_name = bank_name.strip()

    if len(bank_name) < 2:
        return False, "نام بانک خیلی کوتاه است"

    if len(bank_name) > 100:
        return False, "نام بانک خیلی طولانی است"

    # بررسی وجود در لیست بانک‌های معتبر (اختیاری)
    # if bank_name not in VALID_BANKS:
    #     return False, "بانک انتخابی معتبر نیست"

    return True, None


def validate_account_name(account_name: str) -> Tuple[bool, Optional[str]]:
    """اعتبارسنجی نام حساب"""
    if not account_name or not isinstance(account_name, str):
        return False, "نام حساب الزامی است"

    account_name = account_name.strip()

    if len(account_name) < 2:
        return False, "نام حساب خیلی کوتاه است"

    if len(account_name) > 100:
        return False, "نام حساب خیلی طولانی است"

    # بررسی کاراکترهای غیرمجاز
    if re.search(r"[<>\"\'\\]", account_name):
        return False, "نام حساب حاوی کاراکترهای غیرمجاز است"

    return True, None


def validate_category(
    category: str, transaction_type: str
) -> Tuple[bool, Optional[str]]:
    """اعتبارسنجی دسته‌بندی"""
    if not category or not isinstance(category, str):
        return False, "دسته‌بندی الزامی است"

    category = category.strip()

    if transaction_type == "expense":
        valid_categories = VALID_EXPENSE_CATEGORIES
    elif transaction_type == "income":
        valid_categories = VALID_INCOME_CATEGORIES
    else:
        return False, "نوع تراکنش نامعتبر است"

    if category not in valid_categories:
        return False, f"دسته‌بندی '{category}' برای {transaction_type} معتبر نیست"

    return True, None


def validate_date(
    date_value: Any, min_date: Optional[date] = None, max_date: Optional[date] = None
) -> Tuple[bool, Optional[str]]:
    """اعتبارسنجی تاریخ"""
    if date_value is None:
        return False, "تاریخ الزامی است"

    # تبدیل به date object
    if isinstance(date_value, datetime):
        date_value = date_value.date()
    elif isinstance(date_value, str):
        try:
            date_value = datetime.strptime(date_value, "%Y-%m-%d").date()
        except ValueError:
            return False, "فرمت تاریخ نامعتبر است (باید YYYY-MM-DD باشد)"
    elif not isinstance(date_value, date):
        return False, "نوع تاریخ نامعتبر است"

    # بررسی محدوده
    if min_date and date_value < min_date:
        return False, f"تاریخ نمی‌تواند قبل از {min_date} باشد"

    if max_date and date_value > max_date:
        return False, f"تاریخ نمی‌تواند بعد از {max_date} باشد"

    return True, None


def validate_card_digits(card_digits: str) -> Tuple[bool, Optional[str]]:
    """اعتبارسنجی 4 رقم آخر کارت"""
    if not card_digits:
        return True, None  # اختیاری است

    if not isinstance(card_digits, str):
        return False, "4 رقم آخر کارت باید رشته باشد"

    if not CARD_NUMBER_PATTERN.match(card_digits):
        return False, "4 رقم آخر کارت باید دقیقاً 4 عدد باشد"

    return True, None


def validate_description(
    description: str, max_length: int = 500
) -> Tuple[bool, Optional[str]]:
    """اعتبارسنجی توضیحات"""
    if not description:
        return True, None  # اختیاری است

    if not isinstance(description, str):
        return False, "توضیحات باید متن باشد"

    description = description.strip()

    if len(description) > max_length:
        return False, f"توضیحات نمی‌تواند بیشتر از {max_length} کاراکتر باشد"

    # بررسی کاراکترهای خطرناک (SQL injection)
    if re.search(r"[<>\"\'\\]", description):
        return False, "توضیحات حاوی کاراکترهای غیرمجاز است"

    return True, None


def validate_username(username: str) -> Tuple[bool, Optional[str]]:
    """اعتبارسنجی نام کاربری تلگرام"""
    if not username:
        return True, None  # اختیاری است

    if not isinstance(username, str):
        return False, "نام کاربری باید رشته باشد"

    # حذف @ اگر وجود داشته باشد
    username = username.lstrip("@")

    if not USERNAME_PATTERN.match(username):
        return False, "نام کاربری باید 3-32 کاراکتر و شامل حروف، اعداد و _ باشد"

    return True, None


def validate_phone_number(phone: str) -> Tuple[bool, Optional[str]]:
    """اعتبارسنجی شماره موبایل"""
    if not phone:
        return True, None  # اختیاری است

    if not isinstance(phone, str):
        return False, "شماره موبایل باید رشته باشد"

    # حذف فاصله‌ها
    phone = phone.replace(" ", "").replace("-", "")

    if not PHONE_NUMBER_PATTERN.match(phone):
        return False, "شماره موبایل نامعتبر است"

    return True, None


def validate_transaction_data(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """اعتبارسنجی کامل داده‌های تراکنش

    Returns:
        (is_valid, list_of_errors)
    """
    errors = []

    # بررسی فیلدهای الزامی
    required_fields = ["user_id", "account_id", "type", "amount", "category"]
    for field in required_fields:
        if field not in data or data[field] is None:
            errors.append(f"فیلد {field} الزامی است")

    if errors:
        return False, errors

    # اعتبارسنجی نوع تراکنش
    if data["type"] not in ["income", "expense"]:
        errors.append("نوع تراکنش باید income یا expense باشد")

    # اعتبارسنجی مبلغ
    is_valid, error = validate_amount(data["amount"])
    if not is_valid:
        errors.append(error)

    # اعتبارسنجی دسته‌بندی
    if "type" in data:
        is_valid, error = validate_category(data["category"], data["type"])
        if not is_valid:
            errors.append(error)

    # اعتبارسنجی توضیحات
    if "description" in data:
        is_valid, error = validate_description(data["description"])
        if not is_valid:
            errors.append(error)

    # اعتبارسنجی تاریخ
    if "transaction_date" in data:
        is_valid, error = validate_date(
            data["transaction_date"],
            min_date=date.today() - timedelta(days=365),  # حداکثر یک سال قبل
            max_date=date.today() + timedelta(days=30),  # حداکثر یک ماه آینده
        )
        if not is_valid:
            errors.append(error)

    return len(errors) == 0, errors


def sanitize_input(text: str) -> str:
    """پاکسازی ورودی برای جلوگیری از حملات"""
    if not text:
        return text

    # حذف کاراکترهای کنترلی
    text = "".join(char for char in text if ord(char) >= 32 or char in "\n\r\t")

    # محدود کردن طول
    text = text[:1000]

    # Escape کردن کاراکترهای خاص HTML
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    text = text.replace('"', "&quot;")
    text = text.replace("'", "&#39;")

    return text.strip()
