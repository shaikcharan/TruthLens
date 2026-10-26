"""
TruthLens Configuration Module
Centralized settings for port, network binding, models, database, and security limits.
"""

import os
import tempfile
from pathlib import Path
from dotenv import load_dotenv

# Base Directory of TruthLens Project
BASE_DIR = Path(__file__).resolve().parent

# Load environment variables from .env file if it exists
ENV_PATH = BASE_DIR / ".env"
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
else:
    # Also attempt loading from default environment
    load_dotenv()


class Config:
    """Application configuration object."""

    # Project metadata
    PROJECT_NAME = "TruthLens"
    VERSION = "1.0.0"

    # Networking & Port Isolation (Requirement: Port 8765 exclusively)
    PORT = int(os.getenv("PORT", 8765))
    HOST = os.getenv("HOST", "127.0.0.1")

    # Security & Sessions
    SECRET_KEY = os.getenv(
        "SECRET_KEY", "truthlens-dev-insecure-secret-key-10829374182479"
    )

    # Google Gemini AI Configuration
    # Key must be obtained via https://aistudio.google.com/
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

    # Centralized model configuration (Never hardcode model name in other files)
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash").strip()

    # Storage & SQLite Database
    STORAGE_DIR = BASE_DIR / "storage"
    if os.getenv("VERCEL"):
        # On Vercel serverless functions, the root filesystem is read-only.
        # SQLite must use the writable temporary directory (/tmp).
        DATABASE_PATH = Path(
            os.getenv("DATABASE_PATH", str(Path(tempfile.gettempdir()) / "truthlens.db"))
        )
    else:
        DATABASE_PATH = Path(
            os.getenv("DATABASE_PATH", str(STORAGE_DIR / "truthlens.db"))
        )

    # Article Extraction & Input Constraints
    REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", 15))
    MAX_ARTICLE_CHARS = int(os.getenv("MAX_ARTICLE_CHARS", 25000))
    MIN_ARTICLE_CHARS = 30
    MAX_URL_LENGTH = 2048
    MAX_DOWNLOAD_BYTES = 2 * 1024 * 1024  # 2 Megabytes limit to mitigate SSRF bombs

    # Supported Languages
    SUPPORTED_LANGUAGES = {
        "auto": "Auto-Detect (English, Hindi, Telugu, Tamil, Kannada, Punjabi)",
        "en": "English",
        "hi": "Hindi (हिंदी)",
        "te": "Telugu (తెలుగు)",
        "ta": "Tamil (தமிழ்)",
        "kn": "Kannada (ಕನ್ನಡ)",
        "pa": "Punjabi (ਪੰਜਾਬੀ)",
    }

    # External Evidence Verification (Truth Checking)
    ENABLE_FACT_CHECK_SEARCH = (
        os.getenv("ENABLE_FACT_CHECK_SEARCH", "true").lower() in ("true", "1", "yes")
    )

    @classmethod
    def is_api_key_configured(cls) -> bool:
        """Returns True if a non-empty Gemini API key is present."""
        return bool(cls.GEMINI_API_KEY and len(cls.GEMINI_API_KEY) > 5)

    @classmethod
    def get_masked_api_key(cls) -> str:
        """Safe presentation of API key status without leaking secrets."""
        if not cls.is_api_key_configured():
            return "Not Configured (Running in Offline / Mock Mode)"
        key = cls.GEMINI_API_KEY
        if len(key) <= 8:
            return "Configured (***)"
        return f"Configured (ends with ...{key[-4:]})"
