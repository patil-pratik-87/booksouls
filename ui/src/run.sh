#!/bin/bash

# BookSouls Character Chat UI - Development Setup & Run Script
cd "$(dirname "$0")"

echo "🔮 BookSouls Character Chat Interface"
echo "======================================="

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
    
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install dependencies"
        exit 1
    fi
    
    echo "✅ Dependencies installed successfully"
else
    echo "✅ Dependencies already installed"
fi

echo ""
echo "🚀 Starting development server..."
echo "   - Frontend: http://localhost:3001"
echo "   - Make sure BookSouls API is running on http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

npm run dev