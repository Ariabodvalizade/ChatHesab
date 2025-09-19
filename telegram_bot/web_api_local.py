# web_api_local.py
"""
FastAPI web server using SQLite for local development
"""

import logging
import sys
from fastapi import FastAPI, HTTPException, Depends, status, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal
import os
import tempfile

# Import local database components
from .database.connection_local import get_local_db, init_local_database

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Finance Bot Web API (Local)",
    description="Local development REST API for Finance Bot functionality",
    version="1.0.0",
)

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        # Common Vite defaults (kept explicit for clarity)
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:5176",
        "http://localhost:5177",
        "http://localhost:5178",
        "http://localhost:5179",
        "http://localhost:5180",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
        "http://127.0.0.1:5176",
        "http://127.0.0.1:5177",
        "http://127.0.0.1:5178",
        "http://127.0.0.1:5179",
        "http://127.0.0.1:5180",
    ],
    # Accept any localhost/127.0.0.1 port (e.g., Vite may use 517x, 5179, etc.)
    allow_origin_regex=r"^http://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Security
security = HTTPBearer()

# Initialize database
db = get_local_db()


# Pydantic models for API
class UserCreate(BaseModel):
    telegram_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class PhoneAuthRequest(BaseModel):
    phone_number: str


class OTPVerifyRequest(BaseModel):
    phone_number: str
    otp_code: str


class AccountCreate(BaseModel):
    bank_name: str
    account_name: str
    initial_balance: float = 0

class AccountUpdate(BaseModel):
    bank_name: Optional[str] = None
    account_name: Optional[str] = None
    initial_balance: Optional[float] = None
    current_balance: Optional[float] = None


class TransactionCreate(BaseModel):
    account_id: int
    transaction_type: str  # 'income' or 'expense'
    amount: float
    category: str
    description: Optional[str] = None
    transaction_date: Optional[str] = None


class CheckCreate(BaseModel):
    account_id: int
    type: str  # 'issued' or 'received'
    amount: float
    due_date: str
    recipient_issuer: Optional[str] = None
    description: Optional[str] = None


class SavingsPlanCreate(BaseModel):
    plan_name: str
    plan_type: Optional[str] = None
    target_amount: Optional[float] = None
    monthly_contribution: Optional[float] = None
    end_date: Optional[str] = None


class ProcessMessageRequest(BaseModel):
    message: str


# Auth dependency (simplified for demo)
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Simple auth - in production, implement proper JWT validation"""
    token = credentials.credentials
    # For demo, we'll use token as user_id (telegram_id)
    try:
        telegram_id = int(token)
        # Get user from database
        user = db.execute_query(
            "SELECT * FROM users WHERE telegram_id = ?", (telegram_id,), fetch_one=True
        )
        if user:
            return user
        raise HTTPException(status_code=404, detail="User not found")
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        )


# Helper functions
def parse_amount(amount_str: str) -> float:
    """Parse Persian/English numbers and amounts"""
    if isinstance(amount_str, (int, float)):
        return float(amount_str)

    # Simple number parsing for demo
    import re

    numbers = re.findall(r"\d+", str(amount_str).replace("،", "").replace(",", ""))
    if numbers:
        return float("".join(numbers))
    return 0.0


def process_message_with_ai(message: str, accounts: List[Dict]) -> Dict:
    """Enhanced AI message processing using Google Gemini"""
    try:
        import google.generativeai as genai
        from .config_local import GEMINI_API_KEY, GEMINI_MODEL

        # Configure Gemini API
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel(GEMINI_MODEL)

        # Prepare accounts info
        accounts_info = ""
        if accounts:
            accounts_info = "حساب‌های کاربر:\n"
            for acc in accounts:
                accounts_info += f"- {acc['bank_name']} ({acc['account_name']}) - ID: {acc['account_id']}\n"

        # Create the prompt
        prompt = f"""
تو یک دستیار مالی هوشمند هستی که پیام‌های فارسی کاربران را تحلیل می‌کنی.

{accounts_info}

پیام کاربر: "{message}"

این پیام را تحلیل کن و اطلاعات زیر را به صورت JSON استخراج کن:

{{
    "type": "transaction" یا "check" یا "account" یا "query" یا "unknown",
    "action": "create" یا "update" یا "delete" (اگر type=account باشد)،
    "transaction_type": "income" یا "expense" (اگر نوع transaction باشد),
    "amount": عدد (مثلاً ۱۵۰ هزار = 150000),
    "amount_text": متن اصلی مبلغ که کاربر نوشته,
    "category": دسته‌بندی مناسب به فارسی,
    "bank_name": نام بانک (اگر ذکر شده),
    "account_name": نام حساب (اگر ذکر شده),
    "account_id": شناسه حساب (اگر مشخص است),
    "initial_balance": موجودی اولیه حساب (اگر type=account و action=create باشد),
    "description": توضیحات تراکنش,
    "date": تاریخ امروز به فرمت YYYY-MM-DD,
    "check_type": "issued" یا "received" (اگر نوع check باشد),
    "recipient_issuer": نام گیرنده یا صادرکننده چک,
    "response_message": پیام پاسخ مناسب به فارسی برای کاربر,
    "confidence": میزان اطمینان از 0 تا 1
}}

نکات مهم:
1. اگر کاربر "تومن" یا "تومان" گفته و عدد کمتر از 10000 است، احتمالاً منظورش هزار تومان است
2. دسته‌بندی‌های رایج: خانه، خواربار، رستوران و کافی‌شاپ، حمل و نقل، پوشاک، درمان و سلامت، آموزش، سرگرمی، موبایل و اینترنت، تعمیرات، هدیه، اقساط و وام، مالیات، سفر، حقوق، کسب و کار، سرمایه‌گذاری، اجاره، پروژه، سایر
3. برای تشخیص نوع (درآمد/هزینه) به کلمات کلیدی مثل: خرید، پرداخت، هزینه، برداشت (expense) یا دریافت، حقوق، درآمد، واریز (income) توجه کن
4. اگر اطلاعاتی مشخص نیست، null بگذار
5. در response_message پاسخ مناسب و دوستانه به فارسی بنویس
6. اگر عبارت‌هایی مانند "بساز"، "ایجاد کن"، "درست کن" همراه با کلمه "حساب" آمده بود و نام بانک (مثل ملی) یا نام حساب (مثل ۱۸۹۱) و مبلغ اولیه (مثل ۵۵۰ هزارتومن) ذکر شده بود، خروجی را با type=account و action=create برگردان و فیلدهای bank_name, account_name, initial_balance را پر کن

