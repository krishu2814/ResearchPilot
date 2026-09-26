from app.agents.planner import planner_node
from app.agents.extractor import extractor_node, _split_into_meaningful_sentences
from app.agents.fact_checker import fact_checker_node
from app.agents.synthesizer import synthesizer_node


def test_planner_node():
    state = {"question": "Compare PostgreSQL and MongoDB"}
    output = planner_node(state)
    assert "sub_questions" in output
    assert len(output["sub_questions"]) == 3
    assert any("compare" in q.lower() or "architecture" in q.lower() for q in output["sub_questions"])

    # Empty question
    empty_out = planner_node({"question": ""})
    assert empty_out["sub_questions"] == []


def test_extractor_sentence_splitting():
    text = "PostgreSQL is an open-source database system. It supports both relational and non-relational queries. More info."
    sentences = _split_into_meaningful_sentences(text)
    assert len(sentences) >= 1
    assert all(s.endswith((".", "!", "?")) for s in sentences)


def test_extractor_node():
    state = {
        "search_results": [
            {
                "title": "PostgreSQL Overview",
                "url": "https://example.com/postgres",
                "snippet": "PostgreSQL is a powerful open source object-relational database system. It has earned a strong reputation for proven architecture and reliability.",
                "sub_question": "What is Postgres?"
            }
        ],
        "document_results": []
    }
    output = extractor_node(state)
    assert "evidence" in output
    evidence = output["evidence"]
    assert len(evidence) >= 1
    assert evidence[0]["source_type"] == "web"
    assert evidence[0]["source_title"] == "PostgreSQL Overview"


def test_fact_checker_node():
    state = {
        "search_results": [
            {
                "title": "PostgreSQL Overview",
                "url": "https://example.com/postgres",
                "snippet": "PostgreSQL is a powerful open source object-relational database system with high reliability."
            }
        ],
        "document_results": [],
        "evidence": [
            {
                "claim": "PostgreSQL is an open source database system with high reliability.",
                "source_type": "web",
                "source_title": "PostgreSQL Overview",
                "source_url_or_id": "https://example.com/postgres",
                "sub_question": "What is Postgres?"
            },
            {
                "claim": "Quantum teleportation is readily used for intergalactic spacecraft propulsion.",
                "source_type": "web",
                "source_title": "PostgreSQL Overview",
                "source_url_or_id": "https://example.com/postgres",
                "sub_question": "What is Postgres?"
            }
        ]
    }
    output = fact_checker_node(state)
    assert "verified_evidence" in output
    results = output["verified_evidence"]
    assert len(results) == 2
    assert results[0]["verdict"] in ("verified", "partial")
    assert results[1]["verdict"] == "unverified"


def test_synthesizer_node():
    state = {
        "question": "What is Python?",
        "sub_questions": ["What is Python used for?"],
        "search_results": [{"title": "Python Docs", "url": "https://python.org", "snippet": "Python is a high-level programming language."}],
        "document_results": [],
        "verified_evidence": [
            {
                "claim": "Python is a high-level programming language.",
                "source_type": "web",
                "source_title": "Python Docs",
                "source_url_or_id": "https://python.org",
                "sub_question": "What is Python used for?",
                "verdict": "verified",
                "confidence": 0.95,
                "rationale": "Directly grounded in documentation."
            }
        ]
    }
    output = synthesizer_node(state)
    assert "report" in output
    report = output["report"]
    assert "# 📑 Research Report: What is Python?" in report
    assert "Executive Summary" in report
    assert "Sources & Bibliography" in report
