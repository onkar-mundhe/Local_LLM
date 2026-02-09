#!/bin/bash
# Start Qwen Server - macOS/Linux
# Double-click this file or run: ./Start_Qwen_Server.sh

# Change to script directory
cd "$(dirname "$0")"

echo "Starting Qwen Server..."
echo ""

# Check if Python is available
if command -v python3 &> /dev/null; then
    PYTHON=python3
elif command -v python &> /dev/null; then
    PYTHON=python
else
    echo "Error: Python not found!"
    echo "Please install Python 3 first."
    read -p "Press Enter to exit..."
    exit 1
fi

# Run the server
$PYTHON start_server.py

# Keep terminal open on exit (useful when double-clicked)
echo ""
read -p "Press Enter to exit..."