فقط JSON را برگردان، توضیح اضافی نده.
"""

        # Send to Gemini
        response = model.generate_content(prompt)
        response_text = response.text.strip()

        # Parse JSON response
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]

        import json

        result = json.loads(response_text.strip())

        # Validate and complete the result
        if result.get("type") == "transaction":
            # Select default account if not specified
            if not result.get("account_id") and accounts:
                result["account_id"] = accounts[0]["account_id"]
                result["account_name"] = accounts[0]["account_name"]

            # Set default date
            if not result.get("date"):
                from datetime import datetime

                result["date"] = datetime.now().strftime("%Y-%m-%d")

            # Set default category
            if not result.get("category"):
                result["category"] = "سایر"

        result["success"] = True
        return result

    except Exception as e:
        logger.error(f"Error in AI processing: {e}")
        return {
            "success": False,
            "error": "خطا در پردازش هوشمند پیام",
            "response_message": "متأسفانه نتوانستم پیام شما را درک کنم. لطفاً دوباره تلاش کنید.",
        }


def process_message_with_fallback(message: str, accounts: List[Dict]) -> Dict:
    """Process message with AI fallback to simple parsing"""
    try:
        # First try AI processing with timeout
        import signal
        import threading
        from queue import Queue

        def ai_worker(queue):
            try:
                result = process_message_with_ai(message, accounts)
                queue.put(("success", result))
            except Exception as e:
                queue.put(("error", str(e)))

        # Try AI with 10 second timeout
        queue = Queue()
        ai_thread = threading.Thread(target=ai_worker, args=(queue,))
        ai_thread.daemon = True
        ai_thread.start()
        ai_thread.join(timeout=10)

        if not queue.empty():
            status, result = queue.get()
            if status == "success" and result.get("success"):
                return result

        logger.warning("AI processing failed or timed out, using fallback")

        # Fallback to simple processing
        return process_message_simple_enhanced(message, accounts)

    except Exception as e:
        logger.error(f"Error in message processing: {e}")
        return process_message_simple_enhanced(message, accounts)


def process_message_simple_enhanced(message: str, accounts: List[Dict]) -> Dict:
    """Enhanced simple message processing with better response messages including account ops"""
    import re
    from datetime import datetime

    # --- Detect account operations first ---
    msg = message.strip()
    msg_sp = msg.replace("\u200c", " ")
    has_hesab = any(word in msg_sp for word in ["حساب", "اکانت", "حساب بانکی"])  # Persian account
    create_triggers = ["بساز", "بسازی", "ایجاد", "درست کن", "اضافه کن", "بسازید", "بسازی واسم", "بساخت"]
    delete_triggers = ["حذف", "پاک", "پاک کن", "حذف کن", "حذفش", "پاکش", "غیرفعال"]
    update_triggers = ["ویرایش", "تغییر", "تغییر نام", "عوض کن", "rename"]

    # Known bank names (simplified list)
    bank_names = [
        "ملی", "ملت", "صادرات", "تجارت", "پاسارگاد", "پارسیان", "سامان", "مسکن", "کشاورزی", "رفاه",
        "اقتصاد نوین", "آینده", "شهر", "دی", "صنعت و معدن", "قوامین", "انصار"
    ]

    def convert_persian_digits(s: str) -> str:
        trans = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")
        return s.translate(trans)

    def extract_amount_and_account_number(text: str):
        # Find all numbers with positions
        results = []
        for m in re.finditer(r"[\d۰-۹]+", text):
            num_text = m.group(0)
            start = m.start()
            end = m.end()
            after = text[end:end+12]
            before = text[max(0, start-12):start]
            results.append((num_text, start, end, before, after))
        amount = None
        account_num = None
        for num, s, e, before, after in results:
            context = (before + after)
            if any(k in context for k in ["تومن", "تومان", "هزار", "میلیون", "میلیارد"]):
                # Likely amount
                amount = num
            else:
                # Likely account label/number
                if account_num is None:
                    account_num = num
        return amount, account_num

    def detect_bank_name(text: str) -> Optional[str]:
        # Try phrases like "بانک ملی"
        m = re.search(r"بانک\s+([\S\u0600-\u06FF]+)", text)
        if m:
            cand = m.group(1)
            for b in bank_names:
                if b in cand or cand in b:
                    return b
            return cand
        for b in bank_names:
            if b in text:
                return b
        return None

    if has_hesab and any(t in msg_sp for t in create_triggers + delete_triggers + update_triggers):
        action = (
            "create" if any(t in msg_sp for t in create_triggers) else
            "delete" if any(t in msg_sp for t in delete_triggers) else
            "update"
        )

        bank_name = detect_bank_name(msg_sp)
        amount_num, account_num = extract_amount_and_account_number(msg_sp)

        # Determine initial balance
        init_balance = None
        if amount_num is not None:
            amount_val = float(convert_persian_digits(amount_num))
            # Scale if thousand/million mentioned near the amount text
            if any(k in msg_sp for k in ["هزار", "هزارتومن", "هزار تومان"]):
                amount_val *= 1000
            if "میلیون" in msg_sp:
                amount_val *= 1_000_000
            if "میلیارد" in msg_sp:
                amount_val *= 1_000_000_000
            init_balance = amount_val

        # Try to resolve account by name/number for update/delete
        matched_account = None
        if action in ("update", "delete"):
            # Match by account number (digits) or by bank and name
            if account_num:
                acc_num_norm = convert_persian_digits(account_num)
                for acc in accounts:
                    if acc_num_norm in str(acc.get("account_name", "")):
                        matched_account = acc
                        break
            if matched_account is None and bank_name:
                for acc in accounts:
                    if bank_name in str(acc.get("bank_name", "")):
                        matched_account = acc
                        break

        response_message = None
        if action == "create":
            nfmt = f"{int(init_balance):,} تومان" if init_balance is not None else "بدون موجودی اولیه"
            response_message = (
                f"✅ درخواست ساخت حساب ثبت شد:\n"
                f"بانک: {bank_name or 'نامشخص'} | نام حساب: {convert_persian_digits(account_num) if account_num else 'نامشخص'}\n"
                f"موجودی اولیه: {nfmt}\n\nبرای تأیید، دکمه تایید را بزنید."
            )
            return {
                "success": True,
                "type": "account",
                "action": "create",
                "bank_name": bank_name,
                "account_name": convert_persian_digits(account_num) if account_num else None,
                "initial_balance": init_balance or 0,
                "response_message": response_message,
                "confidence": 0.8,
            }
        elif action == "delete":
            if matched_account:
                response_message = (
                    f"⚠️ حذف حساب تایید شود؟\nبانک: {matched_account['bank_name']} | نام حساب: {matched_account['account_name']}"
                )
                return {
                    "success": True,
                    "type": "account",
                    "action": "delete",
                    "account_id": matched_account["account_id"],
                    "bank_name": matched_account["bank_name"],
                    "account_name": matched_account["account_name"],
                    "response_message": response_message,
                }
            else:
                return {
                    "success": False,
                    "type": "account",
                    "action": "delete",
                    "error": "حساب مورد نظر پیدا نشد. لطفاً نام بانک و نام حساب را دقیق‌تر بگویید.",
                    "response_message": "حساب مورد نظر پیدا نشد.",
                }
        else:  # update
            payload = {
                "bank_name": bank_name,
                "account_name": convert_persian_digits(account_num) if account_num else None,
                "initial_balance": init_balance,
            }
            if matched_account:
                response_message = (
                    f"✏️ ویرایش حساب تایید شود؟\nاز: {matched_account['bank_name']} - {matched_account['account_name']}\n"
                    f"به: {payload['bank_name'] or matched_account['bank_name']} - {payload['account_name'] or matched_account['account_name']}"
                )
                return {
                    "success": True,
                    "type": "account",
                    "action": "update",
                    "account_id": matched_account["account_id"],
                    **payload,
                    "response_message": response_message,
                }
            else:
                return {
                    "success": False,
                    "type": "account",
                    "action": "update",
                    **payload,
                    "error": "حساب برای ویرایش پیدا نشد. لطفاً نام حساب/بانک را دقیق‌تر بگویید.",
                    "response_message": "حساب برای ویرایش پیدا نشد.",
                }

    # --- Transaction detection (existing) ---
    
    # Extract amount
    numbers = re.findall(r"\d+", message.replace("،", "").replace(",", ""))
    if not numbers:
        return {
            "success": False,
            "error": "مبلغ مشخص نیست",
            "response_message": "متأسفانه نتوانستم مبلغ را تشخیص دهم. لطفاً مبلغ را به صورت عدد بنویسید.",
        }

    amount = float("".join(numbers))

    # Smart amount detection
    if amount < 1000 and any(word in message for word in ["تومان", "تومن"]):
        amount *= 1000  # Convert to full amount
    elif "هزار" in message:
        amount *= 1000
    elif "میلیون" in message:
        amount *= 1000000

    # Determine transaction type with better keywords
    expense_keywords = [
        "خرید",
        "پرداخت",
        "هزینه",
        "خریدم",
        "دادم",
        "برداشت",
        "پول دادم",
    ]
    income_keywords = ["دریافت", "حقوق", "درآمد", "گرفتم", "واریز", "حقوق گرفتم"]

    transaction_type = "expense"  # Default
    for keyword in income_keywords:
        if keyword in message:
            transaction_type = "income"
            break

    # Enhanced category detection with more detailed categories
    category = "سایر"
    category_map = {
        # Food & Dining
        "رستوران و کافی‌شاپ": [
            "غذا",
            "رستوران",
            "کافه",
            "قهوه",
            "چای",
            "کافی شاپ",
            "نوشیدنی",
            "شام",
            "ناهار",
            "صبحانه",
            "پیتزا",
            "برگر",
            "ساندویچ",
            "کباب",
        ],
        "خواربار و سوپرمارکت": [
            "خرید",
            "سوپر",
            "بازار",
            "میوه",
            "سبزی",
            "گوشت",
            "مرغ",
            "لبنیات",
            "نان",
            "برنج",
            "روغن",
        ],
        "میان‌وعده و تنقلات": ["شیرینی", "بستنی", "چیپس", "شکلات", "آبنبات", "آجیل"],
        # Transportation
        "بنزین و سوخت": ["بنزین", "گازوییل", "سوخت", "پمپ بنزین", "گاز"],
        "حمل‌ونقل عمومی": [
            "تاکسی",
            "اتوبوس",
            "مترو",
            "تراموا",
            "سواری",
            "کرایه",
            "بلیط",
        ],
        "تعمیر و نگهداری خودرو": ["تعمیر", "تعمیرگاه", "روغن موتور", "لاستیک", "باتری"],
        "پارکینگ و عوارض": ["پارکینگ", "عوارض", "جریمه", "خلافی"],
        # Housing
        "اجاره مسکن": ["اجاره", "رهن", "ودیعه"],
        "قبوض و هزینه‌های خانه": [
            "آب",
            "برق",
            "گاز",
            "تلفن ثابت",
            "اینترنت خانگی",
            "قبض",
        ],
        "تعمیرات منزل": ["تعمیرات خانه", "لوله کشی", "برقکاری", "نقاشی"],
        "وسایل منزل": ["مبلمان", "یخچال", "ماشین لباسشویی", "تلویزیون"],
        # Shopping & Personal
        "پوشاک و کفش": [
            "لباس",
            "پوشاک",
            "کفش",
            "کیف",
            "ساعت",
            "عینک",
            "شلوار",
            "پیراهن",
        ],
        "آرایشی و بهداشتی": ["شامپو", "صابون", "خمیردندان", "آرایش", "عطر", "کرم"],
        # Health & Medical
        "دارو و درمان": ["دارو", "داروخانه", "قرص", "شربت", "آمپول", "ویتامین"],
        "ویزیت و خدمات پزشکی": ["دکتر", "پزشک", "ویزیت", "آزمایش", "دندانپزشک"],
        "بیمارستان و درمانگاه": ["بیمارستان", "درمانگاه", "اورژانس"],
        # Technology & Communication
        "موبایل و شارژ": ["شارژ", "موبایل", "گوشی", "سیم کارت", "بسته اینترنت"],
        "اینترنت و فناوری": ["اینترنت", "وای فای", "لپ تاپ", "تبلت"],
        # Entertainment
        "سینما و تئاتر": ["سینما", "تئاتر", "کنسرت", "نمایش"],
        "ورزش و تناسب اندام": ["باشگاه", "ورزش", "تناسب اندام", "شنا"],
        # Income Categories
        "حقوق و دستمزد": ["حقوق", "مزد", "پاداش", "عیدی", "اضافه کار"],
        "کسب‌وکار و فروش": ["فروش", "تجارت", "کسب و کار"],
        "سرمایه‌گذاری و سود": ["سود", "سهام", "سپرده", "سرمایه گذاری"],
        "هدیه و کمک مالی": ["هدیه پولی", "کمک مالی", "عیدی گرفتن"],
    }

    for cat, keywords in category_map.items():
        if any(word in message for word in keywords):
            category = cat
            break

    # Select account (try to detect from message)
    def detect_bank(text: str) -> Optional[str]:
        banks = [
            "ملی", "ملت", "صادرات", "تجارت", "پاسارگاد", "پارسیان", "سامان", "مسکن", "کشاورزی", "رفاه",
            "اقتصاد نوین", "آینده", "شهر", "دی", "صنعت و معدن", "قوامین", "انصار", "بلوبانک", "بلو بانک",
        ]
        for b in banks:
            if b in text:
                return b
        # pattern: بانک X
        import re as _re
        m = _re.search(r"بانک\s+([\S\u0600-\u06FF]+)", text)
        if m:
            return m.group(1)
        return None

    def detect_account_name(text: str) -> Optional[str]:
        import re as _re
        m = _re.search(r'"([\S\s]{1,40}?)"', text)
        if m:
            return m.group(1).strip()
        # digits near 'حساب'
        m = _re.search(r"حساب\s*([\d۰-۹]{2,})", text)
        if m:
            digits = m.group(1).translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789"))
            return digits
        return None

    msg_norm = message
    bank_in_msg = detect_bank(msg_norm)
    acc_name_in_msg = detect_account_name(msg_norm)
    matched = None
    if accounts:
        for acc in accounts:
            if bank_in_msg and bank_in_msg in str(acc.get("bank_name", "")):
                matched = acc
                break
            if acc_name_in_msg and acc_name_in_msg in str(acc.get("account_name", "")):
                matched = acc
                break

    suggest_new_account = None
    if matched:
        account_id = matched["account_id"]
        account_name = matched["account_name"]
    else:
        if accounts:
            account_id = accounts[0]["account_id"]
            account_name = accounts[0]["account_name"]
        else:
            account_id = None
            account_name = None
        if bank_in_msg or acc_name_in_msg:
            suggest_new_account = {
                "bank_name": bank_in_msg,
                "account_name": acc_name_in_msg,
            }

    # Generate response message
    amount_formatted = f"{amount:,.0f} تومان"
    type_text = "درآمد" if transaction_type == "income" else "هزینه"

    response_message = f"✅ {type_text} {amount_formatted} در دسته‌بندی '{category}' ثبت شد.\n\nآیا اطلاعات صحیح است؟"

    result = {
        "success": True,
        "type": "transaction",
        "transaction_type": transaction_type,
        "amount": amount,
        "category": category,
        "description": message[:100],
        "account_id": account_id,
        "account_name": account_name,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "response_message": response_message,
        "confidence": 0.8,
    }
    if suggest_new_account:
        result["suggest_new_account"] = suggest_new_account
        result["response_message"] += "\n\nحساب اشارهشده ناشناخته است. ایجاد حساب جدید؟"
    return result


# Phone Authentication Endpoints
@app.post("/api/auth/send-otp")
async def send_otp(request: PhoneAuthRequest):
    """Send OTP to phone number"""
    try:
        # Store OTP in temporary storage (Redis in production)
        # For demo, we'll just validate the phone number format

        phone = request.phone_number.strip()
        if not phone or len(phone) != 11 or not phone.startswith("09"):
            raise HTTPException(status_code=400, detail="شماره تلفن نامعتبر است")

        # In production, integrate with SMS service:
        # - Generate random 6-digit OTP
        # - Store OTP with expiration (5 minutes)
        # - Send SMS using service like Kavenegar, Ghasedak, etc.

        # For demo:
        demo_otp = "123456"
        logger.info(f"Demo OTP for {phone}: {demo_otp}")

        return {
            "success": True,
            "message": "کد تأیید ارسال شد",
            "demo_otp": demo_otp,  # Remove this in production!
        }

    except Exception as e:
        logger.error(f"Error sending OTP: {e}")
        raise HTTPException(status_code=500, detail="خطا در ارسال کد تأیید")


@app.post("/api/auth/verify-otp")
async def verify_otp(request: OTPVerifyRequest):
    """Verify OTP and create/login user"""
    try:
        phone = request.phone_number.strip()
        otp = request.otp_code.strip()

        # In production, verify OTP from storage
        # For demo, accept 123456 as valid OTP
        if otp != "123456":
            raise HTTPException(status_code=400, detail="کد تأیید اشتباه است")

        # Check if user exists
        user = db.execute_query(
            "SELECT * FROM users WHERE phone_number = ?", (phone,), fetch_one=True
        )

        if user:
            # Existing user - login
            return {
                "success": True,
                "token": str(user["user_id"]),  # Use user_id as token for demo
                "user": {
                    "user_id": user["user_id"],
                    "phone_number": user["phone_number"],
                    "first_name": user["first_name"],
                    "last_name": user["last_name"],
                },
            }
        else:
            # New user - register
            from web_config import get_trial_end_date

            trial_end = get_trial_end_date()

            user_id = db.execute_query(
                """INSERT INTO users (phone_number, telegram_id, trial_end_date)
                   VALUES (?, ?, ?)""",
                (phone, int(phone), trial_end),  # Use phone as telegram_id for demo
            )

            if user_id:
                return {
                    "success": True,
                    "token": str(user_id),
                    "user": {
                        "user_id": user_id,
                        "phone_number": phone,
                        "first_name": None,
                        "last_name": None,
                    },
                    "is_new_user": True,
                }
            else:
                raise HTTPException(status_code=500, detail="خطا در ایجاد حساب کاربری")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying OTP: {e}")
        raise HTTPException(status_code=500, detail="خطا در تأیید کد")


# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "Finance Bot Local API is running"}


# User Management Endpoints
@app.post("/api/users", response_model=dict)
async def create_user(user_data: UserCreate):
    """Create a new user"""
    try:
        # Set trial end date
        from web_config import get_trial_end_date

        trial_end = get_trial_end_date()

        user_id = db.execute_query(
            """INSERT INTO users (telegram_id, username, first_name, last_name, trial_end_date)
               VALUES (?, ?, ?, ?, ?)""",
            (
                user_data.telegram_id,
                user_data.username,
                user_data.first_name,
                user_data.last_name,
                trial_end,
            ),
        )

        if user_id:
            return {
                "success": True,
                "user_id": user_id,
                "token": str(user_data.telegram_id),
            }
        raise HTTPException(status_code=400, detail="Failed to create user")
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        # If user exists, return existing user
        if "UNIQUE constraint failed" in str(e):
            existing_user = db.execute_query(
                "SELECT user_id FROM users WHERE telegram_id = ?",
                (user_data.telegram_id,),
                fetch_one=True,
            )
            if existing_user:
                return {
                    "success": True,
                    "user_id": existing_user["user_id"],
                    "token": str(user_data.telegram_id),
                }
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/users/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information"""
    return current_user


