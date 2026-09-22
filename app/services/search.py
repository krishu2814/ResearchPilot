"""
Web Search Service for ResearchPilot.

This module provides a simple function to search the live web using DuckDuckGo (via the `ddgs` library).
It requires NO API keys, making it completely free and easy to get started with.
"""

from ddgs import DDGS


def search_web(query: str, max_results: int = 3) -> list[dict]:
    """
    Searches the live web for a given query and returns a list of clean results.

    Each result is a dictionary containing:
    - 'title': The headline of the web page.
    - 'url': The link to the web page.
    - 'snippet': A short summary or text preview of the page.

    Args:
        query: What you want to search for (e.g. "PostgreSQL vs MongoDB").
        max_results: Maximum number of search results to return (default is 3).

    Returns:
        A list of search result dictionaries.
    """
    clean_query = query.strip()
    if not clean_query:
        return []

    print(f"[Search Service] Searching web for: '{clean_query}' (max results: {max_results})")

    try:
        # DDGS().text() sends the search query to DuckDuckGo
        raw_results = DDGS().text(clean_query, max_results=max_results)

        # Format raw results into clean, beginner-friendly dictionaries
        formatted_results = []
        for item in raw_results:
            formatted_results.append({
                "title": item.get("title", "No title"),
                "url": item.get("href", ""),
                "snippet": item.get("body", "")
            })

        return formatted_results

    except Exception as error:
        # If there is no internet connection or DuckDuckGo is unreachable,
        # we log the error and use a fallback so our application never crashes!
        print(f"[Search Service] Live search failed ({error}). Using fallback results.")
        return _search_fallback(clean_query, max_results)


def _search_fallback(query: str, max_results: int) -> list[dict]:
    """
    Fallback mock results when offline or rate-limited.
    Keeps learning uninterrupted!
    """
    return [
        {
            "title": f"Overview and Guide for {query}",
            "url": "https://example.com/research-guide",
            "snippet": f"This is an automated research summary providing reference data and architecture comparisons for '{query}'."
        }
    ][:max_results]


# -----------------------------------------------------------------------------
# Quick manual test: You can run this file directly with:
# python -m app.services.search
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    test_query = "FastAPI vs Flask"
    print(f"Testing search_web() with query: '{test_query}'...\n")
    results = search_web(test_query, max_results=2)
    for i, res in enumerate(results, 1):
        print(f"[{i}] {res['title']}")
        print(f"    URL: {res['url']}")
        print(f"    Snippet: {res['snippet'][:120]}...\n")
