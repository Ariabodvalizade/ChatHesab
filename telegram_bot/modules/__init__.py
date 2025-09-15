# modules/__init__.py
from .user_management import UserManager
from .account_management import AccountManager
from .transaction_handler import TransactionHandler
from .ai_processor import AIProcessor
from .check_management import CheckManager
from .reports import ReportGenerator
from .savings_plans import SavingsManager
from .subscription import SubscriptionManager
from .voice_handler import VoiceHandler

__all__ = [
    "UserManager",
    "AccountManager",
    "TransactionHandler",
    "AIProcessor",
    "CheckManager",
    "ReportGenerator",
    "SavingsManager",
    "SubscriptionManager",
    "VoiceHandler",
]

# utils/__init__.py
from .persian_utils import (
    persian_to_english_digits,
    english_to_persian_digits,
    normalize_persian_text,
    parse_amount,
    format_amount,
    extract_bank_name,
    extract_card_digits,
    is_persian_text,
)

from .calendar_utils import (
    gregorian_to_jalali,
    jalali_to_gregorian,
    get_persian_date_string,
    parse_persian_date,
    get_date_range,
    format_date_range,
    get_month_name,
    get_current_persian_month_year,
)

from .formatter import (
    create_inline_keyboard,
    format_transaction_message,
    format_account_summary,
    format_check_reminder,
    format_report_summary,
    format_ai_analysis,
    format_subscription_status,
    format_error_message,
    format_success_message,
    format_confirmation_message,
    create_main_menu,
    create_help_message,
)

__all__ = [
    # persian_utils
    "persian_to_english_digits",
    "english_to_persian_digits",
    "normalize_persian_text",
    "parse_amount",
    "format_amount",
    "extract_bank_name",
    "extract_card_digits",
    "is_persian_text",
    # calendar_utils
    "gregorian_to_jalali",
    "jalali_to_gregorian",
    "get_persian_date_string",
    "parse_persian_date",
    "get_date_range",
    "format_date_range",
    "get_month_name",
    "get_current_persian_month_year",
    # formatter
    "create_inline_keyboard",
    "format_transaction_message",
    "format_account_summary",
    "format_check_reminder",
    "format_report_summary",
    "format_ai_analysis",
    "format_subscription_status",
    "format_error_message",
    "format_success_message",
    "format_confirmation_message",
    "create_main_menu",
    "create_help_message",
]

# database imports
from ..database.connection import DatabaseConnection, get_db, init_database

__all__ += ["DatabaseConnection", "get_db", "init_database"]
