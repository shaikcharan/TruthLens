"""
TruthLens Language Detection Module
Lightweight Unicode script analyzer for English, Hindi, Telugu, Tamil, Kannada, and Punjabi.
Deterministic, fast, and 100% offline.
"""

import re
from typing import Dict, Tuple

LANGUAGE_NAMES: Dict[str, str] = {
    "en": "English",
    "hi": "Hindi",
    "te": "Telugu",
    "ta": "Tamil",
    "kn": "Kannada",
    "pa": "Punjabi",
}

# Unicode Script Regex Patterns
DEVANAGARI_RE = re.compile(r"[\u0900-\u097F]")
TELUGU_RE = re.compile(r"[\u0C00-\u0C7F]")
TAMIL_RE = re.compile(r"[\u0B80-\u0BFF]")
KANNADA_RE = re.compile(r"[\u0C80-\u0CFF]")
GURMUKHI_RE = re.compile(r"[\u0A00-\u0A7F]")
LATIN_RE = re.compile(r"[a-zA-Z]")


def detect_language(text: str, user_selected: str = "auto") -> Tuple[str, str]:
    """
    Detect the primary language of the text.
    Returns a tuple of (language_code, language_name), e.g. ('hi', 'Hindi').
    """
    if user_selected in LANGUAGE_NAMES:
        return user_selected, LANGUAGE_NAMES[user_selected]

    if not text or not isinstance(text, str):
        return "en", "English"

    # Count script characters
    devanagari_count = len(DEVANAGARI_RE.findall(text))
    telugu_count = len(TELUGU_RE.findall(text))
    tamil_count = len(TAMIL_RE.findall(text))
    kannada_count = len(KANNADA_RE.findall(text))
    gurmukhi_count = len(GURMUKHI_RE.findall(text))
    latin_count = len(LATIN_RE.findall(text))

    counts = [
        ("hi", devanagari_count),
        ("te", telugu_count),
        ("ta", tamil_count),
        ("kn", kannada_count),
        ("pa", gurmukhi_count),
        ("en", latin_count),
    ]

    # Sort descending by character match count
    counts.sort(key=lambda x: x[1], reverse=True)
    top_code, top_count = counts[0]

    # If the highest count is 0 or less than 5 characters, default to English
    if top_count < 5:
        return "en", "English"

    return top_code, LANGUAGE_NAMES.get(top_code, "English")


def get_language_name(code: str) -> str:
    """Return human-readable language name for a given language code."""
    return LANGUAGE_NAMES.get(code.lower(), "English")
