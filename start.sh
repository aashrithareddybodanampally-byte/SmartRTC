#!/bin/bash

echo "🚀 TSRTC Smart Analytics Platform - Startup Script"
echo "=================================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

echo "✓ Python found: $(python3 --version)"
echo ""

# Navigate to backend directory
cd backend

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
    echo ""
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"
echo ""

# Install dependencies
echo "📥 Installing dependencies..."
pip install --quiet -r requirements.txt --break-system-packages
echo "✓ Dependencies installed"
echo ""

# Start the backend server
echo "🚀 Starting TSRTC Analytics Backend..."
echo ""
echo "Backend API: http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "To access the frontend, open frontend/index.html in your browser"
echo "Or run: python3 -m http.server 8080 (from frontend directory)"
echo ""
echo "Press Ctrl+C to stop the server"
echo "=================================================="
echo ""

python3 main.py