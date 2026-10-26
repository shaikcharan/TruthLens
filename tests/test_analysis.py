"""
Unit tests for AI rhetorical analysis, prompt construction, and evidence checking.
"""

import pytest
import sys
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.ai_analyzer import (
    analyze_news_content,
    generate_mock_analysis,
    clean_json_response,
    validate_analysis_structure,
    AIAnalyzerError,
)
from backend.evidence_checker import (
    extract_search_keywords,
    verify_claims_evidence,
    verify_single_claim,
)
from config import Config


class TestAIAnalysis:
    """Tests AI rhetorical extraction and mock fallback."""

    def test_clean_json_markdown_fences(self):
        fenced = "```json\n{\"title\": \"Sample\", \"summary\": \"Clean text\"}\n```"
        cleaned = clean_json_response(fenced)
        assert cleaned == "{\"title\": \"Sample\", \"summary\": \"Clean text\"}"

    def test_mock_analysis_structure_english(self):
        text = "This is a detailed article outlining potential fiscal policy changes and new tax rates."
        result = generate_mock_analysis(text, "English", "Test Headline")

        assert result["title"] == "Test Headline"
        assert result["detected_language"] == "English"
        assert len(result["factual_claims"]) > 0
        assert len(result["rhetorical_techniques"]) > 0
        assert "recommended_verification_steps" in result

    def test_mock_analysis_structure_hindi(self):
        text = "नई गाइडलाइंस के अनुसार स्वास्थ्य सुविधाओं में बदलाव की योजना बनाई गई है।"
        result = generate_mock_analysis(text, "Hindi")
        assert result["detected_language"] == "Hindi"
        assert len(result["factual_claims"]) > 0

    def test_mock_analysis_structure_telugu(self):
        text = "రాష్ట్ర ప్రభుత్వం విడుదల చేసిన నివేదిక ప్రకారం పారిశ్రామిక వృద్ధి కొనసాగుతోంది."
        result = generate_mock_analysis(text, "Telugu")
        assert result["detected_language"] == "Telugu"
        assert len(result["factual_claims"]) > 0

    def test_mock_analysis_structure_tamil(self):
        text = "தமிழக அரசின் புதிய அறிவிப்பின்படி நலத்திட்டங்கள் விரிவுபடுத்தப்பட்டுள்ளன."
        result = generate_mock_analysis(text, "Tamil")
        assert result["detected_language"] == "Tamil"
        assert len(result["factual_claims"]) > 0

    def test_mock_analysis_structure_kannada(self):
        text = "ಕರ್ನಾಟಕ ಸರ್ಕಾರದ ವರದಿಯ ಪ್ರಕಾರ ಕೃಷಿ ವಲಯದಲ್ಲಿ ಪ್ರಗತಿ ಸಾಧಿಸಲಾಗಿದೆ."
        result = generate_mock_analysis(text, "Kannada")
        assert result["detected_language"] == "Kannada"
        assert len(result["factual_claims"]) > 0

    def test_validate_analysis_structure_missing_key(self):
        incomplete_data = {"title": "Sample", "summary": "Short"}
        with pytest.raises(AIAnalyzerError, match="missing required field"):
            validate_analysis_structure(incomplete_data)

    @patch("config.Config.is_api_key_configured", return_value=True)
    @patch("backend.ai_analyzer.call_gemini_api")
    def test_live_ai_flow_with_mocked_gemini(self, mock_call, mock_key):
        valid_json = {
            "title": "Mocked Gemini Title",
            "detected_language": "English",
            "summary": "This is a neutral AI summary.",
            "factual_claims": [
                {
                    "claim": "The council voted 7-2 in favor of the measure.",
                    "claim_type": "event",
                    "verification_notes": "Check council voting records.",
                    "requires_external_verification": True,
                }
            ],
            "rhetorical_techniques": [
                {
                    "technique": "Sensationalism",
                    "explanation": "Dramatizes municipal proceedings.",
                    "quote": "Historic unprecedented decision",
                }
            ],
            "framing_indicators": [
                {
                    "indicator": "Conflict Framing",
                    "explanation": "Focuses on division among council members.",
                }
            ],
            "missing_context": "Omitted previous unanimous committee resolutions.",
            "limitations": "Automated text model cannot verify physical council audio.",
            "recommended_verification_steps": ["Review official council minutes."],
        }
        mock_call.return_value = json.dumps(valid_json)

        result = analyze_news_content("Sample body text with sufficient length for testing.", "English")
        assert result["title"] == "Mocked Gemini Title"
        assert len(result["factual_claims"]) == 1
        assert result["factual_claims"][0]["claim_type"] == "event"


class TestEvidenceChecker:
    """Tests factual claim verification without fabricated links."""

    def test_extract_search_keywords(self):
        claim = "The Ministry of Health announced a 40% reduction in clinic wait times."
        keywords = extract_search_keywords(claim)
        assert "Ministry" in keywords
        assert "Health" in keywords
        # Stop words like "in", "a", "of" should be filtered out
        assert "the" not in keywords.lower().split()

    def test_unverified_fallback_when_no_evidence(self):
        claim = {
            "claim": "Alien spacecraft secretly landed in central park yesterday at noon.",
            "claim_type": "event",
        }
        with patch("backend.evidence_checker.query_open_knowledge_base", return_value=[]):
            verified = verify_single_claim(claim)
            assert verified["verification_status"] in ("Not yet verified", "Unverified")
            assert len(verified["evidence_sources"]) == 0
            assert "not yet verified" in verified["verification_notes"].lower() or "external" in verified["verification_notes"].lower()

    def test_genuine_evidence_attachment(self):
        claim = {
            "claim": "Python was created by Guido van Rossum and released in 1991.",
            "claim_type": "event",
        }
        mock_sources = [
            {
                "title": "Python (programming language)",
                "snippet": "Python is a high-level general-purpose programming language.",
                "url": "https://en.wikipedia.org/wiki/Python_(programming_language)",
                "source": "Wikipedia Reference",
            }
        ]
        with patch("backend.evidence_checker.query_open_knowledge_base", return_value=mock_sources):
            verified = verify_single_claim(claim)
            assert verified["verification_status"] == "Partially supported"
            assert len(verified["evidence_sources"]) == 1
            assert verified["evidence_sources"][0]["url"] == "https://en.wikipedia.org/wiki/Python_(programming_language)"
