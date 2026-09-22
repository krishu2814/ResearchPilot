from app.graph.state import ResearchState
from app.services.search import search_web


# -----------------------------------------------------------------------------
# Researcher Node
# -----------------------------------------------------------------------------
# In LangGraph:
# - A node is a simple Python function.
# - It receives the current `state`.
# - It does work (here: searches the web for each sub-question).
# - It returns a dictionary of state updates (here: {"search_results": [...]}).
# -----------------------------------------------------------------------------
def researcher_node(state: ResearchState) -> dict:
    """
    The Researcher agent reads the sub-questions produced by the Planner,
    searches the live web for each sub-question, and collects the evidence.
    """
    sub_questions = state.get("sub_questions", [])
    collected_results = []

    print(f"\n[Researcher Node] Starting web research for {len(sub_questions)} sub-questions...")

    for i, sub_q in enumerate(sub_questions, 1):
        print(f"[Researcher Node] ({i}/{len(sub_questions)}) Searching: '{sub_q}'")

        # Search the web for this specific sub-question (top 2 results per question)
        results = search_web(query=sub_q, max_results=2)

        for item in results:
            # We tag each result with the sub_question it helps answer
            collected_results.append({
                "sub_question": sub_q,
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "snippet": item.get("snippet", "")
            })

    print(f"[Researcher Node] Completed research. Total sources gathered: {len(collected_results)}\n")

    # Return state update: LangGraph merges this into ResearchState
    return {"search_results": collected_results}
