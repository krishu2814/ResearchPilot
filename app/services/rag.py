"""
RAG (Retrieval-Augmented Generation) Vector Store Service for ResearchPilot (Phase 4).

This module manages the vector index of document chunks.
When a user asks a question, this service compares the question's vector
against all chunk vectors in the database and returns the top matching passages!
"""

from typing import List, Dict
from app.services.embeddings import get_embedding, cosine_similarity


# -----------------------------------------------------------------------------
# In-Memory Vector Store Index
# -----------------------------------------------------------------------------
# In later phases (Phase 14), this will be backed by PostgreSQL with pgvector.
# Starting with an in-memory list lets beginners learn the exact math and mechanics
# of vector search with zero database setup hurdles!
# -----------------------------------------------------------------------------
VECTOR_INDEX: List[Dict] = []


def index_document_chunks(doc_id: str, title: str, chunks: List[str]) -> int:
    """
    Computes vector embeddings for each chunk and adds them into the vector index.

    Returns:
        The number of chunks successfully indexed.
    """
    if not chunks:
        return 0

    indexed_count = 0
    for i, chunk_text in enumerate(chunks, 1):
        embedding = get_embedding(chunk_text)

        entry = {
            "chunk_id": f"{doc_id}_c{i}",
            "doc_id": doc_id,
            "title": title,
            "chunk_text": chunk_text,
            "embedding": embedding
        }
        VECTOR_INDEX.append(entry)
        indexed_count += 1

    print(f"[RAG Service] Indexed {indexed_count} chunks for '{title}' (Total indexed: {len(VECTOR_INDEX)})")
    return indexed_count


def search_documents(query: str, top_k: int = 3) -> List[Dict]:
    """
    Retrieves the top_k most relevant document passages for a query
    based on vector cosine similarity.

    Returns:
        List of matching passages sorted from highest to lowest similarity.
    """
    clean_query = query.strip()
    if not clean_query or not VECTOR_INDEX:
        return []

    # 1. Compute embedding vector for the search question
    query_vector = get_embedding(clean_query)

    # 2. Score every chunk in the index using cosine similarity
    scored_results = []
    for item in VECTOR_INDEX:
        score = cosine_similarity(query_vector, item["embedding"])

        # We only keep passages with positive relevance
        if score > 0.05:
            scored_results.append({
                "doc_id": item["doc_id"],
                "title": item["title"],
                "chunk_id": item["chunk_id"],
                "chunk_text": item["chunk_text"],
                "score": round(score, 4)
            })

    # 3. Sort by highest similarity score first
    scored_results.sort(key=lambda x: x["score"], reverse=True)

    # 4. Return top K matches
    return scored_results[:top_k]


def get_index_stats() -> dict:
    """
    Returns statistics about the current vector index.
    """
    return {
        "total_chunks_indexed": len(VECTOR_INDEX),
        "unique_documents": len({item["doc_id"] for item in VECTOR_INDEX})
    }
