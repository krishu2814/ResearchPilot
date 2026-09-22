from langgraph.graph import StateGraph, START, END
from app.graph.state import ResearchState
from app.agents.planner import planner_node
from app.agents.researcher import researcher_node


# -----------------------------------------------------------------------------
# Graph Builder (Phase 3)
# -----------------------------------------------------------------------------
# In LangGraph:
# 1. State: The shared data dictionary (ResearchState).
# 2. Nodes: Workers that process data (planner_node, researcher_node).
# 3. Edges: Arrows that connect the workflow steps:
#           START -> planner -> researcher -> END
# -----------------------------------------------------------------------------
def build_research_graph():
    """
    Constructs and compiles the Phase 3 research workflow graph.
    Flow:
        START -> planner -> researcher -> END
    """
    # 1. Initialize StateGraph with our shared state schema
    workflow = StateGraph(ResearchState)

    # 2. Register nodes
    workflow.add_node("planner", planner_node)
    workflow.add_node("researcher", researcher_node)

    # 3. Connect nodes with edges
    # START -> planner: User question goes first to Planner
    workflow.add_edge(START, "planner")

    # planner -> researcher: Sub-questions go to Researcher to search the web
    workflow.add_edge("planner", "researcher")

    # researcher -> END: Research data collected and workflow completes
    workflow.add_edge("researcher", END)

    # 4. Compile into a runnable agent graph
    return workflow.compile()


# Create compiled instance ready for use in FastAPI
research_graph = build_research_graph()
