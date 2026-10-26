"""
TruthLens Article Extractor Module
Handles URL fetching, SSRF prevention (IP validation & redirect tracking), and clean text extraction.
"""

import socket
import ipaddress
import re
from urllib.parse import urlparse, urljoin
import requests
from bs4 import BeautifulSoup
from typing import Dict, Any, Tuple
from config import Config


class ExtractorError(Exception):
    """Base exception for article extraction failures."""
    pass


class SSRFBlockedError(ExtractorError):
    """Raised when a URL attempts to access private, loopback, or reserved IP ranges."""
    pass


def is_ip_private_or_reserved(ip_str: str) -> bool:
    """
    Check if an IP address belongs to private, loopback, link-local,
    multicast, or reserved address spaces.
    """
    try:
        ip = ipaddress.ip_address(ip_str)
        return (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
            or ip.is_unspecified
        )
    except ValueError:
        return True


def validate_url_safe(url: str) -> Tuple[str, str]:
    """
    Validate that the URL uses HTTP/HTTPS and does not resolve to private or loopback IP addresses.
    Returns (cleaned_url, hostname).
    Raises SSRFBlockedError or ExtractorError.
    """
    if not url or not isinstance(url, str):
        raise ExtractorError("URL cannot be empty.")

    url = url.strip()
    if len(url) > Config.MAX_URL_LENGTH:
        raise ExtractorError(f"URL exceeds maximum allowed length of {Config.MAX_URL_LENGTH} characters.")

    parsed = urlparse(url)
    scheme = parsed.scheme.lower()
    if scheme not in ("http", "https"):
        raise ExtractorError(f"Unsupported URL scheme '{scheme}'. Only HTTP and HTTPS are permitted.")

    hostname = parsed.hostname
    if not hostname:
        raise ExtractorError("Invalid URL: missing hostname.")

    # Check for direct localhost aliases
    if hostname.lower() in ("localhost", "127.0.0.1", "0.0.0.0", "::1", "local"):
        raise SSRFBlockedError(f"Access to '{hostname}' is blocked for security reasons.")

    # Resolve hostname to all associated IP addresses
    try:
        addr_infos = socket.getaddrinfo(hostname, None)
        if not addr_infos:
            raise ExtractorError(f"Could not resolve host '{hostname}'.")

        for addr_info in addr_infos:
            ip_str = addr_info[4][0]
            if is_ip_private_or_reserved(ip_str):
                raise SSRFBlockedError(
                    f"Access to host '{hostname}' (resolved to {ip_str}) is prohibited: Private or local IP range."
                )
    except socket.gaierror as e:
        raise ExtractorError(f"DNS resolution failed for '{hostname}': {str(e)}")

    return url, hostname


def fetch_url_with_ssrf_protection(url: str) -> requests.Response:
    """
    Fetches the URL while inspecting every redirect to prevent SSRF bypasses.
    Enforces maximum download byte size and timeout.
    """
    current_url, _ = validate_url_safe(url)
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "TruthLens-ResearchBot/1.0 (Media Literacy Project)"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
    )

    max_redirects = 5
    redirect_count = 0

    while True:
        try:
            # Stream response to check headers and prevent large file download bombs
            response = session.get(
                current_url,
                timeout=Config.REQUEST_TIMEOUT,
                allow_redirects=False,
                stream=True,
            )
        except requests.exceptions.Timeout:
            raise ExtractorError(f"Connection timed out after {Config.REQUEST_TIMEOUT}s while requesting {current_url}")
        except requests.exceptions.RequestException as e:
            raise ExtractorError(f"Network error while connecting to source: {str(e)}")

        # Check if redirect
        if response.is_redirect or response.is_permanent_redirect:
            redirect_count += 1
            if redirect_count > max_redirects:
                raise ExtractorError(f"Exceeded maximum redirect limit of {max_redirects}.")

            location = response.headers.get("Location")
            if not location:
                raise ExtractorError("Redirect response missing Location header.")

            # Resolve relative redirects
            next_url = urljoin(current_url, location)
            # Crucial: Validate new redirect target against SSRF!
            validate_url_safe(next_url)
            current_url = next_url
            continue

        # Check HTTP status
        if response.status_code != 200:
            raise ExtractorError(f"Website returned HTTP status {response.status_code}. Content could not be retrieved.")

        # Check Content-Type
        content_type = response.headers.get("Content-Type", "").lower()
        if not ("text/html" in content_type or "application/xhtml+xml" in content_type or "text/plain" in content_type):
            raise ExtractorError(f"Unsupported content type '{content_type}'. TruthLens only analyzes HTML or plain text.")

        # Enforce size limit during content download
        content_chunks = []
        downloaded_bytes = 0
        for chunk in response.iter_content(chunk_size=8192):
            downloaded_bytes += len(chunk)
            if downloaded_bytes > Config.MAX_DOWNLOAD_BYTES:
                raise ExtractorError(
                    f"Downloaded page exceeded size limit of {Config.MAX_DOWNLOAD_BYTES // (1024 * 1024)}MB."
                )
            content_chunks.append(chunk)

        response._content = b"".join(content_chunks)
        return response