@app.get("/api/users/subscription-status")
async def get_subscription_status(current_user: dict = Depends(get_current_user)):
    """Get user subscription status"""
    try:
        now = datetime.now()
        trial_end = (
            datetime.fromisoformat(current_user["trial_end_date"])
            if current_user["trial_end_date"]
            else None
        )
        subscription_end = (
            datetime.fromisoformat(current_user["subscription_end_date"])
            if current_user["subscription_end_date"]
            else None
        )

        is_trial = trial_end and trial_end > now
        is_subscribed = subscription_end and subscription_end > now

        return {
            "is_active": is_trial or is_subscribed,
            "is_trial": is_trial,
            "is_subscribed": is_subscribed,
            "trial_end_date": current_user["trial_end_date"],
            "subscription_end_date": current_user["subscription_end_date"],
            "days_remaining": (
                (trial_end - now).days
                if is_trial
                else (subscription_end - now).days if is_subscribed else 0
            ),
        }
    except Exception as e:
        logger.error(f"Error getting subscription status: {e}")
        return {
            "is_active": True,  # For demo, always active
            "is_trial": True,
            "is_subscribed": False,
            "days_remaining": 7,
        }


# Account Management Endpoints
@app.get("/api/accounts")
async def get_accounts(current_user: dict = Depends(get_current_user)):
    """Get user accounts"""
    try:
        accounts = db.execute_query(
            "SELECT * FROM bank_accounts WHERE user_id = ? AND is_active = 1",
            (current_user["user_id"],),
            fetch_all=True,
        )
        return accounts or []
    except Exception as e:
        logger.error(f"Error getting accounts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/accounts")
