"""
Unit tests for article extraction from HTML and mock HTTP responses.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.article_extractor import (
    extract_content_from_html,
    fetch_url_with_ssrf_protection,
    ExtractorError,
    SSRFBlockedError,
)


class TestHtmlArticleExtractor:
    """Tests HTML parsing, title extraction, and boilerplate stripping."""

    def test_extract_clean_html_with_og_title(self):
        sample_html = b"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta property="og:title" content="Verified OpenGraph Headline">
            <title>HTML Browser Title</title>
        </head>
        <body>
            <nav><a href="/">Home</a></nav>
            <article>
                <h1>Inside Header</h1>
                <p>This is the first paragraph detailing the comprehensive public policy shift.</p>
                <p>This is the second paragraph providing background context and expert statements.</p>
            </article>
            <footer>Copyright 2026</footer>
        </body>
        </html>
        """
        result = extract_content_from_html(sample_html, "https://example.com/story")
        assert result["title"] == "Verified OpenGraph Headline"
        assert "This is the first paragraph" in result["text"]
        assert "This is the second paragraph" in result["text"]
        assert "Home" not in result["text"]
        assert "Copyright 2026" not in result["text"]

    def test_extract_title_from_h1_fallback(self):
        sample_html = b"""
        <html>
        <body>
            <h1>Heading Headline</h1>
            <p>This paragraph contains sufficient characters to satisfy the minimum length threshold easily.</p>
        </body>
        </html>
        """
        result = extract_content_from_html(sample_html, "https://example.com/h1")
        assert result["title"] == "Heading Headline"

    def test_insufficient_body_text_raises_error(self):
        sample_html = b"<html><body><p>Short</p></body></html>"
        with pytest.raises(ExtractorError, match="Could not extract sufficient readable article text"):
            extract_content_from_html(sample_html, "https://example.com/empty")


class TestNetworkFetchProtections:
    """Tests SSRF and network response protections."""

    @patch("backend.article_extractor.validate_url_safe")
    @patch("requests.Session.get")
    def test_redirect_to_private_ip_is_blocked(self, mock_get, mock_validate):
        # First request to external URL passes validation
        mock_validate.side_effect = [
            ("http://public-site.com", "public-site.com"),
            SSRFBlockedError("Redirect target resolved to private IP"),
        ]

        # Simulate redirect response
        mock_resp = MagicMock()
        mock_resp.is_redirect = True
        mock_resp.is_permanent_redirect = False
        mock_resp.headers = {"Location": "http://192.168.1.1/admin"}
        mock_get.return_value = mock_resp

        with pytest.raises(SSRFBlockedError):
            fetch_url_with_ssrf_protection("http://public-site.com")

    @patch("backend.article_extractor.validate_url_safe")
    @patch("requests.Session.get")
    def test_unsupported_content_type_rejected(self, mock_get, mock_validate):
        mock_validate.return_value = ("http://public-site.com/image.png", "public-site.com")
        mock_resp = MagicMock()
        mock_resp.is_redirect = False
        mock_resp.is_permanent_redirect = False
        mock_resp.status_code = 200
        mock_resp.headers = {"Content-Type": "image/png"}
        mock_get.return_value = mock_resp

        with pytest.raises(ExtractorError, match="Unsupported content type"):
            fetch_url_with_ssrf_protection("http://public-site.com/image.png")
