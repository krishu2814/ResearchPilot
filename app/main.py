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
    description="Agentic Research & RAG Platform - Phase 4 Document RAG & Vector Storage",
    version="0.4.0",
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
        "version": "0.4.0"
    }


# -----------------------------------------------------------------------------
# Research Endpoints (LangGraph Workflow)
# -----------------------------------------------------------------------------
@app.post("/research", response_model=ResearchResponse, tags=["Research"])
def start_research(request: ResearchRequest):
    """
    Receives a research query from the user, passes it to the LangGraph
    multi-agent workflow (START -> Planner -> Researcher -> END), and returns results.
    """
    initial_state = {
        "question": request.query,
        "sub_questions": [],
        "search_results": []
    }

    final_state = research_graph.invoke(initial_state)

    num_questions = len(final_state.get("sub_questions", []))
    num_results = len(final_state.get("search_results", []))

    return ResearchResponse(
        status="researched",
        query=final_state["question"],
        sub_questions=final_state["sub_questions"],
        search_results=final_state["search_results"],
        message=f"Planner generated {num_questions} sub-questions, and Researcher gathered {num_results} web sources."
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
