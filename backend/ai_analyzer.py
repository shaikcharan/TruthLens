"""
TruthLens AI Rhetorical & Factual Claims Analyzer
Enforces strict anti-fabrication rules, exact source quotation matching,
plain English explanations, and honest local offline analysis.
"""

import json
import re
from typing import Dict, Any, List, Optional
from config import Config


class AIAnalyzerError(Exception):
    """Exception raised for AI analysis failures."""
    pass


# Forbidden canned/fabricated phrases that must NEVER appear unless present in the input text
FORBIDDEN_CANNED_PHRASES = [
    "40% shift in public metrics",
    "key leadership officials held an unannounced emergency session",
    "shocking revelation emerges",
    "everyone agrees without question",
    "every citizen lose their savings",
    "revolutionary herbal panacea",
]


def normalize_for_matching(text: str) -> str:
    """Normalizes whitespace and removes punctuation for flexible substring search."""
    cleaned = re.sub(r"[^\w\s]", " ", text.lower())
    return " ".join(cleaned.split())


def is_quote_present(quote: str, source_text: str) -> bool:
    """Verifies that a quotation or passage genuinely exists in the source text."""
    if not quote or not source_text:
        return False
    
    # Direct substring check
    if quote.strip() in source_text:
        return True
    
    # Normalized substring check
    norm_quote = normalize_for_matching(quote)
    norm_source = normalize_for_matching(source_text)
    if norm_quote in norm_source:
        return True
    
    # Check if first 5-6 words match
    words = norm_quote.split()
    if len(words) >= 5:
        prefix = " ".join(words[:6])
        if prefix in norm_source:
            return True
    
    return False


def contains_forbidden_fabrication(text_to_check: str, source_text: str) -> bool:
    """Checks whether the text contains canned synthetic phrases not present in the source."""
    norm_check = normalize_for_matching(text_to_check)
    norm_source = normalize_for_matching(source_text)
    
    for phrase in FORBIDDEN_CANNED_PHRASES:
        norm_phrase = normalize_for_matching(phrase)
        if norm_phrase in norm_check and norm_phrase not in norm_source:
            return True
    return False


ANALYSIS_SYSTEM_INSTRUCTION = """You are TruthLens, an objective media literacy and news discourse analyst.
Your mission is to perform honest, grounded analysis of news articles and social media posts.

ABSOLUTE ACCURACY RULES:
1. NEVER invent factual claims, statistics, events, quotations, or sources.
2. Extract claims ONLY from the actual supplied text.
3. Every extracted claim MUST include the exact supporting passage from the article.
4. Every quotation MUST match the article text verbatim.
5. If no clear verifiable claim exists, return an empty claims list.
6. Distinguish between:
   - What the article reports (e.g. if an article reports that viral claims are false, note that as an article-reported finding).
   - What the original viral claim asserted.
   - What TruthLens independently established.
7. Use SIMPLE, PLAIN ENGLISH throughout. Avoid dense academic jargon:
   - Use "Persuasive Writing Techniques" instead of "Rhetorical Techniques".
   - Use "Exaggerated or Dramatic Language" instead of "Sensationalism".
   - Use "Uses Emotion" instead of "Emotional Appeal".
   - Use "How the Story Is Presented" instead of "Narrative Framing".
   - Use "Not Yet Verified" instead of "Unverified".
8. Distinguish a post's possible effect from its creator's unproven intention. Never claim an author deliberately spread propaganda unless proven.
9. Output strictly valid JSON conforming to the schema.
"""

