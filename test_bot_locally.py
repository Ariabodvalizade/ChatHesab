#!/usr/bin/env python3
"""
Simple script to test the bot locally
This simulates what happens when you run the bot
"""

import asyncio
from datetime import datetime

# Test the local components
from config_local import BOT_TOKEN, WELCOME_MESSAGE
from database.connection_local import get_local_db

# Test local bot classes
from main_local import LocalUserManager, LocalAccountManager, LocalTransactionHandler, LocalAIProcessor

async def test_bot_components():
    """Test all bot components locally"""
    
    print("🧪 Testing Finance Bot Components Locally")
    print("=" * 50)
    
    # Test database
    print("\n1️⃣ Testing Database...")
    db = get_local_db()
    tables = db.execute_query('SELECT name FROM sqlite_master WHERE type="table"', fetch_all=True)
    print(f"✅ Database has {len(tables)} tables")
    
    # Test user management
    print("\n2️⃣ Testing User Management...")
    user_manager = LocalUserManager()
    test_telegram_id = 12345678
    
    user_id = user_manager.create_user(
        telegram_id=test_telegram_id,
        username="test_user",
        first_name="Test",
        last_name="User"
    )
    print(f"✅ Created test user with ID: {user_id}")
    
    # Test subscription check
    subscription = user_manager.check_subscription_status(user_id)
    print(f"✅ Subscription status: {subscription}")
    
    # Test account management
    print("\n3️⃣ Testing Account Management...")
    account_manager = LocalAccountManager()
    
    account_id = account_manager.create_account(
        user_id=user_id,
        bank_name="ملت",
        account_name="حساب اصلی",
        initial_balance=5000000
    )
    print(f"✅ Created test account with ID: {account_id}")
    
    accounts = account_manager.get_user_accounts(user_id)
    print(f"✅ User has {len(accounts)} accounts")
    
    # Test AI processor
    print("\n4️⃣ Testing AI Processing...")
    ai_processor = LocalAIProcessor()
    
    test_messages = [
        "50 هزار تومان نان خریدم",
        "200 هزار تومان حقوق گرفتم",
        "30 هزار تومان بنزین زدم"
    ]
    
    for message in test_messages:
        result = ai_processor.process_message(message, {"accounts": accounts})
        print(f"✅ Processed: '{message}' → {result['transaction_type']} {result['amount']:,} تومان")
    
    # Test transaction handling
    print("\n5️⃣ Testing Transaction Storage...")
    transaction_handler = LocalTransactionHandler()
    
    transaction_id = transaction_handler.create_transaction(
        user_id=user_id,
        account_id=account_id,
        transaction_type="expense",
        amount=50000,
        category="خواربار",
        description="خرید نان"
    )
    print(f"✅ Created test transaction with ID: {transaction_id}")
    
    # Test data retrieval
    print("\n6️⃣ Testing Data Retrieval...")
    transactions = db.execute_query(
        "SELECT * FROM transactions WHERE user_id = ?", 
        (user_id,), 
        fetch_all=True
    )
    print(f"✅ User has {len(transactions)} transactions")
    
    print("\n🎉 All components working perfectly!")
    print("\n" + "=" * 50)
    print("🚀 HOW TO RUN THE ACTUAL BOT:")
    print("1. Open terminal")
    print("2. cd /Users/ariabod/finance_bot")
    print("3. python3 main_local.py")
    print("4. Message @FinanceAppReminderBot on Telegram")
    print("5. Send: /start")
    print("\n💡 Test messages to try:")
    for msg in test_messages:
        print(f"   • {msg}")
    
    return True

if __name__ == "__main__":
    try:
        result = asyncio.run(test_bot_components())
        print(f"\n✅ Test completed successfully!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()