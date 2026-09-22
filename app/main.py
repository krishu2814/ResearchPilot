from fastapi import FastAPI
from app.schemas import ResearchRequest, ResearchResponse
from app.graph.research_graph import research_graph

# 1. Create FastAPI instance
app = FastAPI(
    title="ResearchPilot API",
    description="Agentic Research & RAG Platform - Phase 2 LangGraph Planner",
    version="0.2.0",
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
        "version": "0.2.0"
    }


# 3. Research endpoint powered by LangGraph
@app.post("/research", response_model=ResearchResponse, tags=["Research"])
def start_research(request: ResearchRequest):
    """
    Receives a research query from the user, passes it to the LangGraph
    research workflow (START -> Planner -> END), and returns the plan.
    """
    # Step A: Initialize the graph state
    initial_state = {
        "question": request.query,
        "sub_questions": []
    }

    # Step B: Run the graph
    # LangGraph starts at START, calls planner_node, and finishes at END
    final_state = research_graph.invoke(initial_state)

    # Step C: Return the updated state as an API response
    return ResearchResponse(
        status="planned",
        query=final_state["question"],
        sub_questions=final_state["sub_questions"],
        message=f"Planner generated {len(final_state['sub_questions'])} research sub-questions."
    )
