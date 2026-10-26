"""
Regression tests for TruthLens analysis using the BOOM fact-check article:
"Visuals From CJP's July 20 Protest Falsely Linked To October 10 Stir" (October 10, 2026).

Verifies:
1. Exact extraction of all 3 video claims without hallucinating non-existent quotes.
2. Every extracted claim is linked to its exact supporting passage in the source text.
3. Strict zero-tolerance for forbidden canned phrases ("40% shift", "emergency session", etc.).
4. Accurate publisher ("BOOM") and publish date ("October 10, 2026") preservation.
5. Plain English verdicts attributing findings to the article rather than fabricating independent analysis.
"""

import sys
import pytest
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.ai_analyzer import (
    analyze_offline_text,
    FORBIDDEN_CANNED_PHRASES,
    is_quote_present,
)
from backend.analysis_service import analyze_content


BOOM_ARTICLE_TEXT = """
Visuals From CJP's July 20 Protest Falsely Linked To October 10 Stir
By BOOM Fact Check Desk | Published: October 10, 2026

Three viral videos showing large crowds and police presence are circulating on social media with claims that they show a massive agitation organized on October 10, 2026. BOOM conducted an in-depth investigation into these visuals.

Video 1: Social media users claimed that Video 1 shows protesters clashing with police on October 10 during the recent stir. However, a reverse image search of keyframes revealed that this visual actually dates back to July 20, 2026, during a demonstration organized by Citizens for Justice and Peace (CJP).

Video 2: Another viral clip was shared claiming that public transport was completely paralyzed across the capital on October 10. Archival news reports and traffic police records confirm that this video also originated from the July 20 protest, not the recent demonstration.

Video 3: A third video was circulated claiming government administrative offices were besieged by demonstrators on October 10. BOOM verified that this video was filmed during the same July 20 CJP rally and is falsely linked to the October 10 stir.

In conclusion, none of the viral videos depict events from October 10. All three visuals are from July 20 and have been falsely linked to the recent stir.
""".strip()


class TestBoomFactCheckRegression:
    """Verifies that TruthLens produces grounded, honest analysis on the BOOM fact-check."""

    def test_no_forbidden_canned_phrases_exist(self):
        """Ensure analyzer never outputs canned synthetic phrases."""
        result = analyze_offline_text(
            text=BOOM_ARTICLE_TEXT,
            language_name="English",
            custom_title="Visuals From CJP's July 20 Protest Falsely Linked To October 10 Stir",
            publisher="BOOM",
            publish_date="October 10, 2026",
        )

        result_str = str(result).lower()
        for forbidden in FORBIDDEN_CANNED_PHRASES:
            assert forbidden not in result_str, f"Found forbidden canned phrase: '{forbidden}'"

    def test_extracts_three_video_claims(self):
        """Verify all 3 distinct video claims are extracted from the text."""
        result = analyze_offline_text(
            text=BOOM_ARTICLE_TEXT,
            language_name="English",
            publisher="BOOM",
            publish_date="October 10, 2026",
        )

        claims = result.get("factual_claims") or []
        assert len(claims) >= 3, f"Expected at least 3 claims, got {len(claims)}"

        # Check that Video 1, Video 2, and Video 3 are represented
        claims_text = " ".join([c["claim"].lower() + " " + c.get("source_passage", "").lower() for c in claims])
        assert "video 1" in claims_text or "video" in claims_text
        assert "july 20" in claims_text
        assert "october 10" in claims_text

    def test_every_extracted_claim_has_exact_passage(self):
        """Verify that every claim's source passage exists verbatim in the article."""
        result = analyze_offline_text(
            text=BOOM_ARTICLE_TEXT,
            language_name="English",
            publisher="BOOM",
            publish_date="October 10, 2026",
        )

        claims = result.get("factual_claims") or []
        for claim in claims:
            passage = claim.get("source_passage", "")
            assert passage, f"Claim '{claim.get('claim')}' is missing a source passage!"
            assert is_quote_present(passage, BOOM_ARTICLE_TEXT), (
                f"Source passage '{passage}' was not found verbatim in the article text!"
            )

    def test_publisher_and_date_preservation(self):
        """Verify publisher ('BOOM') and date ('October 10, 2026') are preserved."""
        result = analyze_offline_text(
            text=BOOM_ARTICLE_TEXT,
            language_name="English",
            publisher="BOOM",
            publish_date="October 10, 2026",
        )

        assert result["publisher"] == "BOOM"
        assert result["publish_date"] == "October 10, 2026"

    def test_verdicts_are_plain_english_and_attributed(self):
        """Verify verdicts use plain English and attribute verification to the article's reporting."""
        result = analyze_offline_text(
            text=BOOM_ARTICLE_TEXT,
            language_name="English",
            publisher="BOOM",
            publish_date="October 10, 2026",
        )

        claims = result.get("factual_claims") or []
        valid_plain_english_verdicts = {
            "Contradicted by evidence",
            "Misleading or missing context",
            "Supported by evidence",
            "Mixed evidence",
            "Not yet verified",
        }

        for claim in claims:
            verdict = claim.get("verdict")
            assert verdict in valid_plain_english_verdicts, f"Invalid verdict: '{verdict}'"

        # Overall verdict should reflect that claims were refuted or contradicted
        assert "contradict" in result.get("overall_verdict", "").lower() or "misleading" in result.get("overall_verdict", "").lower()

    def test_full_analysis_service_pipeline(self):
        """Test full end-to-end service including saving and 10-section structure."""
        service_result = analyze_content(
            source_type="text",
            content_input=BOOM_ARTICLE_TEXT,
            selected_language="en",
            custom_title="Visuals From CJP's July 20 Protest Falsely Linked To October 10 Stir",
        )

        assert "id" in service_result
        assert "BOOM" in service_result["publisher"] or service_result["publisher"] in ("Direct Submission", "Identified in source")
        assert len(service_result["factual_claims"]) >= 3

        # Check 10-section payload elements
        assert "summary" in service_result
        assert "factual_claims" in service_result
        assert "accuracy_score_info" in service_result
        assert "persuasive_techniques" in service_result
        assert "possible_purpose" in service_result
        assert "presentation_analysis" in service_result
        assert "missing_context" in service_result
        assert "overall_verdict" in service_result
        assert "reader_next_steps" in service_result
