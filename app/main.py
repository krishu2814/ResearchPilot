from typing import List
from fastapi import FastAPI, Query
from app.schemas import (
    ResearchRequest,
    ResearchResponse,
    DocumentUploadRequest,
    DocumentUploadResponse,
    DocumentListItem,
    DocumentSearchResponse,
    DocumentSearchResultItem
)
from app.graph.research_graph import research_graph
from app.services.documents import save_document, get_all_documents
from app.services.rag import index_document_chunks, search_documents, get_index_stats

# 1. Create FastAPI instance
app = FastAPI(
    title="ResearchPilot API",
    description="Agentic Research & RAG Platform - Phase 7 Fact Checking Pipeline",
    version="0.7.0",
)


# -----------------------------------------------------------------------------
# System Endpoints
# -----------------------------------------------------------------------------
@app.get("/health", tags=["System"])
def health_check():
    """
    Returns the health status of the API server.
    """
    return {
        "status": "ok",
        "service": "ResearchPilot",
        "version": "0.7.0"
    }


# -----------------------------------------------------------------------------
# Research Endpoints (LangGraph Parallel Fact-Checking Workflow)
# -----------------------------------------------------------------------------
@app.post("/research", response_model=ResearchResponse, tags=["Research"])
def start_research(request: ResearchRequest):
    """
    Receives a research query, runs the multi-agent graph:
    1. Planner generates sub-questions
    2. Web Researcher and Document Retriever execute in parallel
    3. Extractor distills sources into atomic claims with source citations
    4. Fact Checker audits claims against source material and assigns verdicts
    """
    initial_state = {
        "question": request.query,
        "sub_questions": [],
        "search_results": [],
        "document_results": [],
        "evidence": [],
        "verified_evidence": []
    }

    final_state = research_graph.invoke(initial_state)

    num_questions = len(final_state.get("sub_questions", []))
    web_count = len(final_state.get("search_results", []))
    doc_count = len(final_state.get("document_results", []))
    evidence_count = len(final_state.get("evidence", []))
    verified_list = final_state.get("verified_evidence", [])
    verified_count = sum(1 for v in verified_list if v.get("verdict") == "verified")

    return ResearchResponse(
        status="researched",
        query=final_state["question"],
        sub_questions=final_state["sub_questions"],
        search_results=final_state["search_results"],
        document_results=final_state["document_results"],
        evidence=final_state["evidence"],
        verified_evidence=final_state["verified_evidence"],
        message=(
            f"Planner generated {num_questions} sub-questions. "
            f"Gathered {web_count} web sources and {doc_count} document passages in parallel, "
            f"extracting {evidence_count} claims and fact-verifying {verified_count} supported statements."
        )
    )


# -----------------------------------------------------------------------------
# Document & RAG Endpoints (Phase 4)
# -----------------------------------------------------------------------------
@app.post("/documents", response_model=DocumentUploadResponse, tags=["Documents & RAG"])
def upload_document(request: DocumentUploadRequest):
    """
    Uploads a text document, splits it into overlapping chunks,
    computes vector embeddings, and stores them in the vector index.
    """
    # Step 1: Save document and split into chunks
    doc_record = save_document(title=request.title, content=request.content)

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
    matches = search_documents(query=q, top_k=top_k)

    return DocumentSearchResponse(
        query=q,
        total_matches=len(matches),
        results=[DocumentSearchResultItem(**item) for item in matches]
    )