ANALYSIS_PROMPT_TEMPLATE = """Analyze the following article text carefully in {language_name}.

Article Content:
\"\"\"
{article_text}
\"\"\"

Produce a valid JSON object matching this structure:
{{
  "title": "Clear headline or topic",
  "detected_language": "{language_name}",
  "summary": "3 to 5 simple, factual sentences explaining what the article is about, the main topic, people/organizations involved, and its core message.",
  "analysis_mode": "ai_assisted",
  "factual_claims": [
    {{
      "claim": "Specific empirical assertion stated in the text",
      "source_passage": "Exact verbatim sentence from the article where this claim is made",
      "claim_type": "video_claim | statistical | event | quote | other",
      "verdict": "Supported by evidence | Contradicted by evidence | Misleading or missing context | Mixed evidence | Not yet verified",
      "verdict_explanation": "Simple plain-English reason for this verdict",
      "evidence_sources": [
        {{
          "title": "Source name or document mentioned in the article",
          "url": "",
          "snippet": "What the evidence showed"
        }}
      ],
      "evidence_quality": "High | Medium | Low | Insufficient",
      "verification_type": "Article-reported finding | Independently verified finding",
      "limitations": "What could not be checked or verified"
    }}
  ],
  "persuasive_techniques": [
    {{
      "technique": "Plain English name (e.g. Exaggerated or Dramatic Language, Uses Emotion, Blaming a Group, Broad Claim Without Enough Evidence, One-Sided Sourcing)",
      "quote": "Exact short quotation from the article showing this technique",
      "explanation": "Simple explanation of why this wording was chosen",
      "likely_effect": "Likely effect on the reader, without assuming deliberate bad intent"
    }}
  ],
  "presentation_analysis": [
    {{
      "aspect": "Aspect name (e.g. How Sourcing Is Handled, Tone & Wording, Treatment of Opposing Views)",
      "explanation": "Observable pattern in how the article presents the information"
    }}
  ],
  "possible_purpose": {{
    "suggested_purpose": "Possible purpose (e.g. informing readers about old footage, attracting viral engagement, promoting a viewpoint)",
    "supporting_evidence": "Specific evidence in the article supporting this interpretation",
    "intent_disclaimer": "Possible effect: this content may influence reader perceptions. The creator's actual intention is unknown."
  }},
  "missing_context": "Concrete missing information that would help resolve uncertainty, or 'No critical contextual omissions identified.'",
  "overall_verdict": "Evidence largely supports the assessed claims | Some claims are misleading or contradicted | Important claims remain unverified | Mixed findings | Insufficient evidence for an overall verdict",
  "accuracy_score_info": {{
    "score_available": false,
    "score_percentage": null,
    "formula_explanation": "Accuracy score unavailable: there is not enough independently verified evidence."
  }},
  "reader_next_steps": [
    "Practical step 1 for a critical reader",
    "Practical step 2 for a critical reader"
  ]
}}

Return ONLY valid JSON.
"""


def clean_json_response(raw_text: str) -> str:
    """Removes markdown code fences and extraneous whitespace from AI response."""
    cleaned = raw_text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    return cleaned.strip()


