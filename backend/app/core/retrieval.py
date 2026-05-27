"""Denomination-aware retrieval over scripture and history corpora.

Embeddings are normalized, so cosine similarity = 1 - (pgvector `<=>` distance).
Canon membership is enforced in SQL via the `@>` array-contains operator, so a
Protestant query never retrieves deuterocanonical verses.
"""

from pgvector.psycopg import Vector

from app.config import get_settings
from app.core.db import get_conn
from app.core.embeddings import embed_query
from app.logging_config import get_logger

log = get_logger(__name__)
_settings = get_settings()

_SCRIPTURE_SQL = """
    SELECT book, chapter, verse, text_kjv,
           1 - (embedding <=> %s) AS similarity
    FROM bible_verses
    WHERE denomination_canon @> ARRAY[%s]::varchar[]
      AND embedding IS NOT NULL
    ORDER BY embedding <=> %s
    LIMIT %s
"""

_HISTORY_SQL = """
    SELECT source, title, content,
           1 - (embedding <=> %s) AS similarity
    FROM history_docs
    WHERE denomination_scope @> ARRAY[%s]::varchar[]
      AND embedding IS NOT NULL
    ORDER BY embedding <=> %s
    LIMIT %s
"""


def search_scripture(
    query: str, denomination: str, k: int | None = None
) -> tuple[list[dict], float]:
    """Return (verses, retrieval_confidence). Confidence = top similarity."""
    k = k or _settings.rag_top_k
    vec = Vector(embed_query(query))
    with get_conn() as conn:
        rows = conn.execute(
            _SCRIPTURE_SQL, (vec, denomination, vec, k)
        ).fetchall()

    verses = [
        {
            "book": r[0],
            "chapter": r[1],
            "verse": r[2],
            "text": r[3],
            "ref": f"{r[0]} {r[1]}:{r[2]}",
            "similarity": float(r[4]),
        }
        for r in rows
    ]
    confidence = verses[0]["similarity"] if verses else 0.0
    log.info(
        "retrieval.scripture",
        denomination=denomination,
        k=k,
        hits=len(verses),
        confidence=round(confidence, 4),
    )
    return verses, confidence


def search_history(
    query: str, denomination: str, k: int | None = None
) -> tuple[list[dict], float]:
    """Return (history docs, retrieval_confidence) for non-scripture facts."""
    k = k or _settings.rag_top_k
    vec = Vector(embed_query(query))
    with get_conn() as conn:
        rows = conn.execute(
            _HISTORY_SQL, (vec, denomination, vec, k)
        ).fetchall()

    docs = [
        {
            "source": r[0],
            "title": r[1],
            "content": r[2],
            "similarity": float(r[3]),
        }
        for r in rows
    ]
    confidence = docs[0]["similarity"] if docs else 0.0
    log.info(
        "retrieval.history",
        denomination=denomination,
        k=k,
        hits=len(docs),
        confidence=round(confidence, 4),
    )
    return docs, confidence


def verse_exists(book: str, chapter: int, verse: int) -> bool:
    """Citation-validation primitive: does this exact reference exist?"""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT 1 FROM bible_verses "
            "WHERE lower(book) = lower(%s) AND chapter = %s AND verse = %s "
            "LIMIT 1",
            (book, chapter, verse),
        ).fetchone()
    return row is not None
