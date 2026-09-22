from langgraph.graph import StateGraph, START, END
from app.graph.state import ResearchState
from app.agents.planner import planner_node
from app.agents.researcher import researcher_node
from app.agents.retriever import document_retriever_node


# -----------------------------------------------------------------------------
# Join Node (Fan-in Barrier)
# -----------------------------------------------------------------------------
def combine_results_node(state: ResearchState) -> dict:
    """
    Barrier Join Node:
    LangGraph calls this node ONLY after BOTH web_researcher and doc_retriever have finished!
    It logs the combined collection and passes the state forward.
    """
    web_count = len(state.get("search_results", []))
    doc_count = len(state.get("document_results", []))
    print(f"[Combine Node] Both parallel branches finished! Merged {web_count} web sources + {doc_count} document passages.")
    return {}


# -----------------------------------------------------------------------------
# Parallel Graph Builder (Phase 5)
# -----------------------------------------------------------------------------
# Graph Topology:
#                  [START]
#                     │
#                     ▼
#                 [planner]
#                     │
#            ┌────────┴────────┐
#            ▼                 ▼
#     [web_researcher]   [doc_retriever]    <-- Run in Parallel!
#            └────────┬────────┘
#                     ▼
#              [combine_results]            <-- Synchronization Barrier
#                     │
#                     ▼
#                   [END]
# -----------------------------------------------------------------------------
def build_research_graph():
    """
    Constructs and compiles the Phase 5 parallel research workflow.
    """
    # 1. Initialize StateGraph with our shared state schema
    workflow = StateGraph(ResearchState)

    # 2. Register all agent nodes
    workflow.add_node("planner", planner_node)
    workflow.add_node("web_researcher", researcher_node)
    workflow.add_node("doc_retriever", document_retriever_node)
    workflow.add_node("combine_results", combine_results_node)

    # 3. Connect START to planner
    workflow.add_edge(START, "planner")

    # 4. FAN-OUT: From planner, split into two parallel branches!
    workflow.add_edge("planner", "web_researcher")
    workflow.add_edge("planner", "doc_retriever")

    # 5. FAN-IN: Both branches point to combine_results (LangGraph waits for both!)
    workflow.add_edge("web_researcher", "combine_results")
    workflow.add_edge("doc_retriever", "combine_results")

    # 6. From combine_results to END
    workflow.add_edge("combine_results", END)

    # 7. Compile into a runnable agent graph
    return workflow.compile()


# Create compiled instance ready for use across our application
research_graph = build_research_graph()
