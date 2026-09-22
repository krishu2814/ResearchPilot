"""
Report Synthesizer Agent for ResearchPilot (Phase 8).

This agent compiles all verified findings, source citations, and fact-checking
audits into a clean, comprehensive, publication-ready research report formatted
in standard GitHub-flavored Markdown.
"""

import os
from typing import List, Dict
from app.graph.state import ResearchState


# -----------------------------------------------------------------------------
# Synthesizer Node
# -----------------------------------------------------------------------------
def synthesizer_node(state: ResearchState) -> dict:
    """
    Synthesizes the complete research graph state into a structured Markdown report.
    """
    question = state.get("question", "")
    sub_questions = state.get("sub_questions", [])
    search_results = state.get("search_results", [])
    document_results = state.get("document_results", [])
    verified_evidence = state.get("verified_evidence", [])

    print(f"\n[Synthesizer Node] Synthesizing final report for: '{question}'...")

    api_key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
    if api_key:
        try:
            report_md = _synthesize_with_llm(
                question=question,
                sub_questions=sub_questions,
                verified_evidence=verified_evidence,
                api_key=api_key
            )
            print(f"[Synthesizer Node] LLM generated report ({len(report_md)} chars).\n")
            return {"report": report_md}
        except Exception as err:
            print(f"[Synthesizer Node] LLM synthesis failed ({err}). Using built-in engine.")

    # Built-in structured Markdown synthesis engine (100% offline & deterministic)
    report_md = _synthesize_with_templates(
        question=question,
        sub_questions=sub_questions,
        search_results=search_results,
        document_results=document_results,
        verified_evidence=verified_evidence
    )

    print(f"[Synthesizer Node] Synthesized Markdown report ({len(report_md)} characters).\n")
    return {"report": report_md}


