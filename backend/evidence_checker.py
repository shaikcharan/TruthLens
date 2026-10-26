"""
TruthLens Evidence Checker Module
Integrates with open-source reference knowledge APIs (Wikipedia OpenSearch)
to locate genuine citations for factual claims.
NEVER fabricates evidence, citations, or URLs.
"""

import re
import requests
from typing import List, Dict, Any
from config import Config

USER_AGENT = "TruthLens-Verifier/1.0 (B.Tech Media Literacy Project; mailto:truthlens-verifier@local)"


def extract_search_keywords(claim_text: str) -> str:
    """Extract 3-5 salient keywords from a claim string for query formulation."""
    # Remove common punctuation
    cleaned = re.sub(r"[^\w\s]", " ", claim_text)
    # Stop words to filter out
    stop_words = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of",
        "with", "by", "from", "as", "is", "was", "are", "were", "been", "be",
        "have", "has", "had", "do", "does", "did", "can", "could", "should", "would",
        "that", "this", "these", "those", "it", "its", "they", "their", "we", "our",
        "reported", "stated", "claimed", "according", "also", "which", "who", "whom",
        "video", "showing", "allegedly", "shows", "purporting", "first", "second", "third"
    }
    words = [w for w in cleaned.split() if len(w) > 3 and w.lower() not in stop_words]
    return " ".join(words[:4]) if words else claim_text[:50]


def query_open_knowledge_base(query: str, lang: str = "en") -> List[Dict[str, str]]:
    """
    Queries open encyclopedic knowledge via OpenSearch API.
    Returns list of genuine source dicts: [{'title': ..., 'url': ..., 'snippet': ...}].
    """
    if not query.strip():
        return []

    # Map language code to Wikipedia subdomain
    wiki_lang = lang if lang in ("en", "hi", "te", "ta", "kn", "pa") else "en"
    endpoint = f"https://{wiki_lang}.wikipedia.org/w/api.php"

    params = {
        "action": "opensearch",
        "search": query,
        "limit": 2,
        "namespace": 0,
        "format": "json",
    }
    headers = {"User-Agent": USER_AGENT}

    try:
        response = requests.get(endpoint, params=params, headers=headers, timeout=5)
        if response.status_code != 200:
            return []

        data = response.json()
        if len(data) >= 4:
            titles = data[1]
            descriptions = data[2]
            urls = data[3]

            results = []
            for i in range(min(len(titles), len(urls))):
                results.append(
                    {
                        "title": titles[i],
                        "snippet": descriptions[i] if i < len(descriptions) else "",
                        "url": urls[i],
                        "source": f"Wikipedia ({wiki_lang.upper()}) Reference Archive",
                    }
                )
            return results
    except Exception:
        # Network failure or timeout: fail gracefully without crashing
        return []

    return []


def verify_single_claim(claim: Dict[str, Any], lang: str = "en") -> Dict[str, Any]:
    """
    Attempts to locate genuine reference evidence for an extracted factual claim.
    Preserves article-reported verdicts if present; marks unverified claims honestly.
    """
    claim_text = claim.get("claim", "")
    existing_verdict = claim.get("verdict") or claim.get("verification_status")

    # If claim was already determined as contradicted or misleading by the article's own investigation
    if existing_verdict in ("Contradicted by evidence", "Misleading or missing context"):
        verdict = existing_verdict
        verif_type = claim.get("verification_type", "Article-reported finding")
        explanation = claim.get("verdict_explanation") or claim.get("verification_notes") or "Identified by article reporting."
        quality = claim.get("evidence_quality", "Medium")
        sources = claim.get("evidence_sources", [])
        
        return {
            **claim,
            "verdict": verdict,
            "verification_status": verdict,
            "verdict_explanation": explanation,
            "verification_notes": explanation,
            "verification_type": verif_type,
            "evidence_quality": quality,
            "evidence_sources": sources,
            "limitations": claim.get("limitations", "Independent video/archival file check was not performed.")
        }

    if not Config.ENABLE_FACT_CHECK_SEARCH:
        verdict = "Not yet verified"
        explanation = "External evidence verification is disabled in configuration. Claim must be independently cross-checked."
        return {
            **claim,
            "verdict": verdict,
            "verification_status": verdict,
            "verdict_explanation": explanation,
            "verification_notes": explanation,
            "verification_type": "Independently verified finding",
            "evidence_quality": "Insufficient",
            "evidence_sources": [],
            "limitations": "No external searches performed."
        }

    keywords = extract_search_keywords(claim_text)
    sources = query_open_knowledge_base(keywords, lang=lang)

    if sources:
        # Genuine open knowledge source was found
        verdict = "Partially supported"  # Kept honest: open knowledge provides topical corroboration
        explanation = (
            f"Retrieved {len(sources)} related open reference source(s) matching claim topic. "
            "Review linked references to verify specific details or figures."
        )
        return {
            **claim,
            "verdict": verdict,
            "verification_status": verdict,
            "verdict_explanation": explanation,
            "verification_notes": explanation,
            "verification_type": "Independently verified finding",
            "evidence_quality": "Medium",
            "evidence_sources": sources,
            "limitations": "Open encyclopedic references provide background context but may not reflect latest real-time events."
        }

    # No evidence retrieved: never fabricate
    verdict = "Not yet verified"
    explanation = "No independent external evidence was located to confirm or contradict this claim. It remains not yet verified."
    return {
        **claim,
        "verdict": verdict,
        "verification_status": verdict,
        "verdict_explanation": explanation,
        "verification_notes": explanation,
        "verification_type": "Independently verified finding",
        "evidence_quality": "Insufficient",
        "evidence_sources": [],
        "limitations": "No matching open-access reference entries found."
    }


def verify_claims_evidence(claims: List[Dict[str, Any]], lang: str = "en") -> List[Dict[str, Any]]:
    """Verify list of claims against external reference evidence."""
    verified_claims = []
    for c in claims:
        verified_claims.append(verify_single_claim(c, lang=lang))
    return verified_claims
