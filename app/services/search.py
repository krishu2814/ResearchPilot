"""
Web Search Service for ResearchPilot.

This module provides a simple function to search the live web using DuckDuckGo (via the `ddgs` library).
It requires NO API keys, making it completely free and easy to get started with.
"""

from ddgs import DDGS
from app.services.cache import get_cache, set_cache
from app.services.resilience import search_circuit_breaker, retry_with_backoff


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

    # 1. Check cache first (Phase 11)
    cache_key = f"search:{clean_query}:{max_results}"
    cached_results = get_cache(cache_key)
    if cached_results is not None:
        print(f"[Search Service] Cache hit for: '{clean_query}' ({len(cached_results)} results)")
        return cached_results

    # 2. Check Circuit Breaker (Phase 12)
    # If the search service has failed repeatedly, fast-fail immediately without waiting!
    if not search_circuit_breaker.can_execute():
        print(f"[Search Service] Circuit breaker is OPEN. Fast-failing immediately to fallback results for: '{clean_query}'")
        return _search_fallback(clean_query, max_results)

    print(f"[Search Service] Cache miss. Searching web for: '{clean_query}' (max results: {max_results})")

    try:
        # 3. Execute search with Exponential Backoff Retry (Phase 12)
        # Transient network hiccups will automatically retry (0.2s, 0.4s) before giving up!
        def _fetch():
            return list(DDGS().text(clean_query, max_results=max_results))

        raw_results = retry_with_backoff(_fetch, max_retries=2, initial_delay=0.2)

        # Record healthy search execution in the circuit breaker
        search_circuit_breaker.record_success()

        # Format raw results into clean, beginner-friendly dictionaries
        formatted_results = []
        for item in raw_results:
            formatted_results.append({
                "title": item.get("title", "No title"),
                "url": item.get("href", ""),
                "snippet": item.get("body", "")
            })

        # Save to cache for 1 hour (3600 seconds)
        set_cache(cache_key, formatted_results, ttl_seconds=3600)
        return formatted_results

    except Exception as error:
        # If live search fails after retries, record the failure in circuit breaker
        search_circuit_breaker.record_failure()
        print(f"[Search Service] Live search failed after retries ({error}). Using fallback results.")
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
