from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "ResearchPilot"
    assert "version" in data


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_cache_endpoints():
    response = client.get("/cache/stats")
    assert response.status_code == 200
    data = response.json()
    assert "backend" in data
    assert "hits" in data
    assert "misses" in data

    clear_resp = client.post("/cache/clear")
    assert clear_resp.status_code == 200
    assert clear_resp.json()["status"] == "cleared"


def test_resilience_endpoints():
    response = client.get("/resilience/circuit-breaker")
    assert response.status_code == 200
    data = response.json()
    assert data["state"] in ("CLOSED", "OPEN", "HALF-OPEN")

    reset_resp = client.post("/resilience/circuit-breaker/reset")
    assert reset_resp.status_code == 200
    assert reset_resp.json()["status"] == "reset"


def test_documents_lifecycle():
    # 1. Upload document
    upload_resp = client.post("/documents", json={
        "title": "API Test Document",
        "content": "FastAPI is a modern, fast web framework for building APIs with Python 3.8+ based on standard Python type hints."
    })
    assert upload_resp.status_code == 200
    upload_data = upload_resp.json()
    assert upload_data["status"] == "indexed"
    assert upload_data["num_chunks"] >= 1

    # 2. List documents
    list_resp = client.get("/documents")
    assert list_resp.status_code == 200
    docs = list_resp.json()
    assert len(docs) >= 1
    assert any(d["title"] == "API Test Document" for d in docs)

    # 3. Document stats
    stats_resp = client.get("/documents/stats")
    assert stats_resp.status_code == 200
    stats = stats_resp.json()
    assert stats["total_chunks_indexed"] >= 1
    assert stats["unique_documents"] >= 1

    # 4. Search document vector store
    search_resp = client.get("/documents/search?q=FastAPI+web+framework&top_k=2")
    assert search_resp.status_code == 200
    search_data = search_resp.json()
    assert search_data["total_matches"] >= 1


def test_error_handlers():
    # 404 handler
    resp = client.get("/sessions/definitely_not_a_real_session_id_xyz")
    assert resp.status_code == 404
    data = resp.json()
    assert data["error"] == "HTTP Error"
    assert "not found" in data["detail"].lower()

    # 422 validation handler
    resp2 = client.post("/research", json={})
    assert resp2.status_code == 422
    data2 = resp2.json()
    assert data2["error"] == "Validation Error"

    # 400 empty query handlers
    resp3 = client.post("/research", json={"query": "   "})
    assert resp3.status_code == 400
    assert "cannot be empty" in resp3.json()["detail"].lower()

    resp4 = client.get("/research/stream?query=   ")
    assert resp4.status_code == 400
    assert "cannot be empty" in resp4.json()["detail"].lower()

    resp5 = client.post("/documents", json={"title": "   ", "content": "valid"})
    assert resp5.status_code == 400

    resp6 = client.get("/documents/search?q=   ")
    assert resp6.status_code == 400
