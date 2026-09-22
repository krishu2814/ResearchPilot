from pydantic import BaseModel, Field
from typing import List


# -----------------------------------------------------------------------------
# Web & Document Item Models
# -----------------------------------------------------------------------------
class SearchResultItem(BaseModel):
    """
    Represents an individual search source gathered by the Web Researcher agent.
    """
    sub_question: str = Field(..., description="The sub-question this source helps answer")
    title: str = Field(..., description="Title of the webpage")
    url: str = Field(..., description="Direct link to the source")
    snippet: str = Field(..., description="Text summary/preview from the source")


class DocumentSearchResultItem(BaseModel):
    """
    A single document chunk matched via vector search.
    """
    sub_question: str = Field(default="", description="The sub-question this passage relates to")
    doc_id: str = Field(..., description="Document identifier")
    title: str = Field(..., description="Title of the source document")
    chunk_id: str = Field(..., description="Chunk identifier")
    chunk_text: str = Field(..., description="Content of the matched passage")
    score: float = Field(..., description="Cosine similarity score (0.0 to 1.0)")


# -----------------------------------------------------------------------------
# Research Workflow Models (Phase 5 Parallel Execution)
# -----------------------------------------------------------------------------
class ResearchRequest(BaseModel):
    """
    Data sent by the user to start a research task.
    """
    query: str = Field(
        ...,
        description="The research question or topic",
        examples=["Compare PostgreSQL, MongoDB and DynamoDB for an e-commerce backend"]
    )


class ResearchResponse(BaseModel):
    """
    Data returned to the user after running the parallel research workflow.
    In Phase 5, this includes both live web search results AND uploaded document passages!
    """
    status: str = Field(..., description="Current status of the research workflow", examples=["researched"])
    query: str = Field(..., description="Echoes back the research query received")
    sub_questions: List[str] = Field(default_factory=list, description="Sub-questions produced by Planner")
    search_results: List[SearchResultItem] = Field(default_factory=list, description="Live web sources (from web_researcher)")
    document_results: List[DocumentSearchResultItem] = Field(default_factory=list, description="Passages from uploaded documents (from doc_retriever)")
    message: str = Field(..., description="Human-readable explanation of current status")


# -----------------------------------------------------------------------------
# Document Management Models (Phase 4)
# -----------------------------------------------------------------------------
class DocumentUploadRequest(BaseModel):
    """
    Data sent by the user to upload and index a text document for RAG.
    """
    title: str = Field(..., description="Title of the document", examples=["PostgreSQL Architecture Guide"])
    content: str = Field(..., description="The full text content of the document")


class DocumentUploadResponse(BaseModel):
    """
    Response sent after chunking and vector indexing an uploaded document.
    """
    status: str = Field(default="indexed", description="Indexing status")
    doc_id: str = Field(..., description="Unique generated document ID")
    title: str = Field(..., description="Title of the stored document")
    num_chunks: int = Field(..., description="How many text chunks were created and vector indexed")
    message: str = Field(..., description="Confirmation message")


class DocumentListItem(BaseModel):
    """
    Summary representation of an indexed document.
    """
    doc_id: str
    title: str
    num_chunks: int
    char_count: int


class DocumentSearchResponse(BaseModel):
    """
    Response returned when querying the document vector store directly.
    """
    query: str
    total_matches: int
    results: List[DocumentSearchResultItem]
