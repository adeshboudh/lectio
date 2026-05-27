"""Ingest the KJV Bible (aruljohn per-book JSON) into bible_verses.

Reads assets/Bible-kjv-master/*.json, embeds each verse with bge-base, and
upserts into Postgres. Idempotent via ON CONFLICT (book, chapter, verse).

All 66 KJV books belong to every canon, so denomination_canon is tagged
{protestant, catholic, orthodox}. Deuterocanon is a separate later pass.

Usage:
    docker compose up -d
    uv run python -m scripts.init_db
    uv run python -m scripts.ingest_bible
"""

import json
from pathlib import Path

from app.core.db import close_pool, get_conn
from app.core.embeddings import embed_passages
from app.logging_config import configure_logging, get_logger

configure_logging()
log = get_logger(__name__)

ASSETS_DIR = Path(__file__).parents[2] / "assets" / "Bible-kjv-master"
ALL_CANONS = ["protestant", "catholic", "orthodox"]
BATCH = 256

UPSERT = """
    INSERT INTO bible_verses
        (book, chapter, verse, text_kjv, denomination_canon, embedding)
    VALUES (%s, %s, %s, %s, %s, %s)
    ON CONFLICT (book, chapter, verse) DO UPDATE
        SET text_kjv = EXCLUDED.text_kjv,
            denomination_canon = EXCLUDED.denomination_canon,
            embedding = EXCLUDED.embedding
"""


def load_verses() -> list[dict]:
    """Flatten all per-book JSON files into verse rows (no embeddings yet)."""
    rows: list[dict] = []
    for path in sorted(ASSETS_DIR.glob("*.json")):
        if path.name == "Books.json":
            continue
        data = json.loads(path.read_text())
        book = data["book"]
        for ch in data["chapters"]:
            chapter = int(ch["chapter"])
            for v in ch["verses"]:
                rows.append(
                    {
                        "book": book,
                        "chapter": chapter,
                        "verse": int(v["verse"]),
                        "text": v["text"],
                    }
                )
    return rows


def main() -> None:
    if not ASSETS_DIR.exists():
        raise SystemExit(f"KJV assets not found at {ASSETS_DIR}")

    rows = load_verses()
    log.info("ingest.loaded", verses=len(rows))

    inserted = 0
    with get_conn() as conn:
        for i in range(0, len(rows), BATCH):
            chunk = rows[i : i + BATCH]
            vectors = embed_passages([r["text"] for r in chunk])
            params = [
                (r["book"], r["chapter"], r["verse"], r["text"], ALL_CANONS, vec)
                for r, vec in zip(chunk, vectors, strict=True)
            ]
            with conn.cursor() as cur:
                cur.executemany(UPSERT, params)
            conn.commit()
            inserted += len(chunk)
            log.info("ingest.progress", done=inserted, total=len(rows))

    with get_conn() as conn:
        count = conn.execute("SELECT count(*) FROM bible_verses").fetchone()[0]
    log.info("ingest.done", rows_in_table=count)
    close_pool()


if __name__ == "__main__":
    main()
