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
| **Phase 5** | Lesson 5.1 | Parallel Graph Execution (Web + Documents) | ⏳ Next Up |
| **Phase 6** | Lesson 6.1 | Evidence Schema & Information Extraction | 📋 Planned |
| **Phase 7** | Lesson 7.1 | Fact Checker: Validating claims against sources | 📋 Planned |
| **Phase 8** | Lesson 8.1 | Report Synthesis: Structured final document | 📋 Planned |
| **Phase 9** | Lesson 9.1 | PostgreSQL Session Memory & Persistence | 📋 Planned |
| **Phase 10**| Lesson 10.1| Server-Sent Events (SSE) Progress Streaming | 📋 Planned |
| **Phase 11**| Lesson 11.1| Redis Caching for Search & State | 📋 Planned |
| **Phase 12**| Lesson 12.1| Error Handling & Fault Tolerance | 📋 Planned |
| **Phase 13**| Lesson 13.1| Automated Testing with pytest | 📋 Planned |
| **Phase 14**| Lesson 14.1| Docker & docker-compose Deployment | 📋 Planned |
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
  "version": "0.3.0"
}
```

---

### 2. Multi-Agent Research (`POST /research`)
* **Method**: `POST`
* **Path**: `/research`
* **Description**: Runs the multi-agent LangGraph workflow (`START -> planner -> researcher -> END`). The Planner breaks the topic into sub-questions, and the Researcher queries the live web to collect evidence.

```bash
curl -X POST http://127.0.0.1:8000/research \
     -H "Content-Type: application/json" \
     -d '{"query": "FastAPI vs Express"}'
```

**Response:**
```json
{
  "status": "researched",
  "query": "FastAPI vs Express",
  "sub_questions": [
    "What are the core architecture and design differences in FastAPI vs Express?",
    "How do performance, scaling, and consistency compare in FastAPI vs Express?",
    "What are the primary trade-offs and recommended use cases for FastAPI vs Express?"
  ],
  "search_results": [
    {
      "sub_question": "What are the core architecture and design differences in FastAPI vs Express?",
      "title": "FastAPI vs Express: Which Backend Framework Actually Wins?",
      "url": "https://www.kunalganglani.com/blog/fastapi-vs-express",
      "snippet": "Detailed comparison of asynchronous event loops, Python typing vs Node.js ecosystem..."
    }
  ],
  "message": "Planner generated 3 sub-questions, and Researcher gathered 6 web sources."
}
```

---

## 🧠 LangGraph Multi-Agent Workflow Details (Phase 3)

Our agent workflow connects multiple specialized agents using `StateGraph`:

```text
  [START]
     │
     ▼
 [planner]     <-- app/agents/planner.py (breaks question into sub-questions)
     │
     ▼
[researcher]   <-- app/agents/researcher.py (searches the web for each sub-question)
     │
     ▼
   [END]
```

### State Definition (`app/graph/state.py`):
```python
class ResearchState(TypedDict):
    question: str
    sub_questions: List[str]
    search_results: List[dict]
```

### Graph Definition (`app/graph/research_graph.py`):
```python
workflow = StateGraph(ResearchState)
workflow.add_node("planner", planner_node)
workflow.add_node("researcher", researcher_node)

workflow.add_edge(START, "planner")
workflow.add_edge("planner", "researcher")
workflow.add_edge("researcher", END)

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

