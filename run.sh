#!/bin/bash

# Quick start script for the Conversational AI Webapp

echo "🚀 Starting Conversational AI Webapp..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "📝 Please copy config.example.env to .env and add your API keys:"
    echo "   cp config.example.env .env"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -q -r requirements.txt

# Run the application
echo "✨ Starting server on http://localhost:8000"
echo "   Press Ctrl+C to stop"
echo ""
python app.py
