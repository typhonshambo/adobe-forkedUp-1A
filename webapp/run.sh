#!/bin/bash

# PDF Analyzer Web Application Launcher
echo "🚀 Starting PDF Analyzer Web Application..."
echo "==========================================="

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed. Please install Python3 to continue."
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo "❌ app.py not found. Please run this script from the webapp directory."
    exit 1
fi

# Install dependencies if needed
echo "📦 Checking dependencies..."
if [ ! -f "requirements.txt" ]; then
    echo "❌ requirements.txt not found."
    exit 1
fi

# Install Flask and dependencies
echo "🔧 Installing Flask dependencies..."
pip3 install -r requirements.txt

echo ""
echo "✅ Dependencies installed successfully!"
echo ""

# Start the Flask application
echo "🌟 Starting Flask server..."
echo "📱 Web application will be available at: http://localhost:5000"
echo "🛑 Press Ctrl+C to stop the server"
echo ""

# Run the Flask app
python3 app.py