# -----------------------------------------------------------------------------
# Built-in Synthesis Engine (100% Offline & Deterministic)
# -----------------------------------------------------------------------------
def _synthesize_with_templates(
    question: str,
    sub_questions: List[str],
    search_results: List[Dict],
    document_results: List[Dict],
    verified_evidence: List[Dict]
) -> str:
    """
    Constructs a structured, human-readable Markdown report from verified evidence.
    """
    lines = []

    # 1. Document Title
    lines.append(f"# 📑 Research Report: {question}\n")
    lines.append("> *Generated autonomously by ResearchPilot Multi-Agent System.*\n")
    lines.append("---\n")

    # 2. Executive Summary
    lines.append("## 1. Executive Summary\n")
    verified_claims = [e for e in verified_evidence if e.get("verdict") == "verified"]
    total_sources = len(search_results) + len(document_results)

    if verified_claims:
        key_points = [f"- {c['claim']}" for c in verified_claims[:3]]
        points_text = "\n".join(key_points)
        lines.append(
            f"This automated research inquiry investigated **'{question}'**. "
            f"Across **{total_sources} consulted sources** (spanning live web searches and uploaded document repositories), "
            f"a total of **{len(verified_evidence)} factual assertions** were extracted and audited for truthfulness.\n\n"
            f"**Core Takeaways:**\n{points_text}\n"
        )
    else:
        lines.append(
            f"This research investigation gathered evidence across {total_sources} sources. "
            f"Preliminary claims have been compiled and categorized below for detailed review.\n"
        )

    lines.append("---\n")

    # 3. Detailed Findings by Sub-Question
    lines.append("## 2. Detailed Findings by Research Question\n")

    if not sub_questions:
        lines.append("*No sub-questions were defined for this research topic.*\n")
    else:
        for idx, sq in enumerate(sub_questions, 1):
            lines.append(f"### 2.{idx} {sq}\n")

            # Match claims that belong to this sub-question
            matching_claims = [
                e for e in verified_evidence
                if e.get("sub_question") == sq
            ]

            if not matching_claims:
                # If exact match wasn't tagged, show general evidence for the topic
                matching_claims = verified_evidence[
                    (idx - 1) * 2 : idx * 2
                ]

            if matching_claims:
                for c in matching_claims:
                    claim_text = c.get("claim", "")
                    src_title = c.get("source_title", "Source")
                    src_ref = c.get("source_url_or_id", "")
                    src_type = c.get("source_type", "web")
                    verdict = c.get("verdict", "verified").capitalize()
                    conf = int(c.get("confidence", 0.9) * 100)

                    # Format link based on type
                    if src_ref.startswith("http"):
                        link_md = f"[{src_title}]({src_ref})"
                    else:
                        link_md = f"*{src_title}* (`{src_ref}`)"

                    lines.append(f"- **{claim_text}**")
                    lines.append(f"  - *Source ({src_type})*: {link_md}")
                    lines.append(f"  - *Audit*: `{verdict}` ({conf}% confidence)\n")
            else:
                lines.append("*No specific verified evidence items were mapped to this question.*\n")

    lines.append("---\n")

    # 4. Fact-Checking & Evidence Audit Summary
    lines.append("## 3. Fact-Checking & Grounding Audit\n")
    total_claims = len(verified_evidence)
    verified_count = sum(1 for e in verified_evidence if e.get("verdict") == "verified")
    partial_count = sum(1 for e in verified_evidence if e.get("verdict") == "partial")
    unverified_count = sum(1 for e in verified_evidence if e.get("verdict") == "unverified")

    if total_claims > 0:
        avg_conf = sum(e.get("confidence", 0.0) for e in verified_evidence) / total_claims
        avg_conf_pct = int(avg_conf * 100)
    else:
        avg_conf_pct = 0

    lines.append("| Metric | Count / Score |")
    lines.append("| :--- | :--- |")
    lines.append(f"| **Total Claims Audited** | {total_claims} |")
    lines.append(f"| **Fully Verified Claims** | {verified_count} |")
    lines.append(f"| **Partially Grounded Claims** | {partial_count} |")
    lines.append(f"| **Unverified Claims** | {unverified_count} |")
    lines.append(f"| **Average Confidence Score** | {avg_conf_pct}% |")
    lines.append("")

    # 5. References and Consulted Sources
    lines.append("---\n")
    lines.append("## 4. Sources & Bibliography\n")

    seen_sources = set()
    ref_idx = 1

    # Web sources
    if search_results:
        lines.append("### Web Sources")
        for web in search_results:
            url = web.get("url", "")
            title = web.get("title", "Web Page")
            if url and url not in seen_sources:
                seen_sources.add(url)
                lines.append(f"{ref_idx}. [{title}]({url})")
                ref_idx += 1
        lines.append("")

    # Document sources
    if document_results:
        lines.append("### Internal Documents & RAG Passages")
        for doc in document_results:
            doc_id = doc.get("doc_id", "")
            title = doc.get("title", "Document")
            if doc_id and doc_id not in seen_sources:
                seen_sources.add(doc_id)
                lines.append(f"{ref_idx}. **{title}** (Document ID: `{doc_id}`)")
                ref_idx += 1
        lines.append("")

    return "\n".join(lines)


# -----------------------------------------------------------------------------
# Optional: LLM Report Synthesis
# -----------------------------------------------------------------------------
def _synthesize_with_llm(
    question: str,
    sub_questions: List[str],
    verified_evidence: List[Dict],
    api_key: str
) -> str:
    """
    Calls an LLM to craft a coherent, prose-driven Markdown research report.
    """
    import httpx

    sub_q_text = "\n".join([f"- {sq}" for sq in sub_questions])
    claims_text = "\n".join([
        f"- [{c.get('verdict')}] {c.get('claim')} (Source: {c.get('source_title')} - {c.get('source_url_or_id')})"
        for c in verified_evidence
    ])

    prompt = (
        f"You are a principal research synthesizer.\n"
        f"Write a thorough, polished Markdown research report answering: '{question}'\n\n"
        f"Research Questions Investigated:\n{sub_q_text}\n\n"
        f"Verified Evidence & Sources:\n{claims_text}\n\n"
        f"Format the report with:\n"
        f"1. Executive Summary\n"
        f"2. Analysis by Topic\n"
        f"3. Fact-Checking Summary\n"
        f"4. Sources and Citations with Markdown links.\n"
        f"Use clean Markdown with bolding and bullet points."
    )

    base_url = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
    model = os.getenv("LLM_MODEL", "gpt-4o-mini")

    response = httpx.post(
        f"{base_url}/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2
        },
        timeout=30.0
    )
    response.raise_for_status()
    report_content = response.json()["choices"][0]["message"]["content"].strip()
    return report_content