async def create_account(
    account_data: AccountCreate, current_user: dict = Depends(get_current_user)
):
    """Create a new bank account"""
    try:
        account_id = db.execute_query(
            """INSERT INTO bank_accounts (user_id, bank_name, account_name, initial_balance, current_balance)
               VALUES (?, ?, ?, ?, ?)""",
            (
                current_user["user_id"],
                account_data.bank_name,
                account_data.account_name,
                account_data.initial_balance,
                account_data.initial_balance,
            ),
        )

        if account_id:
            return {"success": True, "account_id": account_id}
        raise HTTPException(status_code=400, detail="Failed to create account")
    except Exception as e:
        logger.error(f"Error creating account: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/accounts/{account_id}")
async def update_account(
    account_id: int,
    account_data: AccountUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update bank account fields"""
    try:
        # Ensure account belongs to user
        acc = db.execute_query(
            "SELECT * FROM bank_accounts WHERE account_id = ? AND user_id = ? AND is_active = 1",
            (account_id, current_user["user_id"]),
            fetch_one=True,
        )
        if not acc:
            raise HTTPException(status_code=404, detail="Account not found")

        # Build dynamic update
        fields = []
        params = []
        if account_data.bank_name is not None:
            fields.append("bank_name = ?")
            params.append(account_data.bank_name)
        if account_data.account_name is not None:
            fields.append("account_name = ?")
            params.append(account_data.account_name)
        if account_data.initial_balance is not None:
            fields.append("initial_balance = ?")
            params.append(account_data.initial_balance)
        if account_data.current_balance is not None:
            fields.append("current_balance = ?")
            params.append(account_data.current_balance)

        if not fields:
            return {"success": True, "account_id": account_id}

        params.extend([account_id, current_user["user_id"]])
        query = f"UPDATE bank_accounts SET {', '.join(fields)} WHERE account_id = ? AND user_id = ?"
        db.execute_query(query, params)
        return {"success": True, "account_id": account_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating account: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/accounts/{account_id}")
async def delete_account(account_id: int, current_user: dict = Depends(get_current_user)):
    """Soft delete an account"""
    try:
        # Ensure account belongs to user
        acc = db.execute_query(
            "SELECT * FROM bank_accounts WHERE account_id = ? AND user_id = ? AND is_active = 1",
            (account_id, current_user["user_id"]),
            fetch_one=True,
        )
        if not acc:
            raise HTTPException(status_code=404, detail="Account not found")

        db.execute_query(
            "UPDATE bank_accounts SET is_active = 0 WHERE account_id = ? AND user_id = ?",
            (account_id, current_user["user_id"]),
        )
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting account: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Transaction Management Endpoints
@app.get("/api/transactions")
async def get_transactions(
    current_user: dict = Depends(get_current_user),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    transaction_type: Optional[str] = None,
    category: Optional[str] = None,
    account_id: Optional[int] = None,
    limit: int = 100,
):
    """Get user transactions with optional filters"""
    try:
        query = """
            SELECT t.*, a.bank_name, a.account_name 
            FROM transactions t
            JOIN bank_accounts a ON t.account_id = a.account_id
            WHERE t.user_id = ?
        """
        params = [current_user["user_id"]]

        if start_date:
            query += " AND t.transaction_date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND t.transaction_date <= ?"
            params.append(end_date + " 23:59:59")
        if transaction_type:
            query += " AND t.type = ?"
            params.append(transaction_type)
        if category:
            query += " AND t.category = ?"
            params.append(category)
        if account_id:
            query += " AND t.account_id = ?"
            params.append(account_id)

        query += " ORDER BY t.transaction_date DESC LIMIT ?"
        params.append(limit)

        transactions = db.execute_query(query, params, fetch_all=True)
        return transactions or []
    except Exception as e:
        logger.error(f"Error getting transactions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/transactions")
async def create_transaction(
    transaction_data: TransactionCreate, current_user: dict = Depends(get_current_user)
):
    """Create a new transaction"""
    try:
        # Validate account ownership and prevent negative balances
        acc = db.execute_query(
            "SELECT * FROM bank_accounts WHERE account_id = ? AND user_id = ? AND is_active = 1",
            (transaction_data.account_id, current_user["user_id"]),
            fetch_one=True,
        )
        if not acc:
            raise HTTPException(status_code=404, detail="حساب بانکی یافت نشد")

        if transaction_data.transaction_type == "expense":
            projected = (acc["current_balance"] or 0) - float(transaction_data.amount)
            if projected < 0:
                raise HTTPException(
                    status_code=400,
                    detail="موجودی حساب کافی نیست. امکان برداشت بیشتر از موجودی وجود ندارد. لطفاً تراکنش را ویرایش کنید.",
                )

        # Set transaction datetime with precision: if date provided without time, attach current time
        if transaction_data.transaction_date:
            td = transaction_data.transaction_date
            now = datetime.now()
            if 'T' in td or ' ' in td:
                trans_date = td
            else:
                trans_date = f"{td} {now.strftime('%H:%M:%S')}"
        else:
            trans_date = datetime.now().isoformat()

        transaction_id = db.execute_query(
            """INSERT INTO transactions (user_id, account_id, type, amount, category, description, transaction_date)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                current_user["user_id"],
                transaction_data.account_id,
                transaction_data.transaction_type,
                transaction_data.amount,
                transaction_data.category,
                transaction_data.description,
                trans_date,
            ),
        )

        if transaction_id:
            # Update account balance
            if transaction_data.transaction_type == "income":
                balance_change = transaction_data.amount
            else:
                balance_change = -transaction_data.amount

            db.execute_query(
                "UPDATE bank_accounts SET current_balance = current_balance + ? WHERE account_id = ?",
                (balance_change, transaction_data.account_id),
            )

            return {"success": True, "transaction_id": transaction_id}
        raise HTTPException(status_code=400, detail="Failed to create transaction")
    except Exception as e:
        logger.error(f"Error creating transaction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/transactions/{transaction_id}")
