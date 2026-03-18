#!/usr/bin/env bash
# FinSight - Start Script
set -euo pipefail

echo "=== FinSight Financial Analytics Dashboard ==="
echo ""

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "[1/3] Creating virtual environment..."
    python3 -m venv venv
else
    echo "[1/3] Virtual environment exists."
fi

# Activate and install dependencies
echo "[2/3] Installing dependencies..."
source venv/bin/activate
pip install -q -r requirements.txt

# Create instance directory
mkdir -p instance

# Start application
echo "[3/3] Starting FinSight on port 8001..."
echo ""
echo "  Dashboard:  http://localhost:8001"
echo "  API:        http://localhost:8001/api/stocks"
echo "  Portfolio:  http://localhost:8001/portfolio"
echo "  Sentiment:  http://localhost:8001/sentiment"
echo ""
python app.py
