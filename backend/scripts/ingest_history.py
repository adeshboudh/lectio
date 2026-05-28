"""Ingest church history documents into history_docs table.

Parses creeds1.pdf (CCEL public-domain), splits into ~400-token chunks,
embeds with bge-base, and upserts into Postgres.

Usage:
    docker compose up -d
    uv run python -m scripts.init_db
    uv run python -m scripts.ingest_history
"""

import re
from pathlib import Path

from pypdf import PdfReader

from app.core.db import close_pool, get_conn
from app.core.embeddings import embed_passages
from app.logging_config import configure_logging, get_logger

configure_logging()
log = get_logger(__name__)

ASSETS_DIR = Path(__file__).parents[2] / "assets"
CREEDS_PDF = ASSETS_DIR / "creeds1.pdf"
CHUNK_TOKENS = 400          # ~target chunk size in whitespace-split words
CHUNK_OVERLAP = 50          # words overlapping between adjacent chunks
ALL_SCOPES = ["protestant", "catholic", "orthodox"]

INSERT_SQL = """
    INSERT INTO history_docs
        (source, title, content, denomination_scope, embedding)
    VALUES (%s, %s, %s, %s, %s)
"""

# ---------------------------------------------------------------------------
# Known section headings inside the Creeds / Councils PDF so we can tag source
# ---------------------------------------------------------------------------
SECTION_MARKERS = [
    ("Apostles' Creed",             "Apostles' Creed (traditional)"),
    ("Nicene Creed",                "Nicene Creed (Council of Nicaea, 325 AD)"),
    ("Athanasian Creed",            "Athanasian Creed (c. 500 AD)"),
    ("Chalcedonian Definition",     "Council of Chalcedon (451 AD)"),
    ("Council of Nicaea",           "Council of Nicaea (325 AD)"),
    ("Council of Constantinople",   "First Council of Constantinople (381 AD)"),
    ("Council of Ephesus",          "Council of Ephesus (431 AD)"),
    ("Westminster Confession",      "Westminster Confession of Faith (1646)"),
    ("Heidelberg Catechism",        "Heidelberg Catechism (1563)"),
    ("Belgic Confession",           "Belgic Confession (1561)"),
    ("Canons of Dort",              "Canons of Dort (1619)"),
    ("Thirty-Nine Articles",        "Thirty-Nine Articles (1563)"),
    ("Council of Trent",            "Council of Trent (1545-1563)"),
    ("Baltimore Catechism",         "Baltimore Catechism (1885)"),
    ("Augsburg Confession",         "Augsburg Confession (1530)"),
]


def _extract_text(path: Path) -> str:
    reader = PdfReader(str(path))
    pages = []
    for page in reader.pages:
        text = page.extract_text() or ""
        pages.append(text)
    return "\n".join(pages)


def _clean(text: str) -> str:
    """Collapse runs of whitespace/newlines, remove page artefacts."""
    text = re.sub(r"\f", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _detect_source(text_window: str) -> str:
    """Return best matching source label for a text window."""
    for marker, label in SECTION_MARKERS:
        if marker.lower() in text_window.lower():
            return label
    return "Church History / Creeds (CCEL)"


def _chunk_text(text: str, chunk_size: int, overlap: int) -> list[dict]:
    """Split text into overlapping word-count chunks with source detection."""
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        window = " ".join(words[start:end])
        # Detect source from a slightly wider window for context
        context_start = max(0, start - 100)
        context_window = " ".join(words[context_start:end])
        source = _detect_source(context_window)
        chunks.append({"text": window, "source": source})
        if end == len(words):
            break
        start += chunk_size - overlap
    return chunks


def main() -> None:
    if not CREEDS_PDF.exists():
        raise SystemExit(f"PDF not found: {CREEDS_PDF}")

    log.info("ingest_history.extract", path=str(CREEDS_PDF))
    raw = _extract_text(CREEDS_PDF)
    text = _clean(raw)
    log.info("ingest_history.text_extracted", chars=len(text))

    chunks = _chunk_text(text, CHUNK_TOKENS, CHUNK_OVERLAP)
    log.info("ingest_history.chunks", count=len(chunks))

    BATCH = 64
    inserted = 0
    with get_conn() as conn:
        conn.execute("TRUNCATE TABLE history_docs")
        conn.commit()
        log.info("ingest_history.truncated")

        for i in range(0, len(chunks), BATCH):
            batch = chunks[i : i + BATCH]
            texts = [c["text"] for c in batch]
            vectors = embed_passages(texts)
            params = [
                (
                    c["source"],
                    c["source"],
                    c["text"],
                    ALL_SCOPES,
                    vec,
                )
                for c, vec in zip(batch, vectors, strict=True)
            ]
            with conn.cursor() as cur:
                cur.executemany(INSERT_SQL, params)
            conn.commit()
            inserted += len(batch)
            log.info("ingest_history.progress", done=inserted, total=len(chunks))

    with get_conn() as conn:
        count = conn.execute("SELECT count(*) FROM history_docs").fetchone()[0]
    log.info("ingest_history.done", rows_in_table=count)
    close_pool()


if __name__ == "__main__":
    main()
