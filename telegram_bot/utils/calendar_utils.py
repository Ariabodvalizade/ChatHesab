# utils/calendar_utils.py
from datetime import datetime, date, timedelta
from typing import Tuple, Optional
import jdatetime
from .persian_utils import persian_to_english_digits, english_to_persian_digits

# نام ماه‌های شمسی
PERSIAN_MONTHS = [
    "فروردین",
    "اردیبهشت",
    "خرداد",
    "تیر",
    "مرداد",
    "شهریور",
    "مهر",
    "آبان",
    "آذر",
    "دی",
    "بهمن",
    "اسفند",
]

# نام روزهای هفته
PERSIAN_WEEKDAYS = ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنج‌شنبه", "جمعه"]


def gregorian_to_jalali(g_date: date) -> jdatetime.date:
    """تبدیل تاریخ میلادی به شمسی"""
    return jdatetime.date.fromgregorian(date=g_date)


def jalali_to_gregorian(j_date: jdatetime.date) -> date:
    """تبدیل تاریخ شمسی به میلادی"""
    return j_date.togregorian()


def get_persian_date_string(g_date: date = None, include_time: bool = False) -> str:
    """دریافت تاریخ شمسی به صورت متن فارسی

    مثال: "سه‌شنبه ۱۵ مرداد ۱۴۰۳"
    """
    if g_date is None:
        g_date = date.today()

    j_date = gregorian_to_jalali(g_date)

    weekday = PERSIAN_WEEKDAYS[j_date.weekday()]
    day = english_to_persian_digits(str(j_date.day))
    month = PERSIAN_MONTHS[j_date.month - 1]
    year = english_to_persian_digits(str(j_date.year))

    date_str = f"{weekday} {day} {month} {year}"

    if include_time and isinstance(g_date, datetime):
        hour = english_to_persian_digits(f"{g_date.hour:02d}")
        minute = english_to_persian_digits(f"{g_date.minute:02d}")
        date_str += f" ساعت {hour}:{minute}"

    return date_str


def parse_persian_date(text: str) -> Optional[date]:
    """تبدیل متن فارسی تاریخ به date object

    فرمت‌های پشتیبانی شده:
    - "۱۵ مرداد ۱۴۰۳"
    - "۱۵ مرداد"
    - "فردا"
    - "دیروز"
    - "هفته آینده"
    """
    text = text.strip()
    text = persian_to_english_digits(text)

    # تاریخ‌های نسبی
    today = date.today()
    if "امروز" in text:
        return today
    elif "فردا" in text:
        return today + timedelta(days=1)
    elif "پس‌فردا" in text or "پس فردا" in text:
        return today + timedelta(days=2)
    elif "دیروز" in text:
        return today - timedelta(days=1)
    elif "پریروز" in text:
        return today - timedelta(days=2)
    elif "هفته آینده" in text or "هفته بعد" in text:
        return today + timedelta(weeks=1)
    elif "ماه آینده" in text or "ماه بعد" in text:
        return today + timedelta(days=30)

    # تلاش برای پارس کردن تاریخ کامل
    try:
        # الگوی: روز ماه سال
        parts = text.split()
        if len(parts) >= 2:
            day = None
            month = None
            year = None

            # پیدا کردن روز
            for part in parts:
                if part.isdigit() and 1 <= int(part) <= 31:
                    day = int(part)
                    break

            # پیدا کردن ماه
            for i, month_name in enumerate(PERSIAN_MONTHS):
                if month_name in text:
                    month = i + 1
                    break

            # پیدا کردن سال
            for part in parts:
                if part.isdigit() and len(part) == 4:
                    year = int(part)
                    break

            # اگر سال مشخص نشده، سال جاری
            if year is None:
                year = jdatetime.date.today().year

            if day and month:
                j_date = jdatetime.date(year, month, day)
                return j_date.togregorian()

    except:
        pass

    return None


