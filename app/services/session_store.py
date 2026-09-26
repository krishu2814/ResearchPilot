"""
Session Store Service for ResearchPilot (Phase 9).

This service manages SQLite persistence for research sessions.
It stores research queries, full multi-agent graph states, and
synthesized reports so they can be reviewed, resumed, or audited later.

We use Python's built-in sqlite3 library — no external database
servers or complex ORM setups required!
"""

import json
import os
import sqlite3
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any


DEFAULT_DB_DIR = "data"
DEFAULT_DB_PATH = os.path.join(DEFAULT_DB_DIR, "research_sessions.db")


# -----------------------------------------------------------------------------
# 1. Database Connection & Initialization
# -----------------------------------------------------------------------------
def get_connection(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """
    Creates and returns a connection to the SQLite database.
    Configures sqlite3.Row so we can access columns by name like a dictionary.
    """
    db_dir = os.path.dirname(db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str = DEFAULT_DB_PATH) -> None:
    """
    Initializes the SQLite database and creates the research_sessions table.
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS research_sessions (
            session_id TEXT PRIMARY KEY,
            query TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            sub_questions_json TEXT NOT NULL,
            search_results_json TEXT NOT NULL,
            document_results_json TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            verified_evidence_json TEXT NOT NULL,
            report TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()
    print(f"[Session Store] Database initialized at: {db_path}")


# -----------------------------------------------------------------------------
# 2. Save Session
# -----------------------------------------------------------------------------
def save_session(
    session_id: str,
    query: str,
    state: Dict[str, Any],
    status: str = "researched",
    db_path: str = DEFAULT_DB_PATH
) -> None:
    """
    Inserts or updates a research session and its full multi-agent state.
    """
    init_db(db_path)

    created_at = datetime.now(timezone.utc).isoformat()
    sub_questions_json = json.dumps(state.get("sub_questions", []))
    search_results_json = json.dumps(state.get("search_results", []))
    document_results_json = json.dumps(state.get("document_results", []))
    evidence_json = json.dumps(state.get("evidence", []))
    verified_evidence_json = json.dumps(state.get("verified_evidence", []))
    report = state.get("report", "")

    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR REPLACE INTO research_sessions (
            session_id,
            query,
            status,
            created_at,
            sub_questions_json,
            search_results_json,
            document_results_json,
            evidence_json,
            verified_evidence_json,
            report
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        session_id,
        query,
        status,
        created_at,
        sub_questions_json,
        search_results_json,
        document_results_json,
        evidence_json,
        verified_evidence_json,
        report
    ))

    conn.commit()
    conn.close()
    print(f"[Session Store] Saved session: '{session_id}' ({query})")


# -----------------------------------------------------------------------------
# 3. Retrieve Session
# -----------------------------------------------------------------------------
def get_session(session_id: str, db_path: str = DEFAULT_DB_PATH) -> Optional[Dict[str, Any]]:
    """
    Retrieves a single research session by its session_id.
    Deserializes stored JSON state back into native Python lists and dicts.
    """
    init_db(db_path)

    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM research_sessions WHERE session_id = ?
    """, (session_id,))

    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "session_id": row["session_id"],
        "query": row["query"],
        "status": row["status"],
        "created_at": row["created_at"],
        "sub_questions": json.loads(row["sub_questions_json"] or "[]"),
        "search_results": json.loads(row["search_results_json"] or "[]"),
        "document_results": json.loads(row["document_results_json"] or "[]"),
        "evidence": json.loads(row["evidence_json"] or "[]"),
        "verified_evidence": json.loads(row["verified_evidence_json"] or "[]"),
        "report": row["report"] or ""
    }


# -----------------------------------------------------------------------------
# 4. List All Sessions
# -----------------------------------------------------------------------------
def list_sessions(limit: int = 50, db_path: str = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """
    Lists past research sessions in reverse chronological order (newest first).
    Returns lightweight summary records.
    """
    init_db(db_path)

    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            session_id,
            query,
            status,
            created_at,
            sub_questions_json,
            search_results_json,
            document_results_json,
            verified_evidence_json,
            LENGTH(report) as report_length
        FROM research_sessions
        ORDER BY created_at DESC
        LIMIT ?
    """, (limit,))

    rows = cursor.fetchall()
    conn.close()

    sessions = []
    for row in rows:
        sub_questions = json.loads(row["sub_questions_json"] or "[]")
        search_results = json.loads(row["search_results_json"] or "[]")
        document_results = json.loads(row["document_results_json"] or "[]")
        verified_evidence = json.loads(row["verified_evidence_json"] or "[]")

        sessions.append({
            "session_id": row["session_id"],
            "query": row["query"],
            "status": row["status"],
            "created_at": row["created_at"],
            "num_sub_questions": len(sub_questions),
            "num_sources": len(search_results) + len(document_results),
            "num_verified_claims": len(verified_evidence),
            "report_length": row["report_length"] or 0
        })

    return sessions


# -----------------------------------------------------------------------------
# 5. Delete Session
# -----------------------------------------------------------------------------
def delete_session(session_id: str, db_path: str = DEFAULT_DB_PATH) -> bool:
    """
    Deletes a session by session_id.
    Returns True if a record was deleted, False if not found.
    """
    init_db(db_path)

    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM research_sessions WHERE session_id = ?
    """, (session_id,))

    deleted_count = cursor.rowcount
    conn.commit()
    conn.close()

    return deleted_count > 0
