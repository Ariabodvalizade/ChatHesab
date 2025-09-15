# 🧪 Local Testing Instructions

## 🎯 What Was Created

I've created a complete local testing environment for your finance bot while keeping all your original files intact:

### 📁 New Files Created:
- `config_local.py` - Local configuration using SQLite
- `database/connection_local.py` - SQLite database adapter
- `main_local.py` - Local testing version of the bot
- `test_instructions.md` - This file

### 🔄 Original Files: **UNCHANGED**
All your original files (`main.py`, `config.py`, `database/connection.py`, etc.) remain exactly as they were.

## 🚀 How to Test Locally

### 1. Start the Local Bot
```bash
python3 main_local.py
```

### 2. Test Features
The local bot supports:
- ✅ User registration with `/start`
- ✅ Account creation with `/accounts`
- ✅ Simple transaction processing
- ✅ SQLite database storage
- ✅ Basic AI processing (simplified)

### 3. Sample Test Messages
Once the bot is running, message @FinanceAppReminderBot:

1. Start: `/start`
2. Add account: `/accounts` → "➕ افزودن حساب جدید"
3. Test transactions:
   - "50 هزار تومان نان خریدم"
   - "200 هزار تومان حقوق گرفتم"
   - "30 هزار تومان بنزین زدم"

## 🔧 Technical Details

### Local Changes:
- **Database**: MySQL → SQLite (`local_finance_bot.db`)
- **AI Processing**: Simplified rule-based system
- **Voice/Advanced features**: Disabled for local testing
- **Logging**: Saves to `bot_local.log`

### Database Schema:
The SQLite schema is automatically created with all necessary tables:
- `users`, `bank_accounts`, `transactions`, `checks`, etc.

## 🐛 Troubleshooting

### Bot Conflict Error:
If you see "Conflict: terminated by other getUpdates request":
- **This is normal!** It means another bot instance is running
- Only one bot can use the same token at a time
- Stop any other running instances first

### Missing Packages:
```bash
pip3 install python-telegram-bot==21.3 google-generativeai
```

## 🔄 Switching Back to Production

Your original files are unchanged. To run production version:
```bash
# Make sure MySQL is running
brew services start mysql

# Run original bot
python3 main.py
```

## 📊 Testing Results

The bot successfully:
- ✅ Connected to Telegram API
- ✅ Created SQLite database
- ✅ Initialized all tables
- ✅ Started polling for messages
- ✅ Basic transaction processing works

**Status: Ready for testing!** 🎉

## 🔍 What to Test

1. **User Registration**: `/start` command
2. **Account Management**: `/accounts` command
3. **Transaction Processing**: Send natural language messages
4. **Database Storage**: Check `local_finance_bot.db` file is created
5. **Error Handling**: Invalid inputs, missing data

The local version gives you a safe environment to test bot functionality without affecting your production setup or requiring MySQL/full AI integration.