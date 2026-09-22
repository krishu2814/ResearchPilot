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
| | Lesson 3.2 | Web Search Node in LangGraph | ⏳ Next Up |
| **Phase 4** | Lesson 4.1 | Document Parsing & Text Chunking | 📋 Planned |
| | Lesson 4.2 | Embeddings & pgvector Storage | 📋 Planned |
| | Lesson 4.3 | Document Retrieval Node | 📋 Planned |
| **Phase 5** | Lesson 5.1 | Parallel Graph Execution (Web + Documents) | 📋 Planned |
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
  "version": "0.2.0"
}
```

---

### 2. Research Planning (`POST /research`)
* **Method**: `POST`
* **Path**: `/research`
* **Description**: Runs the LangGraph research workflow (`START -> planner -> END`) to decompose a research topic into structured sub-questions.

```bash
curl -X POST http://127.0.0.1:8000/research \
     -H "Content-Type: application/json" \
     -d '{"query": "Compare PostgreSQL, MongoDB and DynamoDB for high scale"}'
```

**Response:**
```json
{
  "status": "planned",
  "query": "Compare PostgreSQL, MongoDB and DynamoDB for high scale",
  "sub_questions": [
    "What are the core architecture and design differences in Compare PostgreSQL, MongoDB and DynamoDB for high scale?",
    "How do performance, scaling, and consistency compare in Compare PostgreSQL, MongoDB and DynamoDB for high scale?",
    "What are the primary trade-offs and recommended use cases for Compare PostgreSQL, MongoDB and DynamoDB for high scale?"
  ],
  "message": "Planner generated 3 research sub-questions."
}
```

---

## 🧠 LangGraph Workflow Details (Phase 2)

Our agent workflow is constructed using `StateGraph`:

```text
[START]
   │
   ▼
[planner]  <-- app/agents/planner.py (receives question, outputs sub_questions)
   │
   ▼
 [END]
```

### State Definition (`app/graph/state.py`):
```python
class ResearchState(TypedDict):
    question: str
    sub_questions: List[str]
```

### Graph Definition (`app/graph/research_graph.py`):
```python
workflow = StateGraph(ResearchState)
workflow.add_node("planner", planner_node)
workflow.add_edge(START, "planner")
workflow.add_edge("planner", END)
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

