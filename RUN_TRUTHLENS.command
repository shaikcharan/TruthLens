#!/usr/bin/env bash
# ==============================================================================
# TruthLens Launcher for macOS & Linux
# ==============================================================================

# Change to script directory
cd "$(dirname "$0")" || exit 1

echo "=============================================================================="
echo "                     TruthLens Launch Controller"
echo "=============================================================================="

# Check Python 3
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] python3 could not be found. Please install Python 3.9+."
    exit 1
fi

# Create virtual environment if missing
if [ ! -d ".venv" ]; then
    echo "[*] Creating virtual environment (.venv)..."
    python3 -m venv .venv
fi

# Install dependencies if flag missing
if [ ! -f ".venv/.installed_flag" ]; then
    echo "[*] Installing pinned requirements..."
    .venv/bin/pip install --upgrade pip
    .venv/bin/pip install -r requirements.txt
    touch .venv/.installed_flag
    echo "[OK] Dependencies installed."
fi

# Create storage directory
mkdir -p storage

# Initialize database
.venv/bin/python scripts/init_database.py

# Check port 8765
if lsof -i :8765 -sTCP:LISTEN >/dev/null 2>&1; then
    echo "=============================================================================="
    echo "Port 8765 is already in use. Close the existing TruthLens instance or select a different port in config.py."
    echo "=============================================================================="
    exit 1
fi

# Open browser in background
if command -v open &> /dev/null; then
    (sleep 2 && open http://127.0.0.1:8765) &
elif command -v xdg-open &> /dev/null; then
    (sleep 2 && xdg-open http://127.0.0.1:8765) &
fi

# Start application
.venv/bin/python app.py