def extract_content_from_html(html_bytes: bytes, source_url: str) -> Dict[str, Any]:
    """
    Parses HTML, removes ads, scripts, navigation, footers, and extract clean title,
    publisher, publish date, and readable article body.
    """
    soup = BeautifulSoup(html_bytes, "html.parser")

    # 1. Remove non-content, decorative, and clutter elements
    for element in soup(["script", "style", "nav", "footer", "header", "noscript", "aside", "svg", "form", "iframe"]):
        element.extract()

    # Also remove common advertisement, cookie notice, and social widget containers
    clutter_selectors = [
        "div[class*='cookie']", "div[id*='cookie']",
        "div[class*='advertisement']", "div[id*='advertisement']",
        "div[class*='ad-']", "div[id*='ad-']",
        "div[class*='share']", "div[id*='share']",
        "div[class*='sidebar']", "div[id*='sidebar']",
        "div[class*='comment']", "div[id*='comment']",
        "div[class*='related']", "div[id*='related']",
        "div[class*='newsletter']", "div[id*='newsletter']",
    ]
    for sel in clutter_selectors:
        for match in soup.select(sel):
            match.decompose()

    # 2. Extract title
    title = ""
    og_title = soup.find("meta", property="og:title")
    if og_title and og_title.get("content"):
        title = og_title["content"].strip()
    if not title and soup.title and soup.title.string:
        title = soup.title.string.strip()
    if not title:
        h1 = soup.find("h1")
        if h1:
            title = h1.get_text().strip()
    if not title:
        title = "Extracted Article Story"

    # 3. Extract Publisher / Source
    publisher = ""
    og_site = soup.find("meta", property="og:site_name")
    if og_site and og_site.get("content"):
        publisher = og_site["content"].strip()
    if not publisher:
        meta_pub = soup.find("meta", attrs={"name": re.compile(r"publisher|author|source", re.I)})
        if meta_pub and meta_pub.get("content"):
            publisher = meta_pub["content"].strip()
    if not publisher and source_url:
        parsed_url = urlparse(source_url)
        publisher = parsed_url.netloc.replace("www.", "")

    # 4. Extract Publication Date
    publish_date = ""
    date_meta = soup.find("meta", property="article:published_time") or \
                soup.find("meta", attrs={"name": re.compile(r"publish.?date|pubdate|date", re.I)})
    if date_meta and date_meta.get("content"):
        publish_date = date_meta["content"].strip()[:10]  # e.g., YYYY-MM-DD
    if not publish_date:
        time_tag = soup.find("time")
        if time_tag:
            publish_date = time_tag.get("datetime", "") or time_tag.get_text().strip()
            publish_date = publish_date[:10]

    # 5. Extract body text prioritizing article / main / paragraph elements
    article_tag = soup.find("article") or soup.find("main") or soup.find(id=re.compile(r"article|content|body", re.I)) or soup.find(class_=re.compile(r"article|content|body", re.I))
    
    if article_tag:
        paragraphs = article_tag.find_all("p")
    else:
        paragraphs = soup.find_all("p")

    text_parts = [p.get_text().strip() for p in paragraphs if len(p.get_text().strip()) > 20]
    full_text = "\n\n".join(text_parts)

    # Fallback to general text if paragraph extraction returned too little
    if len(full_text) < Config.MIN_ARTICLE_CHARS:
        full_text = soup.get_text(separator="\n", strip=True)

    # Enforce bounds
    if len(full_text) < Config.MIN_ARTICLE_CHARS:
        raise ExtractorError(
            "Could not extract sufficient readable article text from the URL. The page may require JavaScript or authentication."
        )

    if len(full_text) > Config.MAX_ARTICLE_CHARS:
        full_text = full_text[: Config.MAX_ARTICLE_CHARS] + "\n\n[Article truncated due to length limits]"

    return {
        "title": title,
        "publisher": publisher or "Unknown Publisher",
        "publish_date": publish_date or "",
        "text": full_text,
        "source_url": source_url,
        "source_type": "url",
        "char_count": len(full_text),
    }


def extract_content(url: str) -> Dict[str, Any]:
    """Public wrapper to fetch and parse a news article from a safe URL."""
    response = fetch_url_with_ssrf_protection(url)
    return extract_content_from_html(response.content, url)


def validate_pasted_text(
    text: str, custom_title: str = "", custom_publisher: str = "", custom_date: str = ""
) -> Dict[str, Any]:
    """Validates raw pasted text submitted by the user."""
    if not text or not isinstance(text, str):
        raise ExtractorError("Pasted article text cannot be empty.")

    cleaned_text = text.strip()
    if len(cleaned_text) < Config.MIN_ARTICLE_CHARS:
        raise ExtractorError(
            f"Input text is too short ({len(cleaned_text)} characters). Please provide at least {Config.MIN_ARTICLE_CHARS} characters."
        )

    if len(cleaned_text) > Config.MAX_ARTICLE_CHARS:
        cleaned_text = cleaned_text[: Config.MAX_ARTICLE_CHARS]

    lines = [l.strip() for l in cleaned_text.split("\n") if l.strip()]

    # Infer headline if not provided
    title = custom_title.strip() if custom_title else ""
    publisher = custom_publisher.strip() if custom_publisher else "Pasted Source"
    publish_date = custom_date.strip() if custom_date else ""

    if not title and lines:
        first_line = lines[0]
        # Check if first line contains "by [Publisher]" or title
        if len(first_line) <= 120:
            title = first_line
        else:
            title = first_line[:80] + "..."

    # Check for "by Publisher" or dates in the first few lines
    for line in lines[:3]:
        by_match = re.search(r"\bby\s+([A-Za-z0-9\s&]+)", line, re.I)
        if by_match and publisher == "Pasted Source":
            publisher = by_match.group(1).strip()
        date_match = re.search(r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December|\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\s+\d{1,2},?\s+\d{4}?", line, re.I)
        if date_match and not publish_date:
            publish_date = date_match.group(0).strip()

    return {
        "title": title or "Pasted Article Story",
        "publisher": publisher,
        "publish_date": publish_date,
        "text": cleaned_text,
        "source_url": None,
        "source_type": "text",
        "char_count": len(cleaned_text),
    }
