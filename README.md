# 🚀 ResearchPilot — Agentic Research & RAG Platform

> An educational, beginner-friendly Agentic AI backend that conducts automated web and document research, verifies facts, and synthesizes structured reports with citations.

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2+-FF6F00?style=flat&logo=langchain&logoColor=white)](https://langchain-ai.github.io/langgraph/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📖 Table of Contents
- [Project Overview](#-project-overview)
- [System Architecture](#-system-architecture)
- [Learning Roadmap (Phases & Lessons)](#-learning-roadmap-phases--lessons)
- [Local Setup Guide](#-local-setup-guide)
- [API Documentation & Examples](#-api-documentation--examples)
- [LangGraph Workflow Details](#-langgraph-workflow-details)

---

## 🧭 Project Overview

**ResearchPilot** is designed to solve a core problem in AI: *How do we make an LLM research a complex topic without hallucinating or making unsupported claims?*

Instead of asking a single prompt to an LLM, ResearchPilot breaks research down into a multi-agent pipeline:
1. **Planning**: Breaks a broad topic into focused research sub-questions.
2. **Searching**: Queries the live web and local vector database (pgvector).
3. **Evidence Gathering**: Extracts concrete claims with explicit sources and URLs.
4. **Fact Checking**: Audits claims against source material.
5. **Synthesis**: Produces a clean, structured research report with citations.

---

## 🏗 System Architecture

```text
       User (Frontend or curl)
                 │
                 ▼
        FastAPI Web Server
                 │
                 ▼
       LangGraph Research Agent
                 │
      ┌──────────┴──────────┐
      ▼                     ▼
Web Search (Tavily/Duck)  Document RAG (pgvector)
      └──────────┬──────────┘
                 ▼
         Evidence Collector
                 │
                 ▼
           Fact Checker
                 │
                 ▼
         Report Synthesizer
                 │
                 ▼
        Final Research Report
```

---

## 📚 Learning Roadmap (Phases & Lessons)

| Phase | Lesson | Topic | Status |
| :--- | :--- | :--- | :---: |
| **Phase 1** | Lesson 1.1 | Project Setup, Environment, and Health Endpoint | ✅ Completed |
| | Lesson 1.2 | Basic Request/Response with Pydantic Schemas | ✅ Completed |
| **Phase 2** | Lesson 2.1 | LangGraph Fundamentals: State, Nodes, and Edges | ✅ Completed |
| | Lesson 2.2 | The Planner Node: Breaking questions into sub-questions | ✅ Completed |
| | Lesson 2.3 | Building & Compiling `START -> planner -> END` Graph | ✅ Completed |
| **Phase 3** | Lesson 3.1 | Web Search Tool: Integrating live search | ✅ Completed |
| | Lesson 3.2 | Web Search Node in LangGraph | ✅ Completed |
| **Phase 4** | Lesson 4.1 | Document Parsing & Text Chunking | ✅ Completed |
| | Lesson 4.2 | Embeddings & Vector Storage (Cosine Similarity) | ✅ Completed |
| | Lesson 4.3 | Document Retrieval Node & Ingestion API | ✅ Completed |
| **Phase 5** | Lesson 5.1 | Parallel Graph Execution (Web + Documents) | ✅ Completed |
| **Phase 6** | Lesson 6.1 | Evidence Schema & Information Extraction | ✅ Completed |
| **Phase 7** | Lesson 7.1 | Fact Checker: Validating claims against sources | ✅ Completed |
| **Phase 8** | Lesson 8.1 | Report Synthesis: Structured final document | ✅ Completed |
| **Phase 9** | Lesson 9.1 | Session Memory & Database Persistence | ✅ Completed |
| **Phase 10**| Lesson 10.1| Server-Sent Events (SSE) Progress Streaming | ✅ Completed |
| **Phase 11**| Lesson 11.1| Redis Caching for Search & State | ✅ Completed |
| **Phase 12**| Lesson 12.1| Error Handling & Fault Tolerance | ✅ Completed |
| **Phase 13**| Lesson 13.1| Automated Testing with pytest | ✅ Completed |
| **Phase 14**| Lesson 14.1| Docker & docker-compose Deployment | ⏳ Next Up |
| **Phase 15**| Lesson 15.1| Final Portfolio Presentation & Review | 📋 Planned |

---

## 🛠 Local Setup Guide

### 1. Prerequisites
* Python 3.11+
* Git

### 2. Setup Environment
```bash
# Navigate to project directory
cd ResearchPilot

# Create Python virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Run the Development Server
```bash
uvicorn app.main:app --reload --port 8000
```

The server will start at: `http://127.0.0.1:8000`

---

## 📡 API Documentation & Examples

### 1. Health Check
* **Method**: `GET`
* **Path**: `/health`

```bash
curl http://127.0.0.1:8000/health
```

**Response:**
```json
{
  "status": "ok",
  "service": "ResearchPilot",
  "version": "0.9.0"
}
```

---

### 2. Multi-Agent Research (`POST /research`)
* **Method**: `POST`
* **Path**: `/research`
* **Description**: Runs the complete multi-agent LangGraph research workflow (`START -> planner -> [web_researcher + doc_retriever] -> extractor -> fact_checker -> synthesizer -> END`). The Planner decomposes the topic into sub-questions, the Web Researcher and Document Retriever execute concurrently to gather evidence from the live web and uploaded documents, the Extractor distills sources into atomic factual claims with citations, the Fact Checker audits each claim for truthfulness, the Synthesizer compiles verified findings into a publication-ready Markdown report, and the complete session is persisted to SQLite.

```bash
curl -X POST http://127.0.0.1:8000/research \
     -H "Content-Type: application/json" \
     -d '{"query": "Compare PostgreSQL and MongoDB"}'
```

**Response:**
```json
{
  "session_id": "sess_46df5580",
  "status": "researched",
  "query": "Compare PostgreSQL and MongoDB",
  "sub_questions": [
    "What are the core architecture and design differences in Compare PostgreSQL and MongoDB?",
    "How do performance, scaling, and consistency compare in Compare PostgreSQL and MongoDB?",
    "What are the primary trade-offs and recommended use cases for Compare PostgreSQL and MongoDB?"
  ],
  "search_results": [ ... ],
  "document_results": [ ... ],
  "evidence": [ ... ],
  "verified_evidence": [ ... ],
  "report": "# 📑 Research Report: Compare PostgreSQL and MongoDB\n\n## 1. Executive Summary\n...",
  "message": "Planner generated 3 sub-questions. Gathered 4 web sources and 3 document passages in parallel, extracting 7 claims, verifying 7 facts, synthesizing a 4250-character report, and saving session 'sess_46df5580' to database."
}
```

---

### 3. Session Persistence Endpoints (`/sessions`)
* **List Past Sessions**: `GET /sessions`
  ```bash
  curl http://127.0.0.1:8000/sessions
  ```
* **Retrieve Session Details & Report**: `GET /sessions/{session_id}`
  ```bash
  curl http://127.0.0.1:8000/sessions/sess_46df5580
  ```
* **Delete Session**: `DELETE /sessions/{session_id}`
  ```bash
  curl -X DELETE http://127.0.0.1:8000/sessions/sess_46df5580
  ```

---

### 4. Caching & Performance Endpoints (`/cache`)
* **View Cache Metrics & Hit Ratio**: `GET /cache/stats`
  ```bash
  curl http://127.0.0.1:8000/cache/stats
  ```
* **Clear Cache**: `POST /cache/clear`
  ```bash
  curl -X POST http://127.0.0.1:8000/cache/clear
  ```

---

## 🧠 LangGraph Report Synthesis Workflow Details (Phase 8)

Our agent workflow implements **Parallel Graph Execution + Evidence Extraction + Automated Fact-Checking + Report Synthesis**:

```text
                  [START]
                     │
                     ▼
                 [planner]
                     │
            ┌────────┴────────┐
            ▼                 ▼
     [web_researcher]   [doc_retriever]    <-- Run in Parallel!
            └────────┬────────┘
                     ▼
                [extractor]                <-- Barrier Join & Evidence Extraction!
                     │
                     ▼
               [fact_checker]              <-- Audits claims, assigns verdicts & confidence!
                     │
                     ▼
               [synthesizer]               <-- Compiles final structured Markdown report!
                     │
                     ▼
                   [END]
```

### State Definition (`app/graph/state.py`):
```python
class ResearchState(TypedDict):
    question: str
    sub_questions: List[str]
    search_results: List[dict]       # Web evidence (DuckDuckGo)
    document_results: List[dict]     # Document RAG evidence (Vector store)
    evidence: List[dict]             # Atomic claims with citations (Phase 6)
    verified_evidence: List[dict]    # Audited claims with verdicts & confidence (Phase 7)
    report: str                      # Synthesized Markdown research report (Phase 8)
```

### Graph Definition (`app/graph/research_graph.py`):
```python
workflow = StateGraph(ResearchState)
workflow.add_node("planner", planner_node)
workflow.add_node("web_researcher", researcher_node)
workflow.add_node("doc_retriever", document_retriever_node)
workflow.add_node("extractor", extractor_node)
workflow.add_node("fact_checker", fact_checker_node)
workflow.add_node("synthesizer", synthesizer_node)

# Fan-out: Planner splits into two concurrent branches
workflow.add_edge(START, "planner")
workflow.add_edge("planner", "web_researcher")
workflow.add_edge("planner", "doc_retriever")

# Fan-in: LangGraph waits for both branches before continuing to extractor
workflow.add_edge("web_researcher", "extractor")
workflow.add_edge("doc_retriever", "extractor")

# Fact-checker audits claims, then synthesizer compiles the final report
workflow.add_edge("extractor", "fact_checker")
workflow.add_edge("fact_checker", "synthesizer")
workflow.add_edge("synthesizer", END)

research_graph = workflow.compile()
```

---

## 🔍 Web Search Service (Phase 3 — Lesson 3.1)

In Lesson 3.1, we built a standalone search tool in `app/services/search.py` using `ddgs` (DuckDuckGo Search). This gives our agent real-time access to the live web without requiring an API key.

### Usage Example:
```python
from app.services.search import search_web

results = search_web("FastAPI vs Flask", max_results=2)
for r in results:
    print(r["title"])
    print(r["url"])
    print(r["snippet"])
```

### Test Directly from Terminal:
```bash
python -m app.services.search
```

---

## 📄 Document RAG & Vector Storage (Phase 4)

In Phase 4, we added Retrieval-Augmented Generation (RAG) capabilities so the platform can search uploaded documents alongside web search.

### Key Components:
1. **Document Chunking** ([app/services/documents.py](app/services/documents.py)):
   Splits large documents into overlapping character chunks (`chunk_size=300`, `overlap=50`) so context isn't lost at chunk boundaries.
2. **Embeddings & Cosine Similarity** ([app/services/embeddings.py](app/services/embeddings.py)):
   Converts text chunks into numerical vectors and calculates cosine similarity ($A \cdot B / (\|A\| \|B\|)$) to score relevance.
3. **Vector Store** ([app/services/rag.py](app/services/rag.py)):
   Stores chunks and their vector embeddings, and performs ranked semantic search.

### API Endpoints:

#### 1. Upload & Index a Document (`POST /documents`)
```bash
curl -X POST http://127.0.0.1:8000/documents \
     -H "Content-Type: application/json" \
     -d '{
       "title": "PostgreSQL Architecture Guide",
       "content": "PostgreSQL is an advanced open-source relational database. It supports ACID compliance, advanced indexing, JSON querying, and horizontal scaling via read replicas."
     }'
```

**Response:**
```json
{
  "status": "indexed",
  "doc_id": "doc_a1b2c3d4",
  "title": "PostgreSQL Architecture Guide",
  "num_chunks": 1,
  "message": "Document 'PostgreSQL Architecture Guide' successfully parsed into 1 chunks and vector indexed."
}
```

#### 2. Search Document Passages (`GET /documents/search`)
```bash
curl "http://127.0.0.1:8000/documents/search?q=PostgreSQL+indexing&top_k=2"
```

**Response:**
```json
{
  "query": "PostgreSQL indexing",
  "total_matches": 1,
  "results": [
    {
      "doc_id": "doc_a1b2c3d4",
      "title": "PostgreSQL Architecture Guide",
      "chunk_id": "doc_a1b2c3d4_c1",
      "chunk_text": "PostgreSQL is an advanced open-source relational database...",
      "score": 0.4082
    }
  ]
}
```

---

## 🛡️ Error Handling, Retry & Circuit Breaker (Phase 12)

In Phase 12, we equipped ResearchPilot with industrial-grade resilience patterns, ensuring that external network blips or outages never crash the agent graph:

### 1. Retry with Exponential Backoff (`app/services/resilience.py`)
- Automatically retries transient network errors (such as socket resets or temporary rate limits) with escalating delays ($0.2\text{s} \to 0.4\text{s} \to 0.8\text{s}$).
- Configurable via `max_retries`, `initial_delay`, and `backoff_factor`.

### 2. Circuit Breaker Pattern (`CircuitBreaker`)
Protects the web research agent from hammering failing upstream providers:
* **CLOSED (Normal)**: All web search calls execute normally.
* **OPEN (Tripped)**: After 3 consecutive network failures, the circuit trips to `OPEN`. For the 15-second cooldown window, calls fail fast immediately to local fallback summaries without waiting for network timeouts.
* **HALF-OPEN (Probe)**: Once the 15-second cooldown expires, the breaker lets a single probe call pass through to test if DuckDuckGo has recovered. If successful, the circuit resets to `CLOSED`.

### 3. Global Exception Handlers (`app/main.py`)
Intercepts unhandled errors across the entire FastAPI app and formats them into a clean, uniform `ErrorResponse`:
* `HTTPException` (e.g. 404 Not Found)
* `RequestValidationError` (e.g. 422 Bad Request with formatted schema hints)
* `Exception` (e.g. 500 Internal Server Error safety net)

### 4. Monitoring & Admin Endpoints

#### View Circuit Breaker Status:
```bash
curl http://127.0.0.1:8000/resilience/circuit-breaker
```
**Response:**
```json
{
  "state": "CLOSED",
  "failure_count": 0,
  "failure_threshold": 3,
  "cooldown_seconds": 15.0,
  "seconds_until_probe": 0.0
}
```

#### Manually Reset Circuit Breaker:
```bash
curl -X POST http://127.0.0.1:8000/resilience/circuit-breaker/reset
```


