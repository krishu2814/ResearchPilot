from typing import List, Optional
from pydantic import BaseModel, Field


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


class EvidenceItem(BaseModel):
    """
    An atomic factual claim extracted from source materials (Phase 6).
    """
    claim: str = Field(..., description="The concrete factual claim extracted from source material")
    source_type: str = Field(..., description="Origin type: 'web' or 'document'")
    source_title: str = Field(..., description="Title of the source webpage or document")
    source_url_or_id: str = Field(..., description="URL link or document ID")
    sub_question: str = Field(default="", description="Sub-question this claim supports")


class VerifiedEvidenceItem(BaseModel):
    """
    An audited claim with verification verdict and confidence score (Phase 7).
    """
    claim: str = Field(..., description="The audited factual claim")
    source_type: str = Field(..., description="Origin type: 'web' or 'document'")
    source_title: str = Field(..., description="Title of the source webpage or document")
    source_url_or_id: str = Field(..., description="URL link or document ID")
    sub_question: str = Field(default="", description="Sub-question this claim supports")
    verdict: str = Field(..., description="Audit verdict: 'verified', 'partial', or 'unverified'")
    confidence: float = Field(..., description="Confidence score from 0.0 to 1.0")
    rationale: str = Field(..., description="Fact-checker explanation and grounding rationale")


# -----------------------------------------------------------------------------
# Research Workflow Models (Phase 9 Persistent Pipeline)
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
    session_id: Optional[str] = Field(
        default=None,
        description="Optional session identifier; if not provided, a unique ID is auto-generated",
        examples=["sess_ecommerce_db"]
    )


class ResearchResponse(BaseModel):
    """
    Data returned to the user after running the research workflow.
    Includes persistent session_id, sub-questions, raw sources, document passages,
    extracted claims, verified facts, and the synthesized Markdown report!
    """
    session_id: str = Field(..., description="Unique persistent session ID for this research run")
    status: str = Field(..., description="Current status of the research workflow", examples=["researched"])
    query: str = Field(..., description="Echoes back the research query received")
    sub_questions: List[str] = Field(default_factory=list, description="Sub-questions produced by Planner")
    search_results: List[SearchResultItem] = Field(default_factory=list, description="Live web sources (from web_researcher)")
    document_results: List[DocumentSearchResultItem] = Field(default_factory=list, description="Passages from uploaded documents (from doc_retriever)")
    evidence: List[EvidenceItem] = Field(default_factory=list, description="Atomic claims and citations (from extractor)")
    verified_evidence: List[VerifiedEvidenceItem] = Field(default_factory=list, description="Audited claims with verdicts (from fact_checker)")
    report: str = Field(default="", description="Synthesized final Markdown research report with citations (from synthesizer)")
    message: str = Field(..., description="Human-readable explanation of current status")


# -----------------------------------------------------------------------------
# Session Persistence Models (Phase 9)
# -----------------------------------------------------------------------------
class SessionSummaryItem(BaseModel):
    """
    Lightweight summary representation of a stored research session.
    """
    session_id: str = Field(..., description="Unique session ID")
    query: str = Field(..., description="Original research query")
    status: str = Field(..., description="Status of the research session")
    created_at: str = Field(..., description="ISO 8601 timestamp when session was executed")
    num_sub_questions: int = Field(..., description="Number of sub-questions generated")
    num_sources: int = Field(..., description="Total web and document sources consulted")
    num_verified_claims: int = Field(..., description="Number of verified factual claims extracted")
    report_length: int = Field(..., description="Character count of the synthesized Markdown report")


class SessionDetailResponse(BaseModel):
    """
    Full research session record including complete graph state and synthesized report.
    """
    session_id: str
    query: str
    status: str
    created_at: str
    sub_questions: List[str] = Field(default_factory=list)
    search_results: List[SearchResultItem] = Field(default_factory=list)
    document_results: List[DocumentSearchResultItem] = Field(default_factory=list)
    evidence: List[EvidenceItem] = Field(default_factory=list)
    verified_evidence: List[VerifiedEvidenceItem] = Field(default_factory=list)
    report: str = Field(default="")


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


# -----------------------------------------------------------------------------
# Cache Monitoring Models (Phase 11)
# -----------------------------------------------------------------------------
class CacheStatsResponse(BaseModel):
    """
    Performance and operational metrics for the caching layer.
    """
    backend: str = Field(..., description="Active cache backend: 'redis' or 'memory'")
    hits: int = Field(..., description="Total cache hits")
    misses: int = Field(..., description="Total cache misses")
    total_requests: int = Field(..., description="Total cache lookups")
    hit_ratio: float = Field(..., description="Ratio of hits to total requests (0.0 to 1.0)")
    total_keys: int = Field(..., description="Number of currently cached keys")
