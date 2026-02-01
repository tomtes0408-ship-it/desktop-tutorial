#!/bin/bash
# BotCast Startup Script
# Automatically starts both backend and frontend servers

echo "🤖 ============================================"
echo "   BotCast Platform Launcher"
echo "============================================"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+"
    exit 1
fi

# Start backend server
echo ""
echo "🚀 Starting BotCast Backend Server (Port 5000)..."
cd "$(dirname "$0")"
python3 botcast_server.py &
BACKEND_PID=$!
echo "   Backend PID: $BACKEND_PID"

# Wait for backend to start
sleep 2

# Check if backend is running
if ! curl -s http://localhost:5000/api/health > /dev/null; then
    echo "❌ Backend server failed to start"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

echo "✅ Backend started successfully"

# Start frontend server
echo ""
echo "🚀 Starting BotCast Frontend Server (Port 8000)..."
cd "$(dirname "$0")/botcast"
python3 -m http.server 8000 &
FRONTEND_PID=$!
echo "   Frontend PID: $FRONTEND_PID"

# Wait for frontend to start
sleep 1

echo "✅ Frontend started successfully"

echo ""
echo "============================================"
echo "🎉 BotCast Platform is Ready!"
echo "============================================"
echo ""
echo "📱 Open your browser:"
echo "   👉 http://localhost:8000"
echo ""
echo "🔧 API Documentation:"
echo "   👉 http://localhost:5000/api/health"
echo ""
echo "📚 Documentation:"
echo "   - Quick Start: QUICK_START.md"
echo "   - Full Docs: BOTCAST_README.md"
echo ""
echo "🛑 To stop servers:"
echo "   Press Ctrl+C here, or:"
echo "   kill $BACKEND_PID $FRONTEND_PID"
echo ""
echo "============================================"
echo ""

# Handle graceful shutdown
trap "echo ''; echo 'Shutting down BotCast...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; wait; echo 'Goodbye! 👋'" INT

# Wait for both processes
wait
