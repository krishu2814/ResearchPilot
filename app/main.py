import uuid
from datetime import datetime, timezone
from typing import List
from fastapi import FastAPI, Query, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.exceptions import RequestValidationError
from app.schemas import (
    ResearchRequest,
    ResearchResponse,
    SessionSummaryItem,
    SessionDetailResponse,
    DocumentUploadRequest,
    DocumentUploadResponse,
    DocumentListItem,
    DocumentSearchResponse,
    DocumentSearchResultItem,
    CacheStatsResponse,
    CircuitBreakerStatsResponse,
    ErrorResponse
)
from app.graph.research_graph import research_graph
from app.services.documents import save_document, get_all_documents
from app.services.rag import index_document_chunks, search_documents, get_index_stats
from app.services.session_store import (
    init_db,
    save_session,
    get_session,
    list_sessions,
    delete_session
)
from app.services.streaming import stream_research_progress
from app.services.cache import get_cache_stats, clear_cache
from app.services.resilience import search_circuit_breaker

# 1. Initialize SQLite session database
init_db()

# 2. Create FastAPI instance
app = FastAPI(
    title="ResearchPilot API",
    description="Agentic Research & RAG Platform - Phase 12 Error Handling & Fault Tolerance",
    version="0.12.0",
)


# -----------------------------------------------------------------------------
# Global Exception Handlers (Phase 12)
# -----------------------------------------------------------------------------
# In a robust system, errors should NEVER cause unhandled crashes or unformatted
# stack traces to leak to the client. These handlers intercept errors and wrap
# them in a clean, consistent ErrorResponse schema.
# -----------------------------------------------------------------------------
@app.exception_handler(HTTPException)
def http_exception_handler(request: Request, exc: HTTPException):
    """
    Standardizes HTTP exceptions (like 404 Not Found or 400 Bad Request).
    """
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error="HTTP Error",
            detail=str(exc.detail),
            status_code=exc.status_code,
            timestamp=datetime.now(timezone.utc).isoformat()
        ).model_dump()
    )


