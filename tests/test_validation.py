"""
Unit tests for input validation, SSRF protections, and language detection.
"""

import pytest
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.article_extractor import (
    validate_url_safe,
    is_ip_private_or_reserved,
    validate_pasted_text,
    ExtractorError,
    SSRFBlockedError,
)
from backend.language_detector import detect_language, get_language_name
from config import Config


class TestSSRFAndURLValidation:
    """Tests URL validation and SSRF defenses."""

    def test_empty_url_rejected(self):
        with pytest.raises(ExtractorError, match="URL cannot be empty"):
            validate_url_safe("")

    def test_unsupported_schemes_rejected(self):
        for scheme in ["ftp://example.com", "file:///etc/passwd", "gopher://bad.com"]:
            with pytest.raises(ExtractorError, match="Unsupported URL scheme"):
                validate_url_safe(scheme)

    def test_localhost_hostname_rejected(self):
        for host in ["http://localhost", "http://127.0.0.1", "http://0.0.0.0", "http://local"]:
            with pytest.raises(SSRFBlockedError):
                validate_url_safe(host)

    def test_private_ip_detection(self):
        # RFC 1918 Private Ranges
        assert is_ip_private_or_reserved("10.0.0.1") is True
        assert is_ip_private_or_reserved("172.16.0.5") is True
        assert is_ip_private_or_reserved("192.168.1.1") is True
        # Loopback & Link-local
        assert is_ip_private_or_reserved("127.0.0.1") is True
        assert is_ip_private_or_reserved("169.254.1.1") is True
        # Public IP
        assert is_ip_private_or_reserved("8.8.8.8") is False
        assert is_ip_private_or_reserved("93.184.216.34") is False

    def test_excessive_url_length(self):
        long_url = "https://example.com/" + "a" * (Config.MAX_URL_LENGTH + 10)
        with pytest.raises(ExtractorError, match="exceeds maximum allowed length"):
            validate_url_safe(long_url)


class TestPastedTextValidation:
    """Tests pasted text constraints."""

    def test_empty_text_rejected(self):
        with pytest.raises(ExtractorError, match="cannot be empty"):
            validate_pasted_text("")

    def test_short_text_rejected(self):
        with pytest.raises(ExtractorError, match="too short"):
            validate_pasted_text("Too short text.")

    def test_valid_text_extraction(self):
        sample = "This is a legitimate news story discussing local policy announcements and economic developments."
        result = validate_pasted_text(sample, custom_title="Custom Headline")
        assert result["title"] == "Custom Headline"
        assert result["source_type"] == "text"
        assert result["char_count"] == len(sample)


class TestLanguageDetection:
    """Tests multilingual Unicode script detection."""

    def test_english_detection(self):
        text = "Breaking report: The health ministry announced major revisions to clinic protocols today."
        code, name = detect_language(text)
        assert code == "en"
        assert name == "English"

    def test_hindi_detection(self):
        text = "ताज़ा समाचार: स्वास्थ्य मंत्रालय ने आज देश भर के अस्पतालों के लिए नई गाइडलाइंस जारी की हैं।"
        code, name = detect_language(text)
        assert code == "hi"
        assert name == "Hindi"

    def test_telugu_detection(self):
        text = "ముఖ్య సమాచారం: రాష్ట్ర ఆరోగ్య శాఖ ఈరోజు కీలక ప్రకటన విడుదల చేసింది. కొత్త మార్గదర్శకాలు అమలులోకి వచ్చాయి."
        code, name = detect_language(text)
        assert code == "te"
        assert name == "Telugu"

    def test_tamil_detection(self):
        text = "முக்கிய செய்தி: தமிழகத்தில் புதிய நலத்திட்டம் தொடங்கப்பட்டது என்று அரசு அறிவித்துள்ளது."
        code, name = detect_language(text)
        assert code == "ta"
        assert name == "Tamil"

    def test_kannada_detection(self):
        text = "ಮುಖ್ಯ ಸುದ್ದಿ: ಕರ್ನಾಟಕ ರಾಜ್ಯ ಸರ್ಕಾರವು ರೈತರಿಗಾಗಿ ಹೊಸ ಪರಿಹಾರ ಯೋಜನೆಯನ್ನು ಘೋಷಿಸಿದೆ."
        code, name = detect_language(text)
        assert code == "kn"
        assert name == "Kannada"

    def test_user_override(self):
        # Even if text is in Hindi script, user override should be honored
        text = "नमस्ते दुनिया"
        code, name = detect_language(text, user_selected="hi")
        assert code == "hi"
        assert name == "Hindi"
