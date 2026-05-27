from functools import lru_cache

from sentence_transformers import SentenceTransformer

from app.config import get_settings
from app.logging_config import get_logger

log = get_logger(__name__)
_settings = get_settings()

# bge-base-en-v1.5 retrieval instruction: prepend to QUERIES only, not passages.
_QUERY_INSTRUCTION = "Represent this sentence for searching relevant passages: "


@lru_cache
def _model() -> SentenceTransformer:
    log.info("embeddings.load", model=_settings.embedding_model)
    return SentenceTransformer(_settings.embedding_model)


def embed_passages(texts: list[str], batch_size: int = 128) -> list[list[float]]:
    """Embed corpus passages (no instruction prefix). Normalized for cosine."""
    vecs = _model().encode(
        texts,
        batch_size=batch_size,
        normalize_embeddings=True,
        show_progress_bar=False,
        convert_to_numpy=True,
    )
    return vecs.tolist()


def embed_query(text: str) -> list[float]:
    """Embed a single search query with the bge retrieval instruction."""
    vec = _model().encode(
        _QUERY_INSTRUCTION + text,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )
    return vec.tolist()
