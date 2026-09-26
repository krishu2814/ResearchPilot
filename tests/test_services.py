import time
import os
import tempfile
import pytest
from app.services.documents import chunk_text, save_document, DOCUMENTS_STORE
from app.services.embeddings import get_embedding, cosine_similarity, VECTOR_DIMENSION
from app.services.cache import get_cache, set_cache, clear_cache, get_cache_stats
from app.services.resilience import CircuitBreaker, retry_with_backoff
from app.services.session_store import (
    init_db,
    save_session,
    get_session,
    list_sessions,
    delete_session
)


def test_chunk_text_basic():
    text = "The quick brown fox jumps over the lazy dog. " * 10
    chunks = chunk_text(text, chunk_size=100, overlap=20)
    assert len(chunks) > 1
    assert all(len(c) <= 100 for c in chunks)


def test_chunk_text_edge_cases():
    assert chunk_text("") == []
    assert chunk_text("   ") == []
    # Short text
    short = "Hello World"
    assert chunk_text(short, chunk_size=100) == [short]
    # Invalid chunk_size and overlap
    chunks = chunk_text("Some sample content for testing", chunk_size=-5, overlap=-10)
    assert len(chunks) >= 1


def test_save_document():
    DOCUMENTS_STORE.clear()
    record = save_document(title="Sample Guide", content="This is an introductory guide to testing.")
    assert record["title"] == "Sample Guide"
    assert record["doc_id"].startswith("doc_")
    assert len(record["chunks"]) >= 1


def test_embeddings_and_cosine():
    v1 = get_embedding("machine learning algorithms")
    v2 = get_embedding("machine learning models")
    v3 = get_embedding("culinary baking recipes")

    assert len(v1) == VECTOR_DIMENSION
    assert len(v2) == VECTOR_DIMENSION

    # Semantic similarity: related phrases score higher than unrelated phrases
    sim_related = cosine_similarity(v1, v2)
    sim_unrelated = cosine_similarity(v1, v3)

    assert sim_related > sim_unrelated
    assert 0.0 <= sim_related <= 1.0


def test_cosine_similarity_edge_cases():
    assert cosine_similarity([], []) == 0.0
    assert cosine_similarity([1.0], [1.0, 2.0]) == 0.0
    assert cosine_similarity([0.0, 0.0], [0.0, 0.0]) == 0.0


def test_cache_service():
    clear_cache()
    assert get_cache("test_nonexistent_key") is None

    set_cache("key1", {"data": 42}, ttl_seconds=60)
    val = get_cache("key1")
    assert val == {"data": 42}

    stats = get_cache_stats()
    assert stats["hits"] >= 1
    assert stats["total_keys"] >= 1

    clear_cache()
    assert get_cache("key1") is None


def test_circuit_breaker():
    cb = CircuitBreaker(failure_threshold=2, cooldown_seconds=0.1)
    assert cb.state == "CLOSED"
    assert cb.can_execute() is True

    # Record 1 failure -> still CLOSED
    cb.record_failure()
    assert cb.state == "CLOSED"

    # Record 2nd failure -> trips to OPEN
    cb.record_failure()
    assert cb.state == "OPEN"
    assert cb.can_execute() is False

    # Wait for cooldown
    time.sleep(0.12)
    assert cb.can_execute() is True
    assert cb.state == "HALF-OPEN"

    # Successful probe resets to CLOSED
    cb.record_success()
    assert cb.state == "CLOSED"


def test_retry_with_backoff():
    attempts = 0

    def flaky_func():
        nonlocal attempts
        attempts += 1
        if attempts < 2:
            raise ConnectionError("Temporary network blip")
        return "success"

    res = retry_with_backoff(flaky_func, max_retries=2, initial_delay=0.01)
    assert res == "success"
    assert attempts == 2

    # Test failure exhaustion
    def always_fails():
        raise ValueError("Fatal error")

    with pytest.raises(ValueError):
        retry_with_backoff(always_fails, max_retries=1, initial_delay=0.01)


def test_session_store_custom_path():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_sessions.db")
        init_db(db_path)

        state = {
            "sub_questions": ["q1", "q2"],
            "search_results": [{"title": "Web Title", "url": "https://example.com", "snippet": "Snippet"}],
            "document_results": [],
            "evidence": [{"claim": "Fact 1", "source_type": "web", "source_title": "Web Title", "source_url_or_id": "https://example.com"}],
            "verified_evidence": [{"claim": "Fact 1", "verdict": "verified", "confidence": 0.95}],
            "report": "# Report Title\nContent here."
        }

        save_session("test_sess_1", "Test Query", state, db_path=db_path)

        sess = get_session("test_sess_1", db_path=db_path)
        assert sess is not None
        assert sess["query"] == "Test Query"
        assert len(sess["sub_questions"]) == 2
        assert len(sess["evidence"]) == 1

        all_sess = list_sessions(db_path=db_path)
        assert len(all_sess) == 1
        assert all_sess[0]["session_id"] == "test_sess_1"

        deleted = delete_session("test_sess_1", db_path=db_path)
        assert deleted is True
        assert get_session("test_sess_1", db_path=db_path) is None
