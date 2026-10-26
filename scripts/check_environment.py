"""
TruthLens Environment Diagnostics & Pre-Flight Check Script
Verifies Python version, package dependencies, port 8765 availability,
database integrity, and environment configuration.
"""

import sys
import socket
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import Config
from database.db_manager import check_db_health


def check_python_version() -> bool:
    print(f"[*] Python Version: {sys.version.split()[0]}")
    if sys.version_info >= (3, 9):
        print("    [OK] Python version is compatible (>= 3.9).")
        return True
    else:
        print("    [FAIL] Python 3.9 or higher is required.")
        return False


def check_dependencies() -> bool:
    print("[*] Checking Core Dependencies:")
    packages = [
        ("Flask", "flask"),
        ("Requests", "requests"),
        ("BeautifulSoup4", "bs4"),
        ("Python-Dotenv", "dotenv"),
        ("PyTest", "pytest"),
    ]
    all_ok = True
    for name, module in packages:
        try:
            __import__(module)
            print(f"    [OK] {name}")
        except ImportError:
            print(f"    [FAIL] {name} is not installed.")
            all_ok = False

    # Check Gemini SDKs (modern or legacy)
    has_genai = False
    try:
        __import__("google.genai")
        print("    [OK] google-genai (Modern SDK)")
        has_genai = True
    except ImportError:
        pass

    try:
        __import__("google.generativeai")
        print("    [OK] google-generativeai (Compatible SDK)")
        has_genai = True
    except ImportError:
        pass

    if not has_genai:
        print("    [WARN] Neither google-genai nor google-generativeai installed. Running in mock mode.")

    return all_ok


def check_port_availability() -> bool:
    print(f"[*] Checking Port {Config.PORT} ({Config.HOST}):")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((Config.HOST, Config.PORT))
            print(f"    [OK] Port {Config.PORT} is free and ready.")
            return True
        except OSError:
            print(f"    [FAIL] Port {Config.PORT} is already in use!")
            print(f"           Close the conflicting application or configure another port in config.py.")
            return False


def check_database() -> bool:
    print(f"[*] Checking Database at {Config.DATABASE_PATH}:")
    health = check_db_health()
    if health.get("healthy"):
        print(f"    [OK] Database file exists and tables are initialized.")
        print(f"         Verified tables: {', '.join(health.get('tables', []))}")
        return True
    else:
        print(f"    [INFO] Database needs initialization. Run 'python scripts/init_database.py'")
        return False


def check_api_configuration():
    print("[*] Checking Gemini AI Configuration:")
    print(f"    Selected Model: {Config.GEMINI_MODEL}")
    if Config.is_api_key_configured():
        print(f"    [OK] GEMINI_API_KEY is configured: {Config.get_masked_api_key()}")
    else:
        print("    [INFO] GEMINI_API_KEY is not set. TruthLens will run in Offline Demonstration Mode.")
        print("           (Full UI, extraction, and rhetorical analysis demo remain fully functional).")


def main():
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    print("=" * 65)
    print("TruthLens -- Pre-Flight System Diagnostic")
    print("=" * 65)

    py_ok = check_python_version()
    deps_ok = check_dependencies()
    port_ok = check_port_availability()
    db_ok = check_database()
    check_api_configuration()

    print("=" * 65)
    if py_ok and deps_ok and port_ok:
        print("[OK] Pre-flight checks passed! TruthLens is ready to launch.")
        print(f"     Run: python app.py  (or double-click RUN_TRUTHLENS.bat)")
    else:
        print("[WARN] Some checks reported issues. Please review details above.")
    print("=" * 65)


if __name__ == "__main__":
    main()
