"""Apply the database schema. Idempotent.

Usage:
    docker compose up -d            # from repo root, start postgres
    uv run python -m scripts.init_db
"""

from app.core.db import close_pool, get_conn, init_schema
from app.logging_config import configure_logging, get_logger

configure_logging()
log = get_logger(__name__)


def main() -> None:
    init_schema()
    with get_conn() as conn:
        tables = conn.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'public' ORDER BY table_name"
        ).fetchall()
        ext = conn.execute(
            "SELECT extname FROM pg_extension ORDER BY extname"
        ).fetchall()
    log.info(
        "init_db.done",
        tables=[t[0] for t in tables],
        extensions=[e[0] for e in ext],
    )
    close_pool()


if __name__ == "__main__":
    main()
