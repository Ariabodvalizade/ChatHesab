#!/bin/bash

echo "🔧 Setting up Finance Bot environment..."

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing required packages..."
pip install -r requirements.txt

# Fix python module structure
echo "🔧 Fixing module structure..."
# Create symbolic link for persian_utils in modules
if [ ! -f "modules/persian_utils.py" ]; then
    ln -sf "utils/persian_utils.py" "modules/persian_utils.py"
    echo "✅ Created symbolic link for persian_utils.py"
fi

# Create symbolic link for calendar_utils in modules
if [ ! -f "modules/calendar_utils.py" ]; then
    ln -sf "utils/calendar_utils.py" "modules/calendar_utils.py"
    echo "✅ Created symbolic link for calendar_utils.py"
fi

# Create symbolic link for formatter in modules
if [ ! -f "modules/formatter.py" ]; then
    ln -sf "utils/formatter.py" "modules/formatter.py"
    echo "✅ Created symbolic link for formatter.py"
fi

# Create symbolic link for database connection in modules
if [ ! -f "modules/connection.py" ]; then
    ln -sf "database/connection.py" "modules/connection.py"
    echo "✅ Created symbolic link for connection.py"
fi

echo "✅ Setup complete!"
echo ""
echo "To run the bot:"
echo "1. Activate the virtual environment:"
echo "   source venv/bin/activate"
echo "2. Run the bot:"
echo "   python3 main_local.py"
echo ""
echo "⚠️ Note: If you encounter 'Conflict' errors, close all other instances"
echo "   of the bot before running it again."