def get_date_range(period: str) -> Tuple[date, date]:
    """دریافت بازه تاریخی بر اساس دوره

    period: 'today', 'yesterday', 'this_week', 'last_week',
            'this_month', 'last_month', 'last_3_months', etc.
    """
    today = date.today()
    j_today = gregorian_to_jalali(today)

    if period == "today":
        return today, today

    elif period == "yesterday":
        yesterday = today - timedelta(days=1)
        return yesterday, yesterday

    elif period == "last_3_days":
        start = today - timedelta(days=2)
        return start, today

    elif period == "this_week":
        # شروع هفته در ایران شنبه است
        days_since_saturday = (j_today.weekday() + 2) % 7
        start = today - timedelta(days=days_since_saturday)
        return start, today

    elif period == "last_week":
        days_since_saturday = (j_today.weekday() + 2) % 7
        this_week_start = today - timedelta(days=days_since_saturday)
        start = this_week_start - timedelta(days=7)
        end = this_week_start - timedelta(days=1)
        return start, end

    elif period == "last_7_days":
        start = today - timedelta(days=6)
        return start, today

    elif period == "last_15_days":
        start = today - timedelta(days=14)
        return start, today

    elif period == "this_month":
        # اول ماه جاری
        j_start = jdatetime.date(j_today.year, j_today.month, 1)
        start = j_start.togregorian()
        return start, today

    elif period == "last_month":
        # ماه قبل
        if j_today.month == 1:
            j_start = jdatetime.date(j_today.year - 1, 12, 1)
            j_end = jdatetime.date(j_today.year - 1, 12, 30)  # آخرین روز اسفند
        else:
            j_start = jdatetime.date(j_today.year, j_today.month - 1, 1)
            # پیدا کردن آخرین روز ماه
            if j_today.month - 1 <= 6:
                last_day = 31
            elif j_today.month - 1 <= 11:
                last_day = 30
            else:  # اسفند
                last_day = 29 if j_today.isleap() else 30
            j_end = jdatetime.date(j_today.year, j_today.month - 1, last_day)

        return j_start.togregorian(), j_end.togregorian()

    elif period == "last_30_days":
        start = today - timedelta(days=29)
        return start, today

    elif period == "last_3_months":
        start = today - timedelta(days=89)
        return start, today

    elif period == "last_6_months":
        start = today - timedelta(days=179)
        return start, today

    elif period == "this_year":
        # اول فروردین امسال
        j_start = jdatetime.date(j_today.year, 1, 1)
        start = j_start.togregorian()
        return start, today

    elif period == "last_year":
        # سال قبل
        j_start = jdatetime.date(j_today.year - 1, 1, 1)
        j_end = jdatetime.date(
            j_today.year - 1,
            12,
            29 if jdatetime.date(j_today.year - 1, 1, 1).isleap() else 30,
        )
        return j_start.togregorian(), j_end.togregorian()

    else:
        # پیش‌فرض: امروز
        return today, today


def format_date_range(start_date: date, end_date: date) -> str:
    """فرمت‌دهی بازه تاریخی به فارسی"""
    if start_date == end_date:
        return get_persian_date_string(start_date)

    j_start = gregorian_to_jalali(start_date)
    j_end = gregorian_to_jalali(end_date)

    start_str = f"{english_to_persian_digits(str(j_start.day))} {PERSIAN_MONTHS[j_start.month - 1]}"
    end_str = (
        f"{english_to_persian_digits(str(j_end.day))} {PERSIAN_MONTHS[j_end.month - 1]}"
    )

    # اگر سال‌ها متفاوت باشند
    if j_start.year != j_end.year:
        start_str += f" {english_to_persian_digits(str(j_start.year))}"
        end_str += f" {english_to_persian_digits(str(j_end.year))}"
    else:
        end_str += f" {english_to_persian_digits(str(j_end.year))}"

    return f"از {start_str} تا {end_str}"


def get_month_name(month_number: int) -> str:
    """دریافت نام ماه شمسی"""
    if 1 <= month_number <= 12:
        return PERSIAN_MONTHS[month_number - 1]
    return ""


def get_current_persian_month_year() -> Tuple[int, int]:
    """دریافت ماه و سال جاری شمسی"""
    j_today = jdatetime.date.today()
    return j_today.month, j_today.year
