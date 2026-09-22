from langgraph.graph import StateGraph, START, END
from app.graph.state import ResearchState
from app.agents.planner import planner_node
from app.agents.researcher import researcher_node
from app.agents.retriever import document_retriever_node
from app.agents.extractor import extractor_node
from app.agents.fact_checker import fact_checker_node


# -----------------------------------------------------------------------------
# Parallel Research Graph with Fact Checking (Phase 7)
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
#                [extractor]                <-- Barrier Join & Claim Extraction
#                     │
#                     ▼
#               [fact_checker]              <-- Phase 7: Audits claims & assigns verdicts
#                     │
#                     ▼
#                   [END]
# -----------------------------------------------------------------------------
def build_research_graph():
    """
    Constructs and compiles the Phase 7 research workflow graph.
    """
    # 1. Initialize StateGraph with our shared state schema
    workflow = StateGraph(ResearchState)

    # 2. Register all agent nodes
    workflow.add_node("planner", planner_node)
    workflow.add_node("web_researcher", researcher_node)
    workflow.add_node("doc_retriever", document_retriever_node)
    workflow.add_node("extractor", extractor_node)
    workflow.add_node("fact_checker", fact_checker_node)

    # 3. Connect START to planner
    workflow.add_edge(START, "planner")

    # 4. FAN-OUT: From planner, split into two parallel research branches
    workflow.add_edge("planner", "web_researcher")
    workflow.add_edge("planner", "doc_retriever")

    # 5. FAN-IN: Both branches point to extractor (LangGraph waits for both!)
    workflow.add_edge("web_researcher", "extractor")
    workflow.add_edge("doc_retriever", "extractor")

    # 6. From extractor to fact_checker
    workflow.add_edge("extractor", "fact_checker")

    # 7. From fact_checker to END
    workflow.add_edge("fact_checker", END)

    # 8. Compile into a runnable agent graph
    return workflow.compile()


# Create compiled instance ready for use across our application
research_graph = build_research_graph()
