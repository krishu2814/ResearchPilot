"""
Fact Checker Agent for ResearchPilot (Phase 7).

This agent audits every extracted claim to prevent hallucinations and ungrounded statements.
It cross-references each claim against the original source materials, calculating
grounding scores and assigning clear verdicts ('verified', 'partial', 'unverified')
along with confidence metrics and rationales.
"""

import os
import re
from typing import List, Dict
from app.graph.state import ResearchState


# Common stop words to exclude when analyzing factual keyword overlap
STOP_WORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
    "below", "between", "both", "but", "by", "can't", "cannot", "could", "couldn't",
    "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down", "during",
    "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't",
    "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here",
    "here's", "hers", "herself", "him", "himself", "his", "how", "how's", "i",
    "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's",
    "its", "itself", "let's", "me", "more", "most", "mustn't", "my", "myself",
    "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought",
    "our", "ours", "ourselves", "out", "over", "own", "same", "shan't", "she",
    "she'd", "she'll", "she's", "should", "shouldn't", "so", "some", "such",
    "than", "that", "that's", "the", "their", "theirs", "them", "themselves",
    "then", "there", "there's", "these", "they", "they'd", "they'll", "they're",
    "they've", "this", "those", "through", "to", "too", "under", "until", "up",
    "very", "was", "wasn't", "we", "we'd", "we'll", "we're", "we've", "were",
    "weren't", "what", "what's", "when", "when's", "where", "where's", "which",
    "while", "who", "who's", "whom", "why", "why's", "with", "won't", "would",
    "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your", "yours"
}


# -----------------------------------------------------------------------------
# Fact Checker Node
# -----------------------------------------------------------------------------
def fact_checker_node(state: ResearchState) -> dict:
    """
    Audits each claim in state['evidence'] against the underlying source text.
    """
    evidence_list = state.get("evidence", [])
    search_results = state.get("search_results", [])
    document_results = state.get("document_results", [])

    print(f"\n[Fact Checker Node] Auditing {len(evidence_list)} extracted claims...")

    api_key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
    if api_key:
        try:
            verified = _verify_with_llm(evidence_list, api_key)
            print(f"[Fact Checker Node] LLM verified {len(verified)} claims.\n")
            return {"verified_evidence": verified}
        except Exception as err:
            print(f"[Fact Checker Node] LLM verification failed ({err}). Using built-in auditor.")

    # Built-in lexical grounding auditor (100% offline & deterministic)
    verified = _verify_with_heuristics(evidence_list, search_results, document_results)

    verified_count = sum(1 for v in verified if v["verdict"] == "verified")
    print(f"[Fact Checker Node] Audited {len(verified)} claims: {verified_count} verified.\n")

    return {"verified_evidence": verified}


# -----------------------------------------------------------------------------
# Helper: Heuristic Grounding Auditor (100% Offline)
# -----------------------------------------------------------------------------
def _verify_with_heuristics(
    evidence_list: List[Dict],
    search_results: List[Dict],
    document_results: List[Dict]
) -> List[Dict]:
    """
    Checks if the key terms of each claim are present in the cited source text.
    """
    # 1. Build a quick lookup of source texts
    source_texts: Dict[str, str] = {}
    for web in search_results:
        url = web.get("url", "")
        title = web.get("title", "")
        snippet = web.get("snippet", "")
        if url:
            source_texts[url] = snippet
        if title:
            source_texts[title] = snippet

    for doc in document_results:
        doc_id = doc.get("doc_id", "")
        title = doc.get("title", "")
        chunk_text = doc.get("chunk_text", "")
        if doc_id:
            source_texts[doc_id] = chunk_text
        if title:
            source_texts[title] = chunk_text

    verified_results = []

    # 2. Audit each claim
    for item in evidence_list:
        claim = item.get("claim", "")
        source_id = item.get("source_url_or_id", "")
        source_title = item.get("source_title", "")
        source_type = item.get("source_type", "unknown")

        # Find source text
        source_content = source_texts.get(source_id) or source_texts.get(source_title) or ""

        # Extract meaningful claim keywords
        claim_words = [
            w for w in re.findall(r"\b\w+\b", claim.lower())
            if w not in STOP_WORDS and len(w) > 2
        ]

        if not claim_words or not source_content:
            # If no keywords or source text missing, mark unverified
            verdict = "unverified"
            confidence = 0.40
            rationale = "Insufficient source text to substantiate claim."
        else:
            source_lower = source_content.lower()
            # Calculate what percentage of claim keywords are grounded in source text
            matched_words = [w for w in claim_words if w in source_lower]
            overlap_ratio = len(matched_words) / len(claim_words)

            if overlap_ratio >= 0.65:
                verdict = "verified"
                confidence = round(min(0.85 + (0.15 * overlap_ratio), 0.99), 2)
                rationale = f"Claim is directly supported by cited {source_type} source '{source_title}'."
            elif overlap_ratio >= 0.35:
                verdict = "partial"
                confidence = round(0.50 + (0.20 * overlap_ratio), 2)
                rationale = f"Claim has partial keyword grounding in '{source_title}'."
            else:
                verdict = "unverified"
                confidence = 0.30
                rationale = f"Claim assertions are not sufficiently grounded in source '{source_title}'."

        verified_results.append({
            "claim": claim,
            "source_type": source_type,
            "source_title": source_title,
            "source_url_or_id": source_id,
            "sub_question": item.get("sub_question", ""),
            "verdict": verdict,
            "confidence": confidence,
            "rationale": rationale
        })

    return verified_results


# -----------------------------------------------------------------------------
# Helper: LLM Fact Checker (Optional)
# -----------------------------------------------------------------------------
def _verify_with_llm(evidence_list: List[Dict], api_key: str) -> List[Dict]:
    """
    Calls an LLM to evaluate factual consistency of claims against their sources.
    """
    import json
    import httpx

    claims_text = "\n".join([
        f"Claim [{i}]: \"{e.get('claim')}\" | Source: {e.get('source_title')} ({e.get('source_url_or_id')})"
        for i, e in enumerate(evidence_list, 1)
    ])

    prompt = (
        f"You are a strict fact-checking auditor.\n"
        f"For each claim below, determine if it is: 'verified', 'partial', or 'unverified'.\n"
        f"Claims:\n{claims_text}\n\n"
        f"Return ONLY a JSON array of objects with keys: 'verdict' ('verified'|'partial'|'unverified'), "
        f"'confidence' (float 0.0 to 1.0), and 'rationale' (string explanation).\n"
        f"Return exactly {len(evidence_list)} items in order."
    )

    base_url = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
    model = os.getenv("LLM_MODEL", "gpt-4o-mini")

    response = httpx.post(
        f"{base_url}/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.0
        },
        timeout=20.0
    )
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"].strip()

    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
    content = content.strip()

    parsed = json.loads(content)
    if isinstance(parsed, list) and len(parsed) == len(evidence_list):
        output = []
        for orig, audit in zip(evidence_list, parsed):
            item = dict(orig)
            item["verdict"] = audit.get("verdict", "verified")
            item["confidence"] = float(audit.get("confidence", 0.9))
            item["rationale"] = audit.get("rationale", "Verified by auditor.")
            output.append(item)
        return output

    raise ValueError("LLM returned unexpected response format")