async def update_transaction(
    transaction_id: int,
    transaction_data: TransactionCreate,
    current_user: dict = Depends(get_current_user),
):
    """Update an existing transaction (amount/category/description/date/type/account)
    Ensures account balances never become negative.
    """
    try:
        # Load current transaction
        tx = db.execute_query(
            "SELECT * FROM transactions WHERE transaction_id = ? AND user_id = ?",
            (transaction_id, current_user["user_id"]),
            fetch_one=True,
        )
        if not tx:
            raise HTTPException(status_code=404, detail="تراکنش یافت نشد")

        old_account_id = tx["account_id"]
        old_type = tx["type"]
        old_amount = float(tx["amount"]) if tx["amount"] is not None else 0.0
        old_effect = old_amount if old_type == "income" else -old_amount

        new_account_id = transaction_data.account_id if transaction_data.account_id is not None else old_account_id
        new_type = transaction_data.transaction_type if transaction_data.transaction_type is not None else old_type
        new_amount = float(transaction_data.amount) if transaction_data.amount is not None else old_amount
        new_effect = new_amount if new_type == "income" else -new_amount

        # Load balances
        old_acc = db.execute_query(
            "SELECT * FROM bank_accounts WHERE account_id = ? AND user_id = ?",
            (old_account_id, current_user["user_id"]), fetch_one=True,
        )
        if not old_acc:
            raise HTTPException(status_code=404, detail="حساب قبلی یافت نشد")

        if new_account_id != old_account_id:
            new_acc = db.execute_query(
                "SELECT * FROM bank_accounts WHERE account_id = ? AND user_id = ? AND is_active = 1",
                (new_account_id, current_user["user_id"]), fetch_one=True,
            )
            if not new_acc:
                raise HTTPException(status_code=404, detail="حساب جدید یافت نشد")
            projected_old = (old_acc["current_balance"] or 0) - old_effect
            projected_new = (new_acc["current_balance"] or 0) + new_effect
            if projected_new < 0:
                raise HTTPException(status_code=400, detail="این تغییر باعث منفی شدن موجودی حساب مقصد می‌شود. لطفاً تراکنش را ویرایش کنید.")
        else:
            projected = (old_acc["current_balance"] or 0) - old_effect + new_effect
            if projected < 0:
                raise HTTPException(status_code=400, detail="این تغییر باعث منفی شدن موجودی حساب می‌شود. لطفاً تراکنش را ویرایش کنید.")

        # Build update fields
        fields = []
        params = []
        if transaction_data.account_id is not None:
            fields.append("account_id = ?")
            params.append(new_account_id)
        if transaction_data.transaction_type is not None:
            fields.append("type = ?")
            params.append(new_type)
        if transaction_data.amount is not None:
            fields.append("amount = ?")
            params.append(new_amount)
        if transaction_data.category is not None:
            fields.append("category = ?")
            params.append(transaction_data.category)
        if transaction_data.description is not None:
            fields.append("description = ?")
            params.append(transaction_data.description)
        if transaction_data.transaction_date is not None:
            td = transaction_data.transaction_date
            if 'T' in td or ' ' in td:
                trans_date = td
            else:
                from datetime import datetime as dt
                trans_date = f"{td} {dt.now().strftime('%H:%M:%S')}"
            fields.append("transaction_date = ?")
            params.append(trans_date)

        # Apply changes and balances
        # Use a single transaction
        if True:
            if fields:
                params.extend([transaction_id, current_user["user_id"]])
                query = f"UPDATE transactions SET {', '.join(fields)} WHERE transaction_id = ? AND user_id = ?"
                db.execute_query(query, params)

            # Adjust balances
            if new_account_id != old_account_id:
                db.execute_query(
                    "UPDATE bank_accounts SET current_balance = current_balance - ? WHERE account_id = ?",
                    (old_effect, old_account_id),
                )
                db.execute_query(
                    "UPDATE bank_accounts SET current_balance = current_balance + ? WHERE account_id = ?",
                    (new_effect, new_account_id),
                )
            else:
                net = -old_effect + new_effect
                db.execute_query(
                    "UPDATE bank_accounts SET current_balance = current_balance + ? WHERE account_id = ?",
                    (net, old_account_id),
                )

        return {"success": True, "transaction_id": transaction_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating transaction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/transactions/summary")
async def get_transactions_summary(
    current_user: dict = Depends(get_current_user),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    """Get transaction summary"""
    try:
        query = """
            SELECT 
                type,
                COUNT(*) as count,
                SUM(amount) as total
            FROM transactions
            WHERE user_id = ?
        """
        params = [current_user["user_id"]]

        if start_date:
            query += " AND transaction_date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND transaction_date <= ?"
            params.append(end_date + " 23:59:59")

        query += " GROUP BY type"

        results = db.execute_query(query, params, fetch_all=True)

        summary = {
            "income": {"count": 0, "total": 0},
            "expense": {"count": 0, "total": 0},
            "balance": 0,
        }

        for row in results:
            summary[row["type"]] = {"count": row["count"], "total": float(row["total"])}

        summary["balance"] = summary["income"]["total"] - summary["expense"]["total"]
        return summary
    except Exception as e:
        logger.error(f"Error getting summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/transactions/categories")
async def get_category_summary(
    current_user: dict = Depends(get_current_user),
    transaction_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    """Get transaction summary by category"""
    try:
        query = """
            SELECT 
                category,
                COUNT(*) as count,
                SUM(amount) as total
            FROM transactions
            WHERE user_id = ?
        """
        params = [current_user["user_id"]]

        if transaction_type:
            query += " AND type = ?"
            params.append(transaction_type)
        if start_date:
            query += " AND transaction_date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND transaction_date <= ?"
            params.append(end_date + " 23:59:59")

        query += " GROUP BY category ORDER BY total DESC"

        results = db.execute_query(query, params, fetch_all=True)

        summary = {}
        for row in results:
            summary[row["category"]] = {
                "count": row["count"],
                "total": float(row["total"]),
            }

        return summary
    except Exception as e:
        logger.error(f"Error getting category summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# AI Processing Endpoints
@app.post("/api/ai/process-message")
async def process_message(
    request: ProcessMessageRequest, current_user: dict = Depends(get_current_user)
):
    """Process natural language message with enhanced AI"""
    try:
        # Get user accounts for context
        accounts = db.execute_query(
            "SELECT * FROM bank_accounts WHERE user_id = ? AND is_active = 1",
            (current_user["user_id"],),
            fetch_all=True,
        )

        # Use enhanced AI processing with fallback
        result = process_message_with_fallback(request.message, accounts or [])
        return result
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Check Management Endpoints
@app.get("/api/checks")
async def get_checks(
    current_user: dict = Depends(get_current_user),
    status: Optional[str] = None,
    type: Optional[str] = None,
):
    """Get user checks"""
    try:
        query = """
            SELECT c.*, a.bank_name, a.account_name 
            FROM checks c
            JOIN bank_accounts a ON c.account_id = a.account_id
            WHERE c.user_id = ?
        """
        params = [current_user["user_id"]]

        if status:
            query += " AND c.status = ?"
            params.append(status)
        if type:
            query += " AND c.type = ?"
            params.append(type)

        query += " ORDER BY c.due_date DESC"

        checks = db.execute_query(query, params, fetch_all=True)
        return checks or []
    except Exception as e:
        logger.error(f"Error getting checks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/checks")
async def create_check(
    check_data: CheckCreate, current_user: dict = Depends(get_current_user)
):
    """Create a new check"""
    try:
        check_id = db.execute_query(
            """INSERT INTO checks (user_id, account_id, type, amount, due_date, recipient_issuer, description)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                current_user["user_id"],
                check_data.account_id,
                check_data.type,
                check_data.amount,
                check_data.due_date,
                check_data.recipient_issuer,
                check_data.description,
            ),
        )

        if check_id:
            return {"success": True, "check_id": check_id}
        raise HTTPException(status_code=400, detail="Failed to create check")
    except Exception as e:
        logger.error(f"Error creating check: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Savings Plans Endpoints
@app.get("/api/savings-plans")
async def get_savings_plans(current_user: dict = Depends(get_current_user)):
    """Get user savings plans"""
    try:
        plans = db.execute_query(
            "SELECT * FROM savings_plans WHERE user_id = ? ORDER BY created_at DESC",
            (current_user["user_id"],),
            fetch_all=True,
        )
        return plans or []
    except Exception as e:
        logger.error(f"Error getting savings plans: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/savings-plans")
async def create_savings_plan(
    plan_data: SavingsPlanCreate, current_user: dict = Depends(get_current_user)
):
    """Create a new savings plan"""
    try:
        # Set start_date to today if not provided
        from datetime import date

        start_date = date.today().isoformat()

        plan_id = db.execute_query(
            """INSERT INTO savings_plans (user_id, plan_name, plan_type, target_amount, monthly_contribution, start_date, end_date)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                current_user["user_id"],
                plan_data.plan_name,
                plan_data.plan_type,
                plan_data.target_amount,
                plan_data.monthly_contribution,
                start_date,
                plan_data.end_date,
            ),
        )

        if plan_id:
            return {"success": True, "plan_id": plan_id}
        raise HTTPException(status_code=400, detail="Failed to create savings plan")
    except Exception as e:
        logger.error(f"Error creating savings plan: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Categories endpoint
@app.get("/api/categories")
async def get_categories():
    """Get all available enhanced categories"""
    categories = {
        "expense": [
            # Food & Dining
            {"name": "رستوران و کافی‌شاپ", "icon": "🍔", "group": "غذا و نوشیدنی"},
            {"name": "خواربار", "icon": "🛒", "group": "غذا و نوشیدنی"},
            {"name": "حمل و نقل", "icon": "🚗", "group": "حمل و نقل"},
            {"name": "پوشاک", "icon": "👕", "group": "خرید"},
            {"name": "درمان و سلامت", "icon": "🏥", "group": "سلامت"},
            {"name": "سرگرمی", "icon": "🎮", "group": "تفریح"},
            {"name": "سایر", "icon": "💰", "group": "عمومی"},
        ],
        "income": [
            {"name": "حقوق", "icon": "💼", "group": "کار"},
            {"name": "کسب و کار", "icon": "🏪", "group": "کار"},
            {"name": "سرمایه‌گذاری", "icon": "💹", "group": "سرمایه"},
            {"name": "سایر", "icon": "💸", "group": "عمومی"},
        ],
    }
    return categories


# AI Financial Advisor Endpoints (Gemini 2.5 Pro)
class FinancialAdvisorRequest(BaseModel):
    question: str
    analysis_type: Optional[str] = (
        "general"  # general, spending, investment, optimization
    )


# Usage limit tracking table (for hourly limits)
def init_advisor_usage_table():
    """Create advisor usage tracking table"""
    try:
        db.execute_query(
            """
            CREATE TABLE IF NOT EXISTS ai_advisor_usage (
                usage_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                usage_timestamp DATETIME NOT NULL,
                question TEXT,
                response_summary TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        """
        )
        logger.info("AI advisor usage table initialized")
    except Exception as e:
        logger.error(f"Error creating advisor usage table: {e}")


# Initialize the advisor table
init_advisor_usage_table()


def check_advisor_usage_limit(user_id: int) -> Dict:
    """Check if user can use AI advisor (1 per hour limit)"""
    try:
        from datetime import datetime, timedelta

        # Check usage in the last hour
        one_hour_ago = (datetime.now() - timedelta(hours=1)).isoformat()

        recent_usage = db.execute_query(
            "SELECT COUNT(*) as count FROM ai_advisor_usage WHERE user_id = ? AND usage_timestamp > ?",
            (user_id, one_hour_ago),
            fetch_one=True,
        )

        usage_count = recent_usage["count"] if recent_usage else 0
        can_use = usage_count < 1

        # Get next available time
        if not can_use:
            last_usage = db.execute_query(
                "SELECT usage_timestamp FROM ai_advisor_usage WHERE user_id = ? ORDER BY usage_timestamp DESC LIMIT 1",
                (user_id,),
                fetch_one=True,
            )
            if last_usage:
                last_time = datetime.fromisoformat(last_usage["usage_timestamp"])
                next_available = last_time + timedelta(hours=1)
                minutes_remaining = max(
                    0, int((next_available - datetime.now()).total_seconds() / 60)
                )
            else:
                minutes_remaining = 0
        else:
            minutes_remaining = 0

        return {
            "can_use": can_use,
            "usage_count": usage_count,
            "limit": 1,
            "minutes_remaining": minutes_remaining,
        }

    except Exception as e:
        logger.error(f"Error checking advisor usage limit: {e}")
        return {"can_use": True, "usage_count": 0, "limit": 1, "minutes_remaining": 0}


def record_advisor_usage(user_id: int, question: str, response_summary: str):
    """Record AI advisor usage"""
    try:
        from datetime import datetime

        db.execute_query(
            "INSERT INTO ai_advisor_usage (user_id, usage_timestamp, question, response_summary) VALUES (?, ?, ?, ?)",
            (
                user_id,
                datetime.now().isoformat(),
                question[:500],
                response_summary[:200],
            ),
        )

    except Exception as e:
        logger.error(f"Error recording advisor usage: {e}")


def get_user_financial_analysis(user_id: int) -> Dict:
    """Get comprehensive financial analysis for user"""
    try:
        # Get user's transactions for last 6 months
        from datetime import datetime, timedelta

        six_months_ago = (datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d")

        # Get transaction summary
        summary = db.execute_query(
            """
            SELECT 
                type,
                COUNT(*) as count,
                SUM(amount) as total,
                AVG(amount) as average
            FROM transactions 
            WHERE user_id = ? AND transaction_date >= ?
            GROUP BY type
        """,
            (user_id, six_months_ago),
            fetch_all=True,
        )

        # Get category breakdown
        categories = db.execute_query(
            """
            SELECT 
                category,
                type,
                COUNT(*) as count,
                SUM(amount) as total,
                AVG(amount) as average
            FROM transactions 
            WHERE user_id = ? AND transaction_date >= ?
            GROUP BY category, type
            ORDER BY total DESC
        """,
            (user_id, six_months_ago),
            fetch_all=True,
        )

        # Get monthly trends
        monthly_trends = db.execute_query(
            """
            SELECT 
                strftime('%Y-%m', transaction_date) as month,
                type,
                SUM(amount) as total
            FROM transactions 
            WHERE user_id = ? AND transaction_date >= ?
            GROUP BY month, type
            ORDER BY month DESC
        """,
            (user_id, six_months_ago),
            fetch_all=True,
        )

        from .config_local import GEMINI_API_KEY, GEMINI_MODEL
        accounts = db.execute_query(
            "SELECT bank_name, account_name, current_balance FROM bank_accounts WHERE user_id = ? AND is_active = 1",
            (user_id,),
            fetch_all=True,
        )

        return {
            "summary": summary,
            "categories": categories,
            "monthly_trends": monthly_trends,
            "accounts": accounts,
        }

    except Exception as e:
        logger.error(f"Error getting financial analysis: {e}")
        return {"summary": [], "categories": [], "monthly_trends": [], "accounts": []}


def process_financial_question_with_gemini(
    question: str, user_data: Dict, user_id: int
) -> Dict:
    """Process financial advisory question using Gemini 2.5 Pro with strict guidelines"""
    try:
        import google.generativeai as genai
        from config_local import GEMINI_API_KEY, GEMINI_MODEL

        # Configure Gemini API
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel(GEMINI_MODEL)

        # Prepare user financial data
        financial_summary = ""
        if user_data.get("summary"):
            for item in user_data["summary"]:
                financial_summary += f"- {item['type']}: {item['total']:,.0f} تومان ({item['count']} تراکنش)\n"

        category_summary = ""
        if user_data.get("categories"):
            for item in user_data["categories"][:10]:  # Top 10 categories
                category_summary += f"- {item['category']} ({item['type']}): {item['total']:,.0f} تومان\n"

        accounts_summary = ""
        if user_data.get("accounts"):
            total_balance = sum(acc["current_balance"] for acc in user_data["accounts"])
            accounts_summary = f"موجودی کل: {total_balance:,.0f} تومان\n"
            for acc in user_data["accounts"]:
                accounts_summary += (
                    f"- {acc['bank_name']}: {acc['current_balance']:,.0f} تومان\n"
                )

        # Create strict prompt with guidelines
        prompt = f"""
شما یک مشاور مالی حرفه‌ای هستید که باید به سوالات مالی کاربران پاسخ دهید.

🔒 قوانین سخت‌گیرانه:
1. فقط به سوالات مالی، سرمایه‌گذاری، بودجه‌بندی، و برنامه‌ریزی مالی پاسخ دهید
2. هیچ‌گاه درباره موضوعات غیرمالی، احوال‌پرسی، یا موضوعات شخصی صحبت نکنید
3. اطلاعات سایر کاربران محرمانه است و نباید درباره آن‌ها صحبت کنید
4. درباره نحوه عملکرد سیستم یا فناوری صحبت نکنید
5. اگر سوال غیرمالی است، مودبانه کاربر را به موضوعات مالی هدایت کنید

اطلاعات مالی کاربر (6 ماه اخیر):
{financial_summary}

دسته‌بندی‌های اصلی:
{category_summary}

حساب‌های بانکی:
{accounts_summary}

سوال کاربر: "{question}"

پاسخ شما باید شامل:
1. تحلیل وضعیت مالی فعلی
2. پیشنهادات عملی و کاربردی
3. برنامه‌ریزی برای بهبود
4. هشدارهای مالی در صورت نیاز

پاسخ را به صورت JSON با ساختار زیر ارائه دهید:
{{
    "is_valid_financial_question": true/false,
    "response_message": "پاسخ کامل به فارسی",
    "analysis": {{
        "financial_health_score": عدد بین 0 تا 100,
        "strengths": ["نقاط قوت مالی"],
        "weaknesses": ["نقاط ضعف مالی"],
        "recommendations": ["پیشنهادات عملی"],
        "investment_suggestions": ["پیشنهادات سرمایه‌گذاری"],
        "cost_optimization": ["راه‌های کاهش هزینه"],
        "risk_warnings": ["هشدارهای مخاطرات مالی"]
    }},
    "spending_analysis": {{
        "top_categories": {{"category": {{"amount": مبلغ, "percentage": درصد, "trend": "increasing/stable/decreasing"}}}}
    }}
}}

اگر سوال غیرمالی است، is_valid_financial_question را false کنید و کاربر را مودبانه راهنمایی کنید.
"""

        # Send to Gemini
        response = model.generate_content(prompt)
        response_text = response.text.strip()

        # Parse JSON response
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]

        import json

        result = json.loads(response_text.strip())

        # Validate that it's a valid financial question
        if not result.get("is_valid_financial_question", False):
            return {
                "success": False,
                "error": "سوال نامعتبر",
                "message": result.get(
                    "response_message",
                    "لطفاً سوالات مرتبط با امور مالی، سرمایه‌گذاری و بودجه‌بندی بپرسید.",
                ),
            }

        # Record usage
        record_advisor_usage(
            user_id, question, result.get("response_message", "")[:200]
        )

        result["success"] = True
        result["usage_recorded"] = True

        return result

    except Exception as e:
        logger.error(f"Error in Gemini financial processing: {e}")
        return {
            "success": False,
            "error": "خطا در پردازش سوال",
            "message": "متأسفانه در حال حاضر امکان پردازش سوال شما وجود ندارد. لطفاً بعداً تلاش کنید.",
        }


@app.get("/api/ai/advisor/usage-limit")
async def get_advisor_usage_limit(current_user: dict = Depends(get_current_user)):
    """Check AI advisor usage limit for current user"""
    try:
        usage_info = check_advisor_usage_limit(current_user["user_id"])
        return usage_info
    except Exception as e:
        logger.error(f"Error checking advisor usage: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ai/advisor/analyze")
async def analyze_financial_status(
    request: FinancialAdvisorRequest, current_user: dict = Depends(get_current_user)
):
    """Analyze user's financial status using Gemini 2.5 Pro"""
    try:
        # Check usage limit
        usage_info = check_advisor_usage_limit(current_user["user_id"])
        if not usage_info["can_use"]:
            raise HTTPException(
                status_code=429,
                detail=f"محدودیت استفاده: لطفاً {usage_info['minutes_remaining']} دقیقه صبر کنید",
            )

        # Get user financial data
        user_data = get_user_financial_analysis(current_user["user_id"])

        # Process with Gemini
        result = process_financial_question_with_gemini(
            request.question, user_data, current_user["user_id"]
        )

        if not result.get("success"):
            return {
                "success": False,
                "error": result.get("error", "خطا در پردازش"),
                "message": result.get("message", "خطا در پردازش سوال"),
            }

        # Add usage info to response
        result["usage_info"] = {
            "usage_remaining": 0,  # Used up this hour
        from .config_local import GEMINI_API_KEY, GEMINI_MODEL
        }

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in financial analysis: {e}")
        raise HTTPException(status_code=500, detail="خطا در تحلیل مالی")


# Enhanced Chat Interface Endpoints
class ChatMessageRequest(BaseModel):
    message: str
    action_type: Optional[str] = (
        "general"  # general, account_management, financial_report
    )


def process_chat_command_with_gemini(
    message: str, accounts: List[Dict], user_id: int
) -> Dict:
    """Process chat commands for account management and reporting"""
    try:
        import google.generativeai as genai
        from config_local import GEMINI_API_KEY, GEMINI_MODEL

        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel(GEMINI_MODEL)

        # Prepare accounts info
        accounts_info = ""
        if accounts:
            accounts_info = "حساب‌های کاربر:\n"
            for acc in accounts:
                accounts_info += f"- {acc['bank_name']} ({acc['account_name']}) - ID: {acc['account_id']} - موجودی: {acc['current_balance']:,.0f} تومان\n"

        # Create enhanced prompt for account management and reporting
        prompt = f"""
شما دستیار مالی هوشمندی هستید که می‌توانید حساب‌های کاربر را مدیریت کنید و گزارش‌های مالی ارائه دهید.

🔒 قوانین سخت:
1. فقط درباره موضوعات مالی، مدیریت حساب، و گزارش‌گیری صحبت کنید
2. احوال‌پرسی، موضوعات شخصی، و سوالات غیرمالی مجاز نیست
3. اطلاعات سایر کاربران محرمانه است
4. درباره عملکرد سیستم صحبت نکنید

{accounts_info}

پیام کاربر: "{message}"

اگر کاربر می‌خواهد:
- حساب جدید اضافه کند
- حساب موجود را ویرایش کند
- حساب را حذف کند
- گزارش مالی دریافت کند
- موجودی حساب‌ها را ببیند

پاسخ را به صورت JSON ارائه دهید:
{{
    "type": "account_create/account_edit/account_delete/financial_report/balance_inquiry/general_response/invalid_request",
    "is_valid_request": true/false,
    "action_data": {{
        "account_id": شناسه حساب (در صورت ویرایش یا حذف),
        "bank_name": نام بانک جدید,
        "account_name": نام حساب جدید,
        "initial_balance": موجودی اولیه
    }},
    "response_message": "پاسخ کامل به فارسی",
    "requires_confirmation": true/false
}}

فقط JSON برگردانید.
"""

        response = model.generate_content(prompt)
        response_text = response.text.strip()

        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]

        import json

        result = json.loads(response_text.strip())

        result["success"] = True
        return result

    except Exception as e:
        logger.error(f"Error in chat command processing: {e}")
        return {
            "success": False,
            "type": "error",
            "response_message": "متأسفانه نتوانستم درخواست شما را پردازش کنم. لطفاً دوباره تلاش کنید.",
        }


@app.post("/api/ai/chat/process")
async def process_enhanced_chat(
    request: ChatMessageRequest, current_user: dict = Depends(get_current_user)
):
    """Process enhanced chat messages for account management and reporting"""
    try:
        # Get user accounts
        accounts = db.execute_query(
            "SELECT * FROM bank_accounts WHERE user_id = ? AND is_active = 1",
            (current_user["user_id"],),
            fetch_all=True,
        )

        # Process with enhanced AI
        result = process_chat_command_with_gemini(
            request.message, accounts or [], current_user["user_id"]
        )

        # Handle specific actions
        if result.get("type") == "account_create":
            action_data = result.get("action_data", {})
            if action_data.get("bank_name") and action_data.get("account_name"):
                # Create account automatically
                account_id = db.execute_query(
                    "INSERT INTO bank_accounts (user_id, bank_name, account_name, initial_balance, current_balance) VALUES (?, ?, ?, ?, ?)",
                    (
                        current_user["user_id"],
                        action_data["bank_name"],
                        action_data["account_name"],
                        action_data.get("initial_balance", 0),
                        action_data.get("initial_balance", 0),
                    ),
                )
                result["account_created"] = True
                result["account_id"] = account_id
                result["response_message"] += f"\n\n✅ حساب جدید با موفقیت ایجاد شد!"

        elif result.get("type") == "balance_inquiry":
            total_balance = sum(acc["current_balance"] for acc in accounts)
            balance_details = f"\n\n💰 موجودی کل: {total_balance:,.0f} تومان\n\n"
            for acc in accounts:
                balance_details += (
                    f"• {acc['bank_name']}: {acc['current_balance']:,.0f} تومان\n"
                )
            result["response_message"] += balance_details

        elif result.get("type") == "financial_report":
            # Get quick financial summary
            summary = db.execute_query(
                "SELECT type, SUM(amount) as total FROM transactions WHERE user_id = ? AND transaction_date >= date('now', '-30 days') GROUP BY type",
                (current_user["user_id"],),
                fetch_all=True,
            )

            report = "\n\n📊 گزارش مالی 30 روز اخیر:\n"
            income_total = 0
            expense_total = 0

            for item in summary:
                if item["type"] == "income":
                    income_total = item["total"]
                    report += f"• درآمد: {income_total:,.0f} تومان\n"
                elif item["type"] == "expense":
                    expense_total = item["total"]
                    report += f"• هزینه: {expense_total:,.0f} تومان\n"

            balance = income_total - expense_total
            report += f"• خالص: {balance:,.0f} تومان\n"

            result["response_message"] += report

        return result

    except Exception as e:
        logger.error(f"Error in enhanced chat processing: {e}")
        raise HTTPException(status_code=500, detail="خطا در پردازش پیام")


if __name__ == "__main__":
    import uvicorn

    init_local_database()
    uvicorn.run("web_api_local:app", host="0.0.0.0", port=8001, reload=True)
