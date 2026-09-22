import os
import json
from app.graph.state import ResearchState

# -----------------------------------------------------------------------------
# Planner Node
# -----------------------------------------------------------------------------
# A node in LangGraph is just a regular Python function!
# It takes the current `state` as an argument and returns a dictionary with updates.
# -----------------------------------------------------------------------------
def planner_node(state: ResearchState) -> dict:
    """
    The Planner agent receives the user's research question,
    analyzes it, and breaks it down into targeted sub-questions.
    """
    question = state.get("question", "").strip()

    # If the question is empty, return empty sub-questions
    if not question:
        return {"sub_questions": []}

    print(f"[Planner Node] Generating research plan for: '{question}'")

    # Check if an API key is configured
    api_key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")

    if api_key:
        try:
            # We will use the LLM if a key is provided
            sub_questions = _generate_subquestions_with_llm(question, api_key)
            return {"sub_questions": sub_questions}
        except Exception as err:
            print(f"[Planner Node] LLM call failed ({err}). Falling back to rule-based planner.")

    # Fallback plan generator (for learning without needing an API key immediately)
    sub_questions = _generate_subquestions_fallback(question)
    return {"sub_questions": sub_questions}


# -----------------------------------------------------------------------------
# Helper: Fallback sub-question generator
# -----------------------------------------------------------------------------
def _generate_subquestions_fallback(question: str) -> list[str]:
    """
    Generates sensible research sub-questions without needing an external API.
    This ensures you can learn LangGraph mechanics immediately!
    """
    # Look for common comparison keywords (e.g. "compare X and Y")
    lower = question.lower()
    if "compare" in lower or " vs " in lower or "versus" in lower:
        return [
            f"What are the core architecture and design differences in {question}?",
            f"How do performance, scaling, and consistency compare in {question}?",
            f"What are the primary trade-offs and recommended use cases for {question}?"
        ]

    # Default sub-questions for general topics
    return [
        f"What is the foundational architecture and purpose of {question}?",
        f"What are the key advantages, disadvantages, and trade-offs of {question}?",
        f"What are the best practices and real-world considerations for {question}?"
    ]


# -----------------------------------------------------------------------------
# Helper: LLM sub-question generator
# -----------------------------------------------------------------------------
def _generate_subquestions_with_llm(question: str, api_key: str) -> list[str]:
    """
    Optional: Calls an LLM to generate 3 targeted sub-questions.
    Uses standard OpenAI-compatible HTTP endpoint if configured.
    """
    import httpx

    prompt = (
        f"You are a research planning assistant.\n"
        f"Break down the following research question into exactly 3 focused sub-questions.\n"
        f"Research Question: '{question}'\n\n"
        f"Return ONLY a JSON list of 3 strings, example: [\"q1\", \"q2\", \"q3\"]."
    )

    base_url = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
    model = os.getenv("LLM_MODEL", "gpt-4o-mini")

    response = httpx.post(
        f"{base_url}/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2
        },
        timeout=15.0
    )
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"].strip()

    # Clean markdown if present
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
    content = content.strip()

    parsed = json.loads(content)
    if isinstance(parsed, list):
        return [str(q) for q in parsed[:3]]
    return _generate_subquestions_fallback(question)
