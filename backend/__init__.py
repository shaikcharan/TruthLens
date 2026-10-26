"""TruthLens Backend Core Logic Package"""
from .article_extractor import extract_content, validate_pasted_text, ExtractorError, SSRFBlockedError
from .language_detector import detect_language, get_language_name
from .ai_analyzer import analyze_news_content, AIAnalyzerError
from .evidence_checker import verify_claims_evidence
from .analysis_service import analyze_story

__all__ = [
    "extract_content",
    "validate_pasted_text",
    "ExtractorError",
    "SSRFBlockedError",
    "detect_language",
    "get_language_name",
    "analyze_news_content",
    "AIAnalyzerError",
    "verify_claims_evidence",
    "analyze_story",
]
