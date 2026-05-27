from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import psycopg
from pgvector.psycopg import register_vector
from psycopg_pool import ConnectionPool

from app.config import get_settings
from app.logging_config import get_logger

log = get_logger(__name__)
_settings = get_settings()

SCHEMA_PATH = Path(__file__).parent / "schema.sql"

_pool: ConnectionPool | None = None


def _configure(conn: psycopg.Connection) -> None:
    """Register pgvector adapters on every pooled connection.

    The vector extension is guaranteed to exist by _bootstrap_extensions(),
    run once before the pool opens, so register_vector can introspect the type.
    """
    register_vector(conn)


def _bootstrap_extensions() -> None:
    """Create required extensions once, on a standalone connection.

    Done before the pool opens so per-connection configure() does not race
    on CREATE EXTENSION across concurrently-opened connections.
    """
    with psycopg.connect(_settings.database_url) as conn:
        conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
        conn.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
        conn.commit()


def get_pool() -> ConnectionPool:
    global _pool
    if _pool is None:
        log.info("db.pool.init", dsn=_redact(_settings.database_url))
        _bootstrap_extensions()
        _pool = ConnectionPool(
            conninfo=_settings.database_url,
            min_size=1,
            max_size=10,
            configure=_configure,
            open=True,
        )
    return _pool


@contextmanager
def get_conn() -> Iterator[psycopg.Connection]:
    with get_pool().connection() as conn:
        yield conn


def close_pool() -> None:
    global _pool
    if _pool is not None:
        _pool.close()
        _pool = None
        log.info("db.pool.closed")


def init_schema() -> None:
    """Apply schema.sql (idempotent — uses IF NOT EXISTS throughout)."""
    sql = SCHEMA_PATH.read_text()
    with get_conn() as conn:
        conn.execute(sql)
        conn.commit()
    log.info("db.schema.applied", path=str(SCHEMA_PATH))


def _redact(dsn: str) -> str:
    if "@" in dsn and "://" in dsn:
        scheme, rest = dsn.split("://", 1)
        if "@" in rest:
            return f"{scheme}://***@{rest.split('@', 1)[1]}"
    return dsn