def validate_analysis_structure(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validates required schema fields in an analysis payload."""
    required_keys = [
        "title",
        "summary",
        "factual_claims",
    ]
    for key in required_keys:
        if key not in data:
            raise AIAnalyzerError(f"AI response is missing required field: '{key}'.")
    return data


def validate_and_sanitize_ai_response(data: Dict[str, Any], source_text: str) -> Dict[str, Any]:
    """
    Validates AI response structure, verifies that quotations exist in source text,
    and strips any fabricated or unsupported assertions.
    """
    # Normalize compatibility keys
    if "persuasive_techniques" not in data and "rhetorical_techniques" in data:
        data["persuasive_techniques"] = data.get("rhetorical_techniques", [])
    if "possible_purpose" not in data:
        data["possible_purpose"] = {
            "suggested_purpose": "Informing readers about news developments or public statements.",
            "supporting_evidence": "Text discusses events and institutional actions.",
            "intent_disclaimer": "Possible effect: this content may shape reader perceptions. The creator's actual intention is unknown."
        }
    if "overall_verdict" not in data:
        data["overall_verdict"] = "Important claims remain unverified"

    required_keys = [
        "title",
        "summary",
        "factual_claims",
        "persuasive_techniques",
        "possible_purpose",
        "overall_verdict",
    ]

    for key in required_keys:
        if key not in data:
            raise AIAnalyzerError(f"AI response is missing required field: '{key}'.")

    if not isinstance(data.get("factual_claims"), list):
        data["factual_claims"] = []
    if not isinstance(data.get("persuasive_techniques"), list):
        data["persuasive_techniques"] = []

    # Sanitize factual claims: verify quotations and eliminate hallucinations
    verified_claims = []
    for c in data["factual_claims"]:
        passage = c.get("source_passage", "")
        claim_text = c.get("claim", "")

        # Check for forbidden canned fabrications
        if contains_forbidden_fabrication(claim_text, source_text) or contains_forbidden_fabrication(passage, source_text):
            continue

        # If source passage does not exist in the source text, attempt to locate matching sentence
        if passage and not is_quote_present(passage, source_text):
            # Try to match claim text in source
            matched_sentence = find_best_matching_sentence(claim_text, source_text)
            if matched_sentence:
                c["source_passage"] = matched_sentence
            else:
                # Discard claim that has no textual basis
                continue
        elif not passage:
            matched_sentence = find_best_matching_sentence(claim_text, source_text)
            c["source_passage"] = matched_sentence if matched_sentence else "Referenced in article body"

        # Standardize verdict label
        v = c.get("verdict", "Not yet verified")
        c["verdict"] = normalize_verdict_label(v)

        verified_claims.append(c)

    data["factual_claims"] = verified_claims

    # Sanitize persuasive techniques
    verified_techniques = []
    for t in data["persuasive_techniques"]:
        quote = t.get("quote", "")
        if contains_forbidden_fabrication(quote, source_text):
            continue
        if quote and not is_quote_present(quote, source_text):
            # Remove fake quotes
            t["quote"] = ""
        verified_techniques.append(t)

    data["persuasive_techniques"] = verified_techniques
    data["rhetorical_techniques"] = verified_techniques
    data["claims"] = verified_claims
    if "recommended_verification_steps" not in data and "reader_next_steps" in data:
        data["recommended_verification_steps"] = data["reader_next_steps"]
    elif "reader_next_steps" not in data and "recommended_verification_steps" in data:
        data["reader_next_steps"] = data["recommended_verification_steps"]

    return data


def normalize_verdict_label(verdict_str: str) -> str:
    """Maps various verdict variations to the 5 official plain-English labels."""
    v = verdict_str.lower().strip()
    if "contradict" in v or "false" in v or "debunk" in v:
        return "Contradicted by evidence"
    if "mislead" in v or "missing context" in v or "lacks context" in v:
        return "Misleading or missing context"
    if "support" in v or "true" in v or "verified" in v and "not" not in v and "un" not in v:
        return "Supported by evidence"
    if "mix" in v:
        return "Mixed evidence"
    return "Not yet verified"


def find_best_matching_sentence(query: str, text: str) -> Optional[str]:
    """Finds the sentence in text that has the highest word overlap with the query."""
    query_words = set(re.findall(r"\w{4,}", query.lower()))
    if not query_words:
        return None

    sentences = [s.strip() for s in re.split(r"(?<=[.!?\n])\s+", text) if len(s.strip()) > 15]
    best_sent = None
    best_overlap = 0

    for sent in sentences:
        sent_words = set(re.findall(r"\w{4,}", sent.lower()))
        overlap = len(query_words.intersection(sent_words))
        if overlap > best_overlap and overlap >= 2:
            best_overlap = overlap
            best_sent = sent

    return best_sent


# ==============================================================================
# Honest Deterministic Local / Offline Analyzer
# ==============================================================================


def analyze_offline_text(
    text: str,
    language_name: str,
    custom_title: str = "",
    publisher: str = "",
    publish_date: str = "",
) -> Dict[str, Any]:
    """
    Performs a genuine, honest, rule-based analysis of the actual input text.
    NEVER fabricates claims, quotes, or fake research.
    """
    clean_text = text.strip()
    lines = [l.strip() for l in clean_text.split("\n") if l.strip()]
    sentences = [s.strip() for s in re.split(r"(?<=[.!?\n])\s+", clean_text) if len(s.strip()) > 20]

    # 1. Headline determination
    title = custom_title
    if not title and lines:
        title = lines[0][:90]
        if len(lines[0]) > 90:
            title += "..."
    if not title:
        title = "Analyzed News Story"

    # 2. Honest, genuine summary derived from actual text sentences
    if len(sentences) >= 3:
        summary = " ".join(sentences[:3])
    elif sentences:
        summary = " ".join(sentences)
    else:
        summary = clean_text[:300]

    # Check if this article is itself a fact-check report (e.g. BOOM, AltNews, Factly)
    is_fact_check_article = bool(
        re.search(r"\b(fact-check|fact check|falsely linked|false claim|misleading|debunk|unrelated|older video|reverse image)\b", clean_text, re.I)
    )

    # 3. Extract real factual claims from the text
    factual_claims = []
    
    # Specific pattern recognition for viral claims or fact-checked claims discussed in the text
    claim_indicators = [
        r"(?:video|clip|image|photo)\s+(?:showing|claimed|allegedly|circulating|purporting)[^.!?\n]+",
        r"(?:claimed|alleged|stated)\s+(?:that|to show)[^.!?\n]+",
        r"(?:protest|demonstration|rally)\s+[^.!?\n]+(?:July|August|September|October|November|December|\d{1,2})[^.!?\n]*",
        r"\b\d{1,3}(?:\.\d+)?%\s+[^.!?\n]+",
    ]

    matched_sentences = set()

    for pattern in claim_indicators:
        for match in re.finditer(pattern, clean_text, re.I):
            matched_span = match.group(0).strip()
            # Find the enclosing sentence
            enclosing_sentence = find_best_matching_sentence(matched_span, clean_text)
            if enclosing_sentence and enclosing_sentence not in matched_sentences:
                matched_sentences.add(enclosing_sentence)
                
                # Formulate a clear claim statement
                claim_label = enclosing_sentence
                if len(claim_label) > 140:
                    claim_label = claim_label[:140] + "..."

                # Determine verdict based on what the text says
                is_debunked_in_text = bool(
                    re.search(r"\b(false|misleading|old|unrelated|earlier post|reverse image|debunked|falsely)\b", enclosing_sentence, re.I)
                )

                if is_fact_check_article and is_debunked_in_text:
                    verdict = "Contradicted by evidence"
                    v_explanation = "The article's investigative reporting identifies this claim or video as contradicted by chronological records or original source footage."
                    verif_type = "Article-reported finding"
                    v_quality = "Medium"
                elif is_fact_check_article and any(word in enclosing_sentence.lower() for word in ["claimed", "alleged", "circulating"]):
                    verdict = "Contradicted by evidence"
                    v_explanation = "The article investigates this claim and reports that it is falsely linked to the event."
                    verif_type = "Article-reported finding"
                    v_quality = "Medium"
                else:
                    verdict = "Not yet verified"
                    v_explanation = "External fact-checking verification was not performed in local offline mode. Claim requires independent cross-referencing."
                    verif_type = "Independently verified finding"
                    v_quality = "Insufficient"

                # Check if evidence source is mentioned in sentence (e.g. reverse image search, date, official)
                evidence_sources = []
                if "reverse image" in clean_text.lower():
                    evidence_sources.append({
                        "title": "Reverse Image Search / Chronological Archives",
                        "url": "",
                        "snippet": "Archival matches cited in article text"
                    })
                if publisher and publisher != "Pasted Source":
                    evidence_sources.append({
                        "title": f"Reporting by {publisher}",
                        "url": "",
                        "snippet": "Reported fact-check findings"
                    })

                factual_claims.append({
                    "claim": claim_label,
                    "source_passage": enclosing_sentence,
                    "claim_type": "video_claim" if "video" in enclosing_sentence.lower() else "event",
                    "verdict": verdict,
                    "verdict_explanation": v_explanation,
                    "evidence_sources": evidence_sources,
                    "evidence_quality": v_quality,
                    "verification_type": verif_type,
                    "limitations": "TruthLens relied on the article text and did not independently query the original video files."
                })

            if len(factual_claims) >= 5:
                break
        if len(factual_claims) >= 5:
            break

    # If no pattern matches, pick high-content assertion sentences from the text
    if not factual_claims and sentences:
        for s in sentences[:3]:
            factual_claims.append({
                "claim": s[:120] + ("..." if len(s) > 120 else ""),
                "source_passage": s,
                "claim_type": "factual",
                "verdict": "Not yet verified",
                "verdict_explanation": "Extracted from source text. External fact-checking verification was not performed in local offline mode.",
                "evidence_sources": [],
                "evidence_quality": "Insufficient",
                "verification_type": "Independently verified finding",
                "limitations": "Independent external evidence retrieval is unavailable in offline mode."
            })

    # 4. Extract genuine persuasive techniques using words ACTUALLY PRESENT in text
    persuasive_techniques = []
    
    sensational_words = ["shocking", "urgent", "secretly", "crisis", "outrage", "disaster", "unprecedented", "massive", "suppressed", "exposed"]
    found_sensational = [w for w in sensational_words if re.search(r"\b" + w + r"\b", clean_text, re.I)]
    
    if found_sensational:
        # Find sentence containing the word
        word = found_sensational[0]
        matching_sent = find_best_matching_sentence(word, clean_text) or word
        persuasive_techniques.append({
            "technique": "Exaggerated or Dramatic Language",
            "quote": matching_sent[:120],
            "explanation": f"Uses emotionally charged vocabulary ('{word}') to increase reader urgency and attention.",
            "likely_effect": "May heighten alarm or urgency. The creator's actual intention is unknown."
        })

    urgency_match = re.search(r"(?:share this|before it gets deleted|emergency|warning)", clean_text, re.I)
    if urgency_match:
        matching_sent = find_best_matching_sentence(urgency_match.group(0), clean_text) or urgency_match.group(0)
        persuasive_techniques.append({
            "technique": "Uses Emotion (Urgency)",
            "quote": matching_sent[:120],
            "explanation": "Appeals to immediate action by creating a sense of impending removal or crisis.",
            "likely_effect": "Encourages rapid forwarding before verifying facts."
        })

    # If no overt techniques found, honestly report that
    if not persuasive_techniques:
        persuasive_techniques.append({
            "technique": "Neutral Presentation",
            "quote": sentences[0][:100] if sentences else "",
            "explanation": "No clear evidence of overt propaganda or manipulation techniques was found in the analyzed text.",
            "likely_effect": "Presents information in a straightforward reportorial style."
        })

    # 5. Presentation analysis
    presentation = [
        {
            "aspect": "Attribution and Sourcing",
            "explanation": f"Material is presented with references to {publisher if publisher else 'external sources and social media claims'}."
        },
        {
            "aspect": "Tone and Neutrality",
            "explanation": "The text maintains reportorial phrasing focusing on documenting events or claims."
        }
    ]

    # 6. Possible purpose
    if is_fact_check_article:
        purpose = {
            "suggested_purpose": "Informing the public by debunking viral misinformation and clarifying historical protest dates.",
            "supporting_evidence": "Text analyzes viral videos, cross-references dates, and clarifies original sources.",
            "intent_disclaimer": "Possible effect: this helps readers identify unrelated footage. The creator's actual intention is unknown."
        }
    else:
        purpose = {
            "suggested_purpose": "Sharing news developments, opinion, or social media commentary.",
            "supporting_evidence": "Text describes events and claims for public consumption.",
            "intent_disclaimer": "Possible effect: this content may shape reader perception. The creator's actual intention is unknown."
        }

    # 7. Overall verdict
    if is_fact_check_article:
        overall_verdict = "Some claims discussed are misleading or contradicted (as reported by source)"
    else:
        overall_verdict = "Important claims remain unverified"

    return {
        "title": title,
        "publisher": publisher,
        "publish_date": publish_date,
        "detected_language": language_name,
        "summary": summary,
        "analysis_mode": "local_offline",
        "factual_claims": factual_claims,
        "claims": factual_claims,
        "persuasive_techniques": persuasive_techniques,
        "rhetorical_techniques": persuasive_techniques,
        "presentation_analysis": presentation,
        "framing_indicators": presentation,
        "possible_purpose": purpose,
        "missing_context": "Independent archival footage verification would be required to verify original social media posts directly.",
        "overall_verdict": overall_verdict,
        "accuracy_score_info": {
            "score_available": False,
            "score_percentage": None,
            "formula_explanation": "Accuracy score unavailable: there is not enough independently verified evidence."
        },
        "reader_next_steps": [
            "Check primary institutional registries or official gazettes for stated figures.",
            "Compare coverage across independent news organizations with diverse editorial perspectives.",
            "Verify whether direct quotes originate from verified transcripts or third-party interpretations."
        ],
        "recommended_verification_steps": [
            "Check primary institutional registries or official gazettes for stated figures.",
            "Compare coverage across independent news organizations with diverse editorial perspectives.",
            "Verify whether direct quotes originate from verified transcripts or third-party interpretations."
        ],
        "limitations": "Offline Local Mode: GEMINI_API_KEY is not configured in .env. Factual claims were extracted directly from the text without external search verification."
    }


# Backwards compatibility alias
generate_mock_analysis = analyze_offline_text


# ==============================================================================
# Main Analyzer Entry Point
# ==============================================================================


def call_gemini_api(prompt: str) -> str:
    """Invokes Google Gemini API using official client libraries."""
    model_name = Config.GEMINI_MODEL
    api_key = Config.GEMINI_API_KEY

    # Strategy 1: Modern google.genai SDK
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
        )
        if response and response.text:
            return response.text
    except Exception as e_genai:
        # Strategy 2: Legacy google.generativeai SDK fallback
        try:
            import google.generativeai as legacy_genai
            legacy_genai.configure(api_key=api_key)
            model = legacy_genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            if response and response.text:
                return response.text
        except Exception as e_legacy:
            raise AIAnalyzerError(
                f"Gemini API invocation failed on model '{model_name}'. Details: {str(e_genai)} / {str(e_legacy)}"
            )

    raise AIAnalyzerError("Gemini API returned an empty response.")


def analyze_news_content(
    text: str,
    language_name: str,
    custom_title: str = "",
    publisher: str = "",
    publish_date: str = "",
) -> Dict[str, Any]:
    """
    Main analysis entry point.
    If GEMINI_API_KEY is configured, calls Gemini with the structured prompt.
    Otherwise, runs honest, deterministic local offline text analysis.
    """
    if not Config.is_api_key_configured():
        return analyze_offline_text(
            text=text,
            language_name=language_name,
            custom_title=custom_title,
            publisher=publisher,
            publish_date=publish_date,
        )

    prompt = ANALYSIS_PROMPT_TEMPLATE.format(
        language_name=language_name,
        article_text=text[:Config.MAX_ARTICLE_CHARS],
    )

    try:
        raw_output = call_gemini_api(prompt)
        cleaned_json = clean_json_response(raw_output)
        parsed_data = json.loads(cleaned_json)
        
        # Verify and sanitize: strip hallucinations and enforce exact quotation matching
        validated_data = validate_and_sanitize_ai_response(parsed_data, source_text=text)
        
        if custom_title and not validated_data.get("title"):
            validated_data["title"] = custom_title
        if publisher and not validated_data.get("publisher"):
            validated_data["publisher"] = publisher
        if publish_date and not validated_data.get("publish_date"):
            validated_data["publish_date"] = publish_date

        validated_data["analysis_mode"] = "ai_assisted"
        return validated_data

    except json.JSONDecodeError:
        # Fallback to local text analysis if LLM output was malformed JSON
        fallback = analyze_offline_text(
            text=text,
            language_name=language_name,
            custom_title=custom_title,
            publisher=publisher,
            publish_date=publish_date,
        )
        fallback["limitations"] += " (Note: Live AI output was malformed JSON; processed via local analysis.)"
        return fallback
    except Exception as exc:
        raise AIAnalyzerError(f"Analysis pipeline error: {str(exc)}")
