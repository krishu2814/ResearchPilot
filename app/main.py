from fastapi import FastAPI
from app.schemas import ResearchRequest, ResearchResponse
from app.graph.research_graph import research_graph

# 1. Create FastAPI instance
app = FastAPI(
    title="ResearchPilot API",
    description="Agentic Research & RAG Platform - Phase 3 Multi-Agent Search",
    version="0.3.0",
)


# 2. Health check endpoint
@app.get("/health", tags=["System"])
def health_check():
    """
    Returns the health status of the API server.
    """
    return {
        "status": "ok",
        "service": "ResearchPilot",
        "version": "0.3.0"
    }


# 3. Research endpoint powered by LangGraph
@app.post("/research", response_model=ResearchResponse, tags=["Research"])
def start_research(request: ResearchRequest):
    """
    Receives a research query from the user, passes it to the LangGraph
    multi-agent workflow (START -> Planner -> Researcher -> END), and returns results.
    """
    # Step A: Initialize the graph state
    initial_state = {
        "question": request.query,
        "sub_questions": [],
        "search_results": []
    }

    # Step B: Run the multi-agent graph
    final_state = research_graph.invoke(initial_state)

    # Step C: Format response
    num_questions = len(final_state.get("sub_questions", []))
    num_results = len(final_state.get("search_results", []))

    return ResearchResponse(
        status="researched",
        query=final_state["question"],
        sub_questions=final_state["sub_questions"],
        search_results=final_state["search_results"],
        message=f"Planner generated {num_questions} sub-questions, and Researcher gathered {num_results} web sources."
    )
