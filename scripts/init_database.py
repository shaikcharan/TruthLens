"""
TruthLens Database Initializer Script
Can be run independently to create or reset the SQLite database.
Usage:
    python scripts/init_database.py [--reset] [--path custom/path.db]
"""

import sys
import argparse
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from database.db_manager import init_db, check_db_health
from config import Config


def main():
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    parser = argparse.ArgumentParser(description="TruthLens Database Initializer")
    parser.add_argument("--reset", action="store_true", help="Drop and recreate all tables")
    parser.add_argument("--path", type=str, default=None, help="Custom database path")
    args = parser.parse_args()

    db_path = args.path or str(Config.DATABASE_PATH)
    print(f"[*] Initializing TruthLens database at: {db_path}")

    if args.reset:
        print("[!] Reset flag provided: Dropping existing tables and rebuilding schema...")

    init_db(db_path=db_path, reset=args.reset)
    health = check_db_health(db_path=db_path)

    if health.get("healthy"):
        print("[OK] Database initialized successfully!")
        print(f"    Tables verified: {', '.join(health.get('tables', []))}")
        print(f"    File size: {health.get('size_kb')} KB")
    else:
        print(f"[FAIL] Database initialization failed: {health.get('error')}")
        sys.exit(1)


if __name__ == "__main__":
    main()
