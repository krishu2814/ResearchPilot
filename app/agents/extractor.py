"""
Evidence Extractor Agent for ResearchPilot (Phase 6).

This agent processes raw text from both web search results and uploaded documents.
It filters out boilerplate/noise and extracts atomic, concrete claims with direct
source attribution (citations) so that the Fact Checker (Phase 7) and Report
Synthesizer (Phase 8) can work with clean, verifiable statements.
"""

import os
import re
from typing import List, Dict
from app.graph.state import ResearchState


# -----------------------------------------------------------------------------
# Extractor Node
# -----------------------------------------------------------------------------
def extractor_node(state: ResearchState) -> dict:
    """
    Reads raw web and document results from state, extracts core informational
    claims, and formats them into structured evidence with citations.
    """
    search_results = state.get("search_results", [])
    document_results = state.get("document_results", [])
    total_sources = len(search_results) + len(document_results)

    print(f"\n[Extractor Node] Extracting structured evidence from {total_sources} sources...")

    api_key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
    if api_key:
        try:
            evidence = _extract_with_llm(state, api_key)
            print(f"[Extractor Node] LLM extracted {len(evidence)} evidence statements.\n")
            return {"evidence": evidence}
        except Exception as err:
            print(f"[Extractor Node] LLM extraction failed ({err}). Using built-in extractor.")

    # Built-in intelligent rule-based sentence extractor (works 100% offline!)
    evidence = _extract_with_heuristics(search_results, document_results)
    print(f"[Extractor Node] Distilled {total_sources} sources into {len(evidence)} structured evidence items.\n")

    return {"evidence": evidence}


# -----------------------------------------------------------------------------
# Helper: Heuristic Evidence Extractor (100% Offline & Deterministic)
# -----------------------------------------------------------------------------
def _extract_with_heuristics(search_results: List[Dict], document_results: List[Dict]) -> List[Dict]:
    """
    Extracts informative sentences from web snippets and document passages,
    tagging each claim with its exact source metadata.
    """
    evidence_items = []

    # 1. Extract from Web Search Results
    for item in search_results:
        raw_snippet = item.get("snippet", "")
        sentences = _split_into_meaningful_sentences(raw_snippet)

        for sent in sentences[:2]:  # Top 1-2 salient claims per web source
            evidence_items.append({
                "claim": sent,
                "source_type": "web",
                "source_title": item.get("title", "Web Source"),
                "source_url_or_id": item.get("url", ""),
                "sub_question": item.get("sub_question", "")
            })

    # 2. Extract from Uploaded Document Results
    for item in document_results:
        raw_text = item.get("chunk_text", "")
        sentences = _split_into_meaningful_sentences(raw_text)

        for sent in sentences[:2]:  # Top 1-2 salient claims per document passage
            evidence_items.append({
                "claim": sent,
                "source_type": "document",
                "source_title": item.get("title", "Uploaded Document"),
                "source_url_or_id": item.get("doc_id", ""),
                "sub_question": item.get("sub_question", "")
            })

    return evidence_items


def _split_into_meaningful_sentences(text: str) -> List[str]:
    """
    Splits text by punctuation (. ! ?) and filters out noisy or truncated snippets.
    """
    if not text:
        return []

    # Split on sentence boundaries
    raw_sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    clean_sentences = []

    for s in raw_sentences:
        clean = s.strip()
        # Remove trailing ellipsis or partial words
        clean = re.sub(r"\.{2,}$", "", clean).strip()

        # Keep sentences that have substance (at least 5 words and > 25 characters)
        words = clean.split()
        if len(words) >= 5 and len(clean) >= 25:
            # Ensure it ends with a period for clean presentation
            if not clean.endswith((".", "!", "?")):
                clean += "."
            clean_sentences.append(clean)

    # Fallback: if strict criteria matched nothing but text is meaningful, retain stripped text
    if not clean_sentences and text.strip():
        fallback_clean = text.strip()
        if len(fallback_clean.split()) >= 3:
            if not fallback_clean.endswith((".", "!", "?")):
                fallback_clean += "."
            clean_sentences.append(fallback_clean)

    return clean_sentences


# -----------------------------------------------------------------------------
# Helper: LLM-Powered Extractor (Optional)
# -----------------------------------------------------------------------------
def _extract_with_llm(state: ResearchState, api_key: str) -> List[Dict]:
    """
    Calls an LLM to distill raw sources into a structured JSON list of claims.
    """
    import json
    import httpx

    sources_summary = []
    for s in state.get("search_results", []):
        sources_summary.append(f"[WEB: {s.get('title')}] ({s.get('url')}): {s.get('snippet')}")
    for d in state.get("document_results", []):
        sources_summary.append(f"[DOC: {d.get('title')}] (ID: {d.get('doc_id')}): {d.get('chunk_text')}")

    combined_text = "\n\n".join(sources_summary[:8])  # Keep prompt compact

    prompt = (
        f"You are a research evidence extractor.\n"
        f"Task: Extract 3 to 6 key factual claims from the research materials below.\n"
        f"Materials:\n{combined_text}\n\n"
        f"Return ONLY a JSON array of objects with keys: 'claim', 'source_type' ('web' or 'document'), "
        f"'source_title', 'source_url_or_id', 'sub_question'.\n"
        f"Example: [{{\"claim\": \"...\", \"source_type\": \"web\", \"source_title\": \"...\", \"source_url_or_id\": \"...\", \"sub_question\": \"...\"}}]"
    )

    base_url = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
    model = os.getenv("LLM_MODEL", "gpt-4o-mini")

    response = httpx.post(
        f"{base_url}/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1
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
    if isinstance(parsed, list):
        return parsed
    return _extract_with_heuristics(state.get("search_results", []), state.get("document_results", []))