@app.exception_handler(RequestValidationError)
def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Standardizes schema validation errors (e.g. missing query in request body).
    """
    error_messages = []
    for err in exc.errors():
        field_path = " -> ".join(str(loc) for loc in err.get("loc", []))
        error_messages.append(f"{field_path}: {err.get('msg', 'Invalid value')}")
    formatted_detail = "; ".join(error_messages)

    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            error="Validation Error",
            detail=formatted_detail,
            status_code=422,
            timestamp=datetime.now(timezone.utc).isoformat()
        ).model_dump()
    )


@app.exception_handler(Exception)
def generic_exception_handler(request: Request, exc: Exception):
    """
    Safety net for unexpected internal errors (500 Internal Server Error).
    """
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal Server Error",
            detail=f"An unexpected internal error occurred: {str(exc)}",
            status_code=500,
            timestamp=datetime.now(timezone.utc).isoformat()
        ).model_dump()
    )


# -----------------------------------------------------------------------------
# System Endpoints
# -----------------------------------------------------------------------------
@app.get("/", tags=["System"])
def root():
    """
    Returns service metadata and helpful API links.
    """
    return {
        "service": "ResearchPilot",
        "description": "Agentic Research & RAG Platform",
        "version": "0.12.0",
        "docs_url": "/docs",
        "health_url": "/health"
    }


@app.get("/health", tags=["System"])
def health_check():
    """
    Returns the health status of the API server.
    """
    return {
        "status": "ok",
        "service": "ResearchPilot",
        "version": "0.12.0"
    }


# -----------------------------------------------------------------------------
# Research Endpoints (LangGraph Parallel Workflow with Streaming & Session Memory)
# -----------------------------------------------------------------------------
@app.get("/research/stream", tags=["Research"])
def stream_research(
    query: str = Query(..., description="The research question or topic", examples=["Compare PostgreSQL and MongoDB"]),
    session_id: str = Query(None, description="Optional custom session ID; auto-generated if omitted")
):
    """
    Streams multi-agent research progress in real-time via Server-Sent Events (SSE).
    Yields events for each agent node (planner, web_researcher, doc_retriever,
    extractor, fact_checker, synthesizer) and persists final results to SQLite.
    """
    clean_query = query.strip()
    if not clean_query:
        raise HTTPException(status_code=400, detail="Research query cannot be empty.")

    return StreamingResponse(
        stream_research_progress(query=clean_query, session_id=session_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@app.post("/research", response_model=ResearchResponse, tags=["Research"])
def start_research(request: ResearchRequest):
    """
    Receives a research query, runs the multi-agent graph:
    1. Planner generates sub-questions
    2. Web Researcher and Document Retriever execute in parallel
    3. Extractor distills sources into atomic claims with source citations
    4. Fact Checker audits claims against source material and assigns verdicts
    5. Synthesizer compiles verified findings into a structured Markdown report
    6. Session Store persists the complete state and report to SQLite database
    """
    clean_query = request.query.strip()
    if not clean_query:
        raise HTTPException(status_code=400, detail="Research query cannot be empty.")

    session_id = request.session_id or f"sess_{uuid.uuid4().hex[:8]}"

    initial_state = {
        "session_id": session_id,
        "question": clean_query,
        "sub_questions": [],
        "search_results": [],
        "document_results": [],
        "evidence": [],
        "verified_evidence": [],
        "report": "",
        "errors": []
    }

    final_state = research_graph.invoke(initial_state)

    # Persist the finished session and graph state to SQLite
    save_session(
        session_id=session_id,
        query=request.query,
        state=final_state,
        status="researched"
    )

    num_questions = len(final_state.get("sub_questions", []))
    web_count = len(final_state.get("search_results", []))
    doc_count = len(final_state.get("document_results", []))
    evidence_count = len(final_state.get("evidence", []))
    verified_list = final_state.get("verified_evidence", [])
    verified_count = sum(1 for v in verified_list if v.get("verdict") == "verified")
    report_length = len(final_state.get("report", ""))

    return ResearchResponse(
        session_id=session_id,
        status="researched",
        query=final_state.get("question", request.query),
        sub_questions=final_state.get("sub_questions", []),
        search_results=final_state.get("search_results", []),
        document_results=final_state.get("document_results", []),
        evidence=final_state.get("evidence", []),
        verified_evidence=final_state.get("verified_evidence", []),
        report=final_state.get("report", ""),
        errors=final_state.get("errors", []),
        message=(
            f"Planner generated {num_questions} sub-questions. "
            f"Gathered {web_count} web sources and {doc_count} document passages in parallel, "
            f"extracting {evidence_count} claims, verifying {verified_count} facts, "
            f"synthesizing a {report_length}-character report, and saving session '{session_id}' to database."
        )
    )


# -----------------------------------------------------------------------------
# Session & Persistence Endpoints (Phase 9)
# -----------------------------------------------------------------------------
@app.get("/sessions", response_model=List[SessionSummaryItem], tags=["Sessions & Persistence"])
def list_research_sessions(limit: int = Query(50, description="Max number of sessions to return", ge=1, le=100)):
    """
    Returns a list of all past research sessions stored in the SQLite database.
    """
    return list_sessions(limit=limit)


@app.get("/sessions/{session_id}", response_model=SessionDetailResponse, tags=["Sessions & Persistence"])
def get_research_session(session_id: str):
    """
    Retrieves the complete state and synthesized report for a specific research session.
    """
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Research session '{session_id}' not found.")
    return session


@app.delete("/sessions/{session_id}", tags=["Sessions & Persistence"])
def delete_research_session(session_id: str):
    """
    Permanently deletes a stored research session.
    """
    success = delete_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Research session '{session_id}' not found.")
    return {"status": "deleted", "session_id": session_id, "message": f"Session '{session_id}' successfully removed."}


# -----------------------------------------------------------------------------
# Document & RAG Endpoints (Phase 4)
# -----------------------------------------------------------------------------
@app.post("/documents", response_model=DocumentUploadResponse, tags=["Documents & RAG"])
def upload_document(request: DocumentUploadRequest):
    """
    Uploads a text document, splits it into overlapping chunks,
    computes vector embeddings, and stores them in the vector index.
    """
    clean_title = request.title.strip()
    clean_content = request.content.strip()
    if not clean_title:
        raise HTTPException(status_code=400, detail="Document title cannot be empty.")
    if not clean_content:
        raise HTTPException(status_code=400, detail="Document content cannot be empty.")

    # Step 1: Save document and split into chunks
    doc_record = save_document(title=clean_title, content=clean_content)

    # Step 2: Compute embeddings and index into the vector store
    indexed_chunks = index_document_chunks(
        doc_id=doc_record["doc_id"],
        title=doc_record["title"],
        chunks=doc_record["chunks"]
    )

    return DocumentUploadResponse(
        status="indexed",
        doc_id=doc_record["doc_id"],
        title=doc_record["title"],
        num_chunks=indexed_chunks,
        message=f"Document '{request.title}' successfully parsed into {indexed_chunks} chunks and vector indexed."
    )


@app.get("/documents", response_model=List[DocumentListItem], tags=["Documents & RAG"])
def list_documents():
    """
    Lists all documents currently indexed in memory.
    """
    return get_all_documents()


@app.get("/documents/search", response_model=DocumentSearchResponse, tags=["Documents & RAG"])
def search_vector_store(
    q: str = Query(..., description="Query to search document passages for"),
    top_k: int = Query(3, description="Maximum number of passages to return", ge=1, le=10)
):
    """
    Searches indexed document chunks using cosine similarity vector search.
    """
    clean_q = q.strip()
    if not clean_q:
        raise HTTPException(status_code=400, detail="Search query cannot be empty.")

    matches = search_documents(query=clean_q, top_k=top_k)

    return DocumentSearchResponse(
        query=q,
        total_matches=len(matches),
        results=[DocumentSearchResultItem(**item) for item in matches]
    )


@app.get("/documents/stats", tags=["Documents & RAG"])
def view_document_index_stats():
    """
    Returns statistics about the vector store index (total chunks, unique documents).
    """
    return get_index_stats()


# -----------------------------------------------------------------------------
# Caching Endpoints (Phase 11)
# -----------------------------------------------------------------------------
@app.get("/cache/stats", response_model=CacheStatsResponse, tags=["Caching"])
def view_cache_stats():
    """
    Returns performance metrics for the caching layer (hits, misses, active backend, and total keys).
    """
    return get_cache_stats()


@app.post("/cache/clear", tags=["Caching"])
def flush_cache():
    """
    Clears all cached web search queries and stored key-value pairs.
    """
    clear_cache()
    return {"status": "cleared", "message": "Cache successfully cleared."}


# -----------------------------------------------------------------------------
# Resilience & Fault Tolerance Endpoints (Phase 12)
# -----------------------------------------------------------------------------
@app.get("/resilience/circuit-breaker", response_model=CircuitBreakerStatsResponse, tags=["Resilience"])
def view_circuit_breaker_status():
    """
    Returns current health state, failure metrics, and cooldown timer of the search circuit breaker.
    """
    return search_circuit_breaker.get_status()


@app.post("/resilience/circuit-breaker/reset", tags=["Resilience"])
def reset_circuit_breaker():
    """
    Manually resets the circuit breaker back to CLOSED state.
    """
    search_circuit_breaker.reset()
    return {
        "status": "reset",
        "message": "Circuit breaker successfully reset to CLOSED state.",
        "circuit_breaker": search_circuit_breaker.get_status()
    }

