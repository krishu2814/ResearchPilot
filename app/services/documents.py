"""
Document Ingestion and Chunking Service for ResearchPilot (Phase 4).

RAG (Retrieval-Augmented Generation) requires breaking large documents into
smaller, focused text chunks so an AI can find and read the most relevant
passages without overloading context windows.
"""

from typing import List, Dict
import uuid


# Simple in-memory document store:
# Maps doc_id -> { "doc_id": ..., "title": ..., "content": ..., "chunks": [...] }
DOCUMENTS_STORE: Dict[str, dict] = {}


def chunk_text(text: str, chunk_size: int = 300, overlap: int = 50) -> List[str]:
    """
    Splits a body of text into smaller overlapping chunks.

    Args:
        text: The raw document text to split.
        chunk_size: Target maximum length (in characters) of each chunk.
        overlap: How many characters to repeat from the previous chunk
                 so sentences/ideas don't get cut in half abruptly.

    Returns:
        A list of text chunk strings.

    Beginner Concept:
    If chunk_size = 100 and overlap = 20:
    - Chunk 1: characters 0 to 100
    - Chunk 2: characters 80 to 180 (starts 20 chars before chunk 1 ends!)
    - Chunk 3: characters 160 to 260
    """
    cleaned_text = text.strip()
    if not cleaned_text:
        return []

    # If the text is already smaller than the chunk size, return it as a single chunk
    if len(cleaned_text) <= chunk_size:
        return [cleaned_text]

    chunks: List[str] = []
    start = 0
    text_len = len(cleaned_text)

    # Slide a window across the text
    step = chunk_size - overlap
    if step <= 0:
        step = chunk_size  # safety fallback in case overlap >= chunk_size

    while start < text_len:
        end = start + chunk_size
        chunk = cleaned_text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        # Move the window forward by step (which leaves 'overlap' characters behind)
        start += step

    return chunks


def save_document(title: str, content: str, chunk_size: int = 300, overlap: int = 50) -> dict:
    """
    Chunks a document and saves it into the in-memory documents store.

    Returns:
        The stored document dictionary with its generated doc_id and chunks.
    """
    doc_id = f"doc_{uuid.uuid4().hex[:8]}"
    chunks = chunk_text(content, chunk_size=chunk_size, overlap=overlap)

    doc_record = {
        "doc_id": doc_id,
        "title": title.strip() or "Untitled Document",
        "content": content.strip(),
        "chunks": chunks
    }

    DOCUMENTS_STORE[doc_id] = doc_record
    print(f"[Documents Service] Stored document '{title}' (ID: {doc_id}) with {len(chunks)} chunks.")

    return doc_record


def get_all_documents() -> List[dict]:
    """
    Returns metadata for all documents currently saved in memory.
    """
    return [
        {
            "doc_id": doc["doc_id"],
            "title": doc["title"],
            "num_chunks": len(doc["chunks"]),
            "char_count": len(doc["content"])
        }
        for doc in DOCUMENTS_STORE.values()
    ]
