"""Conversation memory: persist turns, load via window or semantic retrieval.

Strategy selection:
  session has ≤ SEMANTIC_SWITCH_AT turns → sliding window (last WINDOW_TURNS)
  session exceeds SEMANTIC_SWITCH_AT     → semantic: embed query, top-k past turns

Denomination switch mid-session injects a system note so stale framing
assumptions are not carried forward.
"""

from pgvector.psycopg import Vector

from app.config import get_settings
from app.core.db import get_conn
from app.core.embeddings import embed_passages, embed_query
from app.logging_config import get_logger

log = get_logger(__name__)
_s = get_settings()

_INSERT = """
    INSERT INTO conversations (session_id, role, content, denomination, embedding)
    VALUES (%s, %s, %s, %s, %s)
"""

_COUNT = """
    SELECT count(*) FROM conversations WHERE session_id = %s
"""

_WINDOW = """
    SELECT role, content, denomination FROM conversations
    WHERE session_id = %s
    ORDER BY created_at DESC
    LIMIT %s
"""

_SEMANTIC = """
    SELECT role, content, denomination,
           1 - (embedding <=> %s) AS similarity
    FROM conversations
    WHERE session_id = %s
      AND embedding IS NOT NULL
    ORDER BY embedding <=> %s
    LIMIT %s
"""

_LAST_DENOMINATION = """
    SELECT denomination FROM conversations
    WHERE session_id = %s
    ORDER BY created_at DESC
    LIMIT 1
"""


def save_turn(session_id: str, role: str, content: str, denomination: str) -> None:
    """Persist one turn with embedding."""
    vec = Vector(embed_passages([content])[0])
    with get_conn() as conn:
        conn.execute(_INSERT, (session_id, role, content, denomination, vec))
        conn.commit()


def load_memory(
    session_id: str, query: str, current_denomination: str
) -> tuple[list[dict], str, str]:
    """Return (turns, strategy_used, denomination_guard_note).

    turns: list of {role, content} dicts ready to inject into prompt.
    strategy_used: 'window' | 'semantic'
    denomination_guard_note: non-empty string when denomination changed mid-session.
    """
    with get_conn() as conn:
        total: int = conn.execute(_COUNT, (session_id,)).fetchone()[0]

        # Denomination switch guard
        guard_note = ""
        if total > 0:
            prev_denom = conn.execute(
                _LAST_DENOMINATION, (session_id,)
            ).fetchone()
            if prev_denom and prev_denom[0] != current_denomination:
                guard_note = (
                    f"[System: the user has switched from {prev_denom[0]} to "
                    f"{current_denomination} tradition. Update canon and framing accordingly.]"
                )

        if total <= _s.memory_semantic_switch_at:
            rows = conn.execute(
                _WINDOW, (session_id, _s.memory_window_turns)
            ).fetchall()
            turns = [{"role": r[0], "content": r[1]} for r in reversed(rows)]
            strategy = "window"
        else:
            vec = Vector(embed_query(query))
            rows = conn.execute(
                _SEMANTIC, (vec, session_id, vec, _s.rag_top_k)
            ).fetchall()
            turns = [{"role": r[0], "content": r[1]} for r in rows]
            strategy = "semantic"

    log.info(
        "memory.loaded",
        session_id=session_id,
        total_turns=total,
        loaded=len(turns),
        strategy=strategy,
        denom_switched=bool(guard_note),
    )
    return turns, strategy, guard_note
