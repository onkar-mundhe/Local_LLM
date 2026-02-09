#!/bin/bash
# Start Qwen Server - macOS
# Simply double-click this file to start the server!

# Change to the directory where this script is located
cd "$(dirname "$0")"

echo "=========================================="
echo "  Starting Qwen Server..."
echo "=========================================="
echo ""

# Check if Python is available
if command -v python3 &> /dev/null; then
    PYTHON=python3
elif command -v python &> /dev/null; then
    PYTHON=python
else
    echo "❌ Error: Python not found!"
    echo "Please install Python 3 first."
    echo ""
    echo "Install via Homebrew: brew install python3"
    echo "Or download from: https://www.python.org/downloads/"
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

echo "Using: $PYTHON"
echo ""

# Run the server
$PYTHON start_server.py

# Keep terminal open on exit
echo ""
echo "Server stopped."
read -p "Press Enter to close..."
