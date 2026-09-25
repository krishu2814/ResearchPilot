"""
Streaming Service for ResearchPilot (Phase 10).

This module implements Server-Sent Events (SSE) streaming for the multi-agent
research graph. It allows web frontends and CLI tools to receive real-time,
step-by-step progress events as each agent runs in the pipeline.

SSE is a simple, standard web protocol over HTTP:
Each update is sent as plain text in the format:
    event: <event_name>\n
    data: <json_string>\n\n
"""

import json
import uuid
from typing import Optional, Generator
from app.graph.research_graph import research_graph
from app.services.session_store import save_session


# -----------------------------------------------------------------------------
# Helper: Format SSE Message
# -----------------------------------------------------------------------------
def format_sse(event: str, data: dict) -> str:
    """
    Formats a dictionary into a compliant Server-Sent Event (SSE) text frame.
    """
    payload = json.dumps({"event": event, **data})
    return f"event: {event}\ndata: {payload}\n\n"


# -----------------------------------------------------------------------------
# Generator: Stream Research Progress
# -----------------------------------------------------------------------------
def stream_research_progress(
    query: str,
    session_id: Optional[str] = None
) -> Generator[str, None, None]:
    """
    Executes the multi-agent graph in streaming mode, yielding SSE event frames
    as each agent node starts, progresses, and completes.
    """
    # 1. Resolve session ID
    active_session_id = session_id or f"sess_{uuid.uuid4().hex[:8]}"

    # 2. Yield initial 'started' event
    yield format_sse("started", {
        "session_id": active_session_id,
        "query": query,
        "message": f"Research started for: '{query}'"
    })

    # 3. Prepare initial state
    accumulated_state = {
        "session_id": active_session_id,
        "question": query,
        "sub_questions": [],
        "search_results": [],
        "document_results": [],
        "evidence": [],
        "verified_evidence": [],
        "report": "",
        "errors": []
    }

    try:
        # 4. Stream graph node execution using LangGraph's native stream()
        # 'stream_mode="updates"' yields {node_name: node_output} as each node finishes
        for update in research_graph.stream(accumulated_state, stream_mode="updates"):
            for node_name, node_output in update.items():
                # Merge the node's returned values into our accumulated state
                accumulated_state.update(node_output)

                # Format human-friendly step summary based on which agent just ran
                if node_name == "planner":
                    sub_qs = node_output.get("sub_questions", [])
                    yield format_sse("step", {
                        "session_id": active_session_id,
                        "node": "planner",
                        "status": "completed",
                        "message": f"Planner produced {len(sub_qs)} sub-questions.",
                        "details": {"sub_questions": sub_qs}
                    })

                elif node_name == "web_researcher":
                    sources = node_output.get("search_results", [])
                    yield format_sse("step", {
                        "session_id": active_session_id,
                        "node": "web_researcher",
                        "status": "completed",
                        "message": f"Web Researcher gathered {len(sources)} online sources.",
                        "details": {"source_count": len(sources)}
                    })

                elif node_name == "doc_retriever":
                    passages = node_output.get("document_results", [])
                    yield format_sse("step", {
                        "session_id": active_session_id,
                        "node": "doc_retriever",
                        "status": "completed",
                        "message": f"Document Retriever matched {len(passages)} passages from RAG store.",
                        "details": {"passage_count": len(passages)}
                    })

                elif node_name == "extractor":
                    claims = node_output.get("evidence", [])
                    yield format_sse("step", {
                        "session_id": active_session_id,
                        "node": "extractor",
                        "status": "completed",
                        "message": f"Extractor distilled {len(claims)} atomic claims with citations.",
                        "details": {"claim_count": len(claims)}
                    })

                elif node_name == "fact_checker":
                    verified = node_output.get("verified_evidence", [])
                    num_verified = sum(1 for v in verified if v.get("verdict") == "verified")
                    yield format_sse("step", {
                        "session_id": active_session_id,
                        "node": "fact_checker",
                        "status": "completed",
                        "message": f"Fact Checker audited {len(verified)} claims ({num_verified} verified).",
                        "details": {"verified_count": num_verified, "total_claims": len(verified)}
                    })

                elif node_name == "synthesizer":
                    report_text = node_output.get("report", "")
                    yield format_sse("step", {
                        "session_id": active_session_id,
                        "node": "synthesizer",
                        "status": "completed",
                        "message": f"Synthesizer generated final Markdown report ({len(report_text)} chars).",
                        "details": {"report_length": len(report_text)}
                    })

        # 5. Persist the completed session to SQLite database
        save_session(
            session_id=active_session_id,
            query=query,
            state=accumulated_state,
            status="researched"
        )

        # 6. Yield final 'complete' event with the full report and summary
        yield format_sse("complete", {
            "session_id": active_session_id,
            "status": "completed",
            "query": query,
            "report": accumulated_state.get("report", ""),
            "sub_questions": accumulated_state.get("sub_questions", []),
            "num_sources": len(accumulated_state.get("search_results", [])) + len(accumulated_state.get("document_results", [])),
            "num_verified_claims": len(accumulated_state.get("verified_evidence", [])),
            "message": "Research pipeline completed successfully."
        })

    except Exception as error:
        print(f"[Streaming Service] Error during graph execution: {error}")
        yield format_sse("error", {
            "session_id": active_session_id,
            "message": f"An error occurred during research: {str(error)}"
        })
