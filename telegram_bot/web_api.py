# web_api.py
"""
FastAPI web server to expose finance bot functionality as REST APIs
This allows the React frontend to interact with all bot features
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

# Import existing bot modules
from .database.connection import init_database
from .modules.user_management import UserManager
from .modules.account_management import AccountManager
from .modules.transaction_handler import TransactionHandler
from .modules.ai_processor import AIProcessor
from .modules.check_management import CheckManager
from .modules.reports import ReportGenerator
from .modules.savings_plans import SavingsManager
from .modules.subscription import SubscriptionManager
from .modules.voice_handler import VoiceHandler

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Finance Bot Web API",
    description="REST API for Finance Bot functionality",
    version="1.0.0",
)

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://localhost:5179",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5179",
    ],
    # Allow any localhost/127.0.0.1 port to prevent CORS issues in dev
    allow_origin_regex=r"^http://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Security
security = HTTPBearer()

# Initialize bot managers
user_manager = UserManager()
account_manager = AccountManager()
transaction_handler = TransactionHandler()
ai_processor = AIProcessor()
check_manager = CheckManager()
report_generator = ReportGenerator()
savings_manager = SavingsManager()
subscription_manager = SubscriptionManager()
voice_handler = VoiceHandler()


# Pydantic models for API
class UserCreate(BaseModel):
    telegram_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class AccountCreate(BaseModel):
    bank_name: str
    account_name: str
    initial_balance: float = 0


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
        user_id = int(token)
        return user_id
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        )


# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "Finance Bot API is running"}


# User Management Endpoints
@app.post("/api/users", response_model=dict)
async def create_user(user_data: UserCreate):
    """Create a new user"""
    try:
        user_id = user_manager.create_user(
            telegram_id=user_data.telegram_id,
            username=user_data.username,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
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
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/users/me")
async def get_current_user_info(current_user: int = Depends(get_current_user)):
    """Get current user information"""
    try:
        user = user_manager.get_user_by_telegram_id(current_user)
        if user:
            return user.__dict__
        raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        logger.error(f"Error getting user: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/users/subscription-status")
async def get_subscription_status(current_user: int = Depends(get_current_user)):
    """Get user subscription status"""
    try:
        user = user_manager.get_user_by_telegram_id(current_user)
        if user:
            status = user_manager.check_subscription_status(user.user_id)
            return status
        raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        logger.error(f"Error getting subscription status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Account Management Endpoints
@app.get("/api/accounts")
async def get_accounts(current_user: int = Depends(get_current_user)):
    """Get user accounts"""
    try:
        user = user_manager.get_user_by_telegram_id(current_user)
        if user:
            accounts = account_manager.get_user_accounts(user.user_id)
            return [
                acc.__dict__ if hasattr(acc, "__dict__") else acc for acc in accounts
            ]
        raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        logger.error(f"Error getting accounts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/accounts")
async def create_account(
    account_data: AccountCreate, current_user: int = Depends(get_current_user)
):
    """Create a new bank account"""
    try:
        user = user_manager.get_user_by_telegram_id(current_user)
        if user:
            account_id = account_manager.create_account(
                user_id=user.user_id,
                bank_name=account_data.bank_name,
                account_name=account_data.account_name,
                initial_balance=Decimal(str(account_data.initial_balance)),
            )
            if account_id:
                return {"success": True, "account_id": account_id}
            raise HTTPException(status_code=400, detail="Failed to create account")
        raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        logger.error(f"Error creating account: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Transaction Management Endpoints
@app.get("/api/transactions")
async def get_transactions(
    current_user: int = Depends(get_current_user),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    transaction_type: Optional[str] = None,
    category: Optional[str] = None,
    account_id: Optional[int] = None,
):
    """Get user transactions with optional filters"""
    try:
        user = user_manager.get_user_by_telegram_id(current_user)
        if user:
            transactions = transaction_handler.get_user_transactions(
                user_id=user.user_id,
                start_date=(
                    datetime.strptime(start_date, "%Y-%m-%d").date()
                    if start_date
                    else None
                ),
                end_date=(
                    datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else None
                ),
                transaction_type=transaction_type,
                category=category,
                account_id=account_id,
            )
            return [t.__dict__ if hasattr(t, "__dict__") else t for t in transactions]
        raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        logger.error(f"Error getting transactions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/transactions")
async def create_transaction(
    transaction_data: TransactionCreate, current_user: int = Depends(get_current_user)
):
    """Create a new transaction"""
    try:
        user = user_manager.get_user_by_telegram_id(current_user)
        if user:
            transaction_id = transaction_handler.create_transaction(
                user_id=user.user_id,
                account_id=transaction_data.account_id,
                transaction_type=transaction_data.transaction_type,
                amount=Decimal(str(transaction_data.amount)),
                category=transaction_data.category,
                description=transaction_data.description,
                transaction_date=transaction_data.transaction_date,
            )
            if transaction_id:
                return {"success": True, "transaction_id": transaction_id}
            raise HTTPException(status_code=400, detail="Failed to create transaction")
        raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        logger.error(f"Error creating transaction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/transactions/summary")
async def get_transactions_summary(
    current_user: int = Depends(get_current_user),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    """Get transaction summary"""
    try:
        user = user_manager.get_user_by_telegram_id(current_user)
        if user:
            summary = transaction_handler.get_transactions_summary(
                user_id=user.user_id,
                start_date=(
                    datetime.strptime(start_date, "%Y-%m-%d").date()
                    if start_date
                    else None
                ),
                end_date=(
                    datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else None
                ),
            )
            return summary
        raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        logger.error(f"Error getting summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/transactions/categories")
async def get_category_summary(
    current_user: int = Depends(get_current_user),
    transaction_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    """Get transaction summary by category"""
    try:
        user = user_manager.get_user_by_telegram_id(current_user)
        if user:
            summary = transaction_handler.get_category_summary(
                user_id=user.user_id,
                transaction_type=transaction_type,
                start_date=(
                    datetime.strptime(start_date, "%Y-%m-%d").date()
                    if start_date
                    else None
                ),
                end_date=(
                    datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else None
                ),
            )
            return summary
        raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        logger.error(f"Error getting category summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# AI Processing Endpoints
@app.post("/api/ai/process-message")
async def process_message(
    request: ProcessMessageRequest, current_user: int = Depends(get_current_user)
):
    """Process natural language message with AI"""
    try:
        user = user_manager.get_user_by_telegram_id(current_user)
        if user:
            # Get user accounts for context
            accounts = account_manager.get_user_accounts(user.user_id)
            user_context = {
                "accounts": [
                    acc.__dict__ if hasattr(acc, "__dict__") else acc
                    for acc in accounts
                ]
            }

            result = ai_processor.process_message(request.message, user_context)
            return result
        raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ai/process-voice")
async def process_voice(
    file: UploadFile = File(...), current_user: int = Depends(get_current_user)
):
    """Process voice message and convert to text"""
    try:
        user = user_manager.get_user_by_telegram_id(current_user)
        if user:
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as temp_file:
                content = await file.read()
                temp_file.write(content)
                temp_file_path = temp_file.name

            try:
                # Process voice file
                text = await voice_handler.process_voice_file(temp_file_path)
                if text:
                    # Process with AI
                    accounts = account_manager.get_user_accounts(user.user_id)
                    user_context = {
                        "accounts": [
                            acc.__dict__ if hasattr(acc, "__dict__") else acc
                            for acc in accounts
                        ]
                    }
                    ai_result = ai_processor.process_message(text, user_context)

                    return {"success": True, "text": text, "ai_result": ai_result}
                else:
                    return {
                        "success": False,
                        "error": "Could not process voice message",
                    }
            finally:
                # Clean up temp file
                os.unlink(temp_file_path)

        raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        logger.error(f"Error processing voice: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Check Management Endpoints
@app.get("/api/checks")
async def get_checks(
    current_user: int = Depends(get_current_user),
    status: Optional[str] = None,
    type: Optional[str] = None,
):
    """Get user checks"""
    try:
        user = user_manager.get_user_by_telegram_id(current_user)
        if user:
            checks = check_manager.get_user_checks(
                user_id=user.user_id, status=status, check_type=type
            )
            return [c.__dict__ if hasattr(c, "__dict__") else c for c in checks]
        raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        logger.error(f"Error getting checks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/checks")
async def create_check(
    check_data: CheckCreate, current_user: int = Depends(get_current_user)
):
    """Create a new check"""
    try:
        user = user_manager.get_user_by_telegram_id(current_user)
        if user:
            check_id = check_manager.create_check(
                user_id=user.user_id,
                account_id=check_data.account_id,
                check_type=check_data.type,
                amount=Decimal(str(check_data.amount)),
                due_date=datetime.strptime(check_data.due_date, "%Y-%m-%d").date(),
                recipient_issuer=check_data.recipient_issuer,
                description=check_data.description,
            )
            if check_id:
                return {"success": True, "check_id": check_id}
            raise HTTPException(status_code=400, detail="Failed to create check")
        raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        logger.error(f"Error creating check: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Savings Plans Endpoints
@app.get("/api/savings-plans")
async def get_savings_plans(current_user: int = Depends(get_current_user)):
    """Get user savings plans"""
    try:
        user = user_manager.get_user_by_telegram_id(current_user)
        if user:
            plans = savings_manager.get_user_plans(user.user_id)
            return [p.__dict__ if hasattr(p, "__dict__") else p for p in plans]
        raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        logger.error(f"Error getting savings plans: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/savings-plans")
async def create_savings_plan(
    plan_data: SavingsPlanCreate, current_user: int = Depends(get_current_user)
):
    """Create a new savings plan"""
    try:
        user = user_manager.get_user_by_telegram_id(current_user)
        if user:
            plan_id = savings_manager.create_plan(
                user_id=user.user_id,
                plan_name=plan_data.plan_name,
                plan_type=plan_data.plan_type,
                target_amount=(
                    Decimal(str(plan_data.target_amount))
                    if plan_data.target_amount
                    else None
                ),
                monthly_contribution=(
                    Decimal(str(plan_data.monthly_contribution))
                    if plan_data.monthly_contribution
                    else None
                ),
                end_date=(
                    datetime.strptime(plan_data.end_date, "%Y-%m-%d").date()
                    if plan_data.end_date
                    else None
                ),
            )
            if plan_id:
                return {"success": True, "plan_id": plan_id}
            raise HTTPException(status_code=400, detail="Failed to create savings plan")
        raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        logger.error(f"Error creating savings plan: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Reports Endpoints
@app.get("/api/reports/monthly")
async def get_monthly_report(
    current_user: int = Depends(get_current_user),
    year: int = datetime.now().year,
    month: int = datetime.now().month,
):
    """Get monthly financial report"""
    try:
        user = user_manager.get_user_by_telegram_id(current_user)
        if user:
            report = report_generator.generate_monthly_report(
                user_id=user.user_id, year=year, month=month
            )
            return report
        raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        logger.error(f"Error generating monthly report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Categories endpoint
@app.get("/api/categories")
async def get_categories():
    """Get all available categories"""
    categories = {
        "expense": [
            {"name": "خانه", "icon": "🏠"},
            {"name": "خواربار", "icon": "🛒"},
            {"name": "رستوران و کافی‌شاپ", "icon": "🍔"},
            {"name": "حمل و نقل", "icon": "🚗"},
            {"name": "پوشاک", "icon": "👕"},
            {"name": "درمان و سلامت", "icon": "🏥"},
            {"name": "آموزش", "icon": "📚"},
            {"name": "سرگرمی", "icon": "🎮"},
            {"name": "موبایل و اینترنت", "icon": "📱"},
            {"name": "تعمیرات", "icon": "🔧"},
            {"name": "هدیه", "icon": "🎁"},
            {"name": "اقساط و وام", "icon": "💳"},
            {"name": "مالیات", "icon": "🏢"},
            {"name": "سفر", "icon": "✈️"},
            {"name": "سایر", "icon": "💰"},
        ],
        "income": [
            {"name": "حقوق", "icon": "💼"},
            {"name": "کسب و کار", "icon": "🏪"},
            {"name": "سرمایه‌گذاری", "icon": "💹"},
            {"name": "اجاره", "icon": "🏠"},
            {"name": "پروژه", "icon": "🎯"},
            {"name": "هدیه", "icon": "🎁"},
            {"name": "سایر", "icon": "💸"},
        ],
    }
    return categories


# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    try:
        init_database()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("web_api:app", host="0.0.0.0", port=8000, reload=True)
