# utils/persian_utils.py
import re
from typing import Union, Optional

# نگاشت اعداد فارسی به انگلیسی
PERSIAN_TO_ENGLISH_DIGITS = {
    "۰": "0",
    "۱": "1",
    "۲": "2",
    "۳": "3",
    "۴": "4",
    "۵": "5",
    "۶": "6",
    "۷": "7",
    "۸": "8",
    "۹": "9",
}

# نگاشت اعداد انگلیسی به فارسی
ENGLISH_TO_PERSIAN_DIGITS = {v: k for k, v in PERSIAN_TO_ENGLISH_DIGITS.items()}

# کلمات رایج برای مبالغ
AMOUNT_WORDS = {
    "تومان": 1,
    "تومن": 1,
    "هزار": 1000,
    "هزارتومان": 1000,
    "هزارتومن": 1000,
    "هزار تومان": 1000,
    "هزار تومن": 1000,
    "میلیون": 1000000,
    "میلیون تومان": 1000000,
    "میلیون تومن": 1000000,
    "میلیارد": 1000000000,
    "میلیارد تومان": 1000000000,
    "میلیارد تومن": 1000000000,
}


def persian_to_english_digits(text: str) -> str:
    """تبدیل اعداد فارسی به انگلیسی"""
    if not text:
        return text

    for persian, english in PERSIAN_TO_ENGLISH_DIGITS.items():
        text = text.replace(persian, english)
    return text


def english_to_persian_digits(text: str) -> str:
    """تبدیل اعداد انگلیسی به فارسی"""
    if not text:
        return text

    for english, persian in ENGLISH_TO_PERSIAN_DIGITS.items():
        text = text.replace(english, persian)
    return text


def normalize_persian_text(text: str) -> str:
    """نرمال‌سازی متن فارسی"""
    if not text:
        return text

    # تبدیل ی و ک عربی به فارسی
    text = text.replace("ي", "ی").replace("ك", "ک")

    # حذف فاصله‌های اضافی
    text = " ".join(text.split())

    return text


def parse_amount(text: str) -> Optional[int]:
    """تشخیص و تبدیل مبلغ از متن فارسی به عدد

    مثال‌ها:
    - "۱۵۰ تومن" -> 150000 (۱۵۰ هزار تومان)
    - "۲ میلیون و ۵۶۰ هزار تومان" -> 2560000
    - "۸۹۰ هزارتومان" -> 890000
    - "۲۵۶۰۰۰۰" -> 2560000
    """
    if not text:
        return None

    # نرمال‌سازی متن
    text = normalize_persian_text(text)
    text = persian_to_english_digits(text)

    # حذف کاراکترهای اضافی
    text = text.replace(",", "").replace("،", "")

    # الگوهای مختلف برای تشخیص مبلغ
    patterns = [
        # عدد + میلیون + و + عدد + هزار
        r"(\d+)\s*میلیون(?:\s*و\s*(\d+)\s*هزار)?",
        # عدد + هزار
        r"(\d+)\s*هزار",
        # عدد + تومن/تومان (بدون واحد دیگر)
        r"(\d+)\s*توم[نا]ن?\s*(?!هزار|میلیون)",
        # فقط عدد
        r"(\d+)",
    ]

    amount = None

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            if "میلیون" in pattern:
                millions = int(match.group(1))
                thousands = int(match.group(2)) if match.group(2) else 0
                amount = (millions * 1000000) + (thousands * 1000)
                break
            elif "هزار" in pattern:
                amount = int(match.group(1)) * 1000
                break
            elif "تومن" in pattern or "تومان" in pattern:
                # اگر مبلغ کمتر از 1000 باشد، احتمالاً منظور هزار تومان است
                value = int(match.group(1))
                if value < 1000:
                    amount = value * 1000
                else:
                    amount = value
                break
            else:
                # فقط عدد
                value = int(match.group(1))
                # اگر عدد 6 رقمی یا بیشتر باشد، احتمالاً مبلغ کامل است
                if value >= 100000:
                    amount = value
                # اگر عدد کمتر از 10000 باشد، احتمالاً منظور هزار تومان است
                elif value < 10000:
                    amount = value * 1000
                else:
                    amount = value

    return amount


def format_amount(amount: Union[int, float], with_currency: bool = True) -> str:
    """فرمت‌دهی مبلغ به صورت فارسی

    مثال: 2560000 -> "۲,۵۶۰,۰۰۰ تومان"
    """
    if amount is None:
        return ""

    # تبدیل به int اگر float است
    amount = int(amount)

    # جداسازی رقم‌ها با کاما
    formatted = f"{amount:,}"

    # تبدیل به اعداد فارسی
    formatted = english_to_persian_digits(formatted)

    # اضافه کردن واحد پول
    if with_currency:
        formatted += " تومان"

    return formatted


def extract_bank_name(text: str) -> Optional[str]:
    """استخراج نام بانک از متن"""

    # لیست بانک‌های رایج در ایران
    banks = {
        "ملی": "بانک ملی",
        "ملت": "بانک ملت",
        "صادرات": "بانک صادرات",
        "تجارت": "بانک تجارت",
        "سپه": "بانک سپه",
        "کشاورزی": "بانک کشاورزی",
        "مسکن": "بانک مسکن",
        "رفاه": "بانک رفاه",
        "پارسیان": "بانک پارسیان",
        "پاسارگاد": "بانک پاسارگاد",
        "سامان": "بانک سامان",
        "سینا": "بانک سینا",
        "کارآفرین": "بانک کارآفرین",
        "اقتصاد نوین": "بانک اقتصاد نوین",
        "انصار": "بانک انصار",
        "ایران زمین": "بانک ایران زمین",
        "شهر": "بانک شهر",
        "دی": "بانک دی",
        "آینده": "بانک آینده",
        "توسعه صادرات": "بانک توسعه صادرات",
        "صنعت و معدن": "بانک صنعت و معدن",
        "توسعه تعاون": "بانک توسعه تعاون",
        "پست بانک": "پست بانک",
        "قرض الحسنه رسالت": "بانک قرض‌الحسنه رسالت",
        "قرض الحسنه مهر": "بانک قرض‌الحسنه مهر",
        "خاورمیانه": "بانک خاورمیانه",
        "حکمت": "بانک حکمت",
        "بلو": "بلوبانک",
        "بلوبانک": "بلوبانک",
    }

    text = normalize_persian_text(text.lower())

    for keyword, bank_name in banks.items():
        if keyword in text:
            return bank_name

    return None


def extract_card_digits(text: str) -> Optional[str]:
    """استخراج 4 رقم آخر کارت از متن"""
    # الگوی 4 رقم
    pattern = r"\b(\d{4})\b"
    match = re.search(pattern, persian_to_english_digits(text))

    if match:
        return match.group(1)

    return None


def is_persian_text(text: str) -> bool:
    """بررسی فارسی بودن متن"""
    if not text:
        return False

    # حداقل 30% حروف باید فارسی باشد
    persian_chars = len(re.findall(r"[\u0600-\u06FF]", text))
    total_chars = len(re.findall(r"\w", text))

    if total_chars == 0:
        return False

    return (persian_chars / total_chars) > 0.3
