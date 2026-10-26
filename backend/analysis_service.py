"""
TruthLens Analysis Service
Orchestrates input validation, extraction, language detection, AI analysis,
evidence verification, and atomic database persistence.
"""

import uuid
from typing import Dict, Any, Optional
from config import Config
from backend.article_extractor import extract_content, validate_pasted_text, ExtractorError
from backend.language_detector import detect_language
from backend.ai_analyzer import analyze_news_content
from backend.evidence_checker import verify_claims_evidence
from database.db_manager import save_analysis


def analyze_story(
    source_type: str,
    content_input: str,
    selected_language: str = "auto",
    custom_title: str = "",
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Executes the end-to-end media literacy analysis pipeline.

    Args:
        source_type: 'url' or 'text'
        content_input: URL string or pasted article text
        selected_language: 'auto', 'en', 'hi', 'te', 'ta', 'kn', or 'pa'
        custom_title: Optional user-provided headline for pasted text
        db_path: Optional custom SQLite database path (for isolated testing)

    Returns:
        Structured analysis report dictionary with analysis ID and saved state.
    """
    # Step 1: Input Validation & Content Extraction
    if source_type == "url":
        extracted = extract_content(content_input)
    elif source_type == "text":
        extracted = validate_pasted_text(content_input, custom_title=custom_title)
    else:
        raise ExtractorError(f"Unsupported source type '{source_type}'. Choose 'url' or 'text'.")

    article_text = extracted["text"]
    title = custom_title.strip() if custom_title.strip() else (extracted.get("title") or "Analyzed Story")
    source_url = extracted.get("source_url")
    publisher = extracted.get("publisher") or "Direct Submission"
    publish_date = extracted.get("publish_date") or ""

    # Step 2: Language Detection
    lang_code, lang_name = detect_language(article_text, user_selected=selected_language)

    # Step 3: AI / Local Discourse & Claims Analysis
    ai_result = analyze_news_content(
        text=article_text,
        language_name=lang_name,
        custom_title=title,
        publisher=publisher,
        publish_date=publish_date,
    )

    # Step 4: Factual Claim Evidence Checking
    raw_claims = ai_result.get("factual_claims", [])
    verified_claims = verify_claims_evidence(raw_claims, lang=lang_code)

    # Step 5: Assemble Complete Analysis Payload
    analysis_id = str(uuid.uuid4())
    
    # Map techniques and presentation for backwards and forwards compatibility
    persuasive_techniques = ai_result.get("persuasive_techniques") or ai_result.get("rhetorical_techniques") or []
    presentation_analysis = ai_result.get("presentation_analysis") or ai_result.get("framing_indicators") or []
    possible_purpose = ai_result.get("possible_purpose") or {
        "suggested_purpose": "Informing the public or sharing commentary.",
        "supporting_evidence": "Extracted from source narrative.",
        "intent_disclaimer": "Possible effect: this content may shape reader perception. The creator's actual intention is unknown."
    }
    overall_verdict = ai_result.get("overall_verdict") or "Important claims remain unverified"
    accuracy_score_info = ai_result.get("accuracy_score_info") or {
        "score_available": False,
        "score_percentage": None,
        "formula_explanation": "Accuracy score unavailable: there is not enough independently verified evidence."
    }
    reader_next_steps = ai_result.get("reader_next_steps") or ai_result.get("recommended_verification_steps") or []

    payload = {
        "id": analysis_id,
        "title": ai_result.get("title") or title,
        "publisher": ai_result.get("publisher") or publisher,
        "publish_date": ai_result.get("publish_date") or publish_date,
        "source_type": source_type,
        "source_url": source_url,
        "source_preview": article_text[:300],
        "language": lang_name,
        "analysis_mode": ai_result.get("analysis_mode", "local_offline"),
        "summary": ai_result.get("summary", ""),
        "factual_claims": verified_claims,
        "claims": verified_claims,  # standard key
        "persuasive_techniques": persuasive_techniques,
        "rhetorical_techniques": persuasive_techniques,  # legacy key
        "presentation_analysis": presentation_analysis,
        "framing_indicators": presentation_analysis,  # legacy key
        "possible_purpose": possible_purpose,
        "overall_verdict": overall_verdict,
        "accuracy_score_info": accuracy_score_info,
        "missing_context": ai_result.get("missing_context", "No critical contextual omissions identified."),
        "limitations": ai_result.get("limitations", "Automated analysis cannot substitute for field journalistic investigation."),
        "reader_next_steps": reader_next_steps,
        "recommended_verification_steps": reader_next_steps,  # legacy key
        "status": "completed",
    }

    # Step 6: Atomic Database Persistence
    save_analysis(payload, db_path=db_path)

    return payload


# Backwards compatibility alias
analyze_content = analyze_story
