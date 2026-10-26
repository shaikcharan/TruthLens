"""
TruthLens — Vercel Serverless Function Entry Point
Exposes the Flask WSGI 'app' instance for Vercel's Python runtime.
"""

import sys
from pathlib import Path

# Add project root directory to sys.path so modules like config, backend, database resolve
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import app

# Vercel serverless WSGI expects 'app'
