from langgraph.graph import StateGraph, START, END
from app.graph.state import ResearchState
from app.agents.planner import planner_node


# -----------------------------------------------------------------------------
# Graph Builder
# -----------------------------------------------------------------------------
# A LangGraph workflow is made of:
# 1. State: The data structure passing between nodes (ResearchState).
# 2. Nodes: Functions that do work (like planner_node).
# 3. Edges: Connectors that decide which node runs next (START -> planner -> END).
# -----------------------------------------------------------------------------
def build_research_graph():
    """
    Constructs and compiles the Phase 2 research workflow graph.
    Flow:
        START -> planner -> END
    """
    # 1. Create a StateGraph initialized with our ResearchState
    workflow = StateGraph(ResearchState)

    # 2. Register the 'planner' node
    workflow.add_node("planner", planner_node)

    # 3. Add edges:
    # From START to the planner node
    workflow.add_edge(START, "planner")

    # From the planner node to END
    workflow.add_edge("planner", END)

    # 4. Compile the graph into a runnable instance
    return workflow.compile()


# We create a compiled graph instance ready for use across our app
research_graph = build_research_graph()
