-- Christianity AI Assistant — database schema
-- Single Postgres + pgvector instance: vector search + relational storage.
-- Embedding dim 768 (bge-base-en-v1.5). All scripture/history text is public domain.

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ---------------------------------------------------------------------------
-- bible_verses: public-domain scripture, canon-tagged for denomination filter
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS bible_verses (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    book                VARCHAR        NOT NULL,
    chapter             INTEGER        NOT NULL,
    verse               INTEGER        NOT NULL,
    text_kjv            TEXT,
    text_web            TEXT,
    denomination_canon  VARCHAR[]      NOT NULL,  -- {protestant,catholic,orthodox}
    embedding           VECTOR(768),
    UNIQUE (book, chapter, verse)
);

CREATE INDEX IF NOT EXISTS bible_verses_embedding_hnsw
    ON bible_verses USING hnsw (embedding vector_cosine_ops);

CREATE INDEX IF NOT EXISTS bible_verses_canon_gin
    ON bible_verses USING gin (denomination_canon);

CREATE INDEX IF NOT EXISTS bible_verses_ref
    ON bible_verses (book, chapter, verse);

-- ---------------------------------------------------------------------------
-- history_docs: councils, creeds, catechism, church history (public domain)
-- grounds non-scripture factual claims so they are not answered from memory
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS history_docs (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source              VARCHAR        NOT NULL,  -- e.g. "Council of Nicaea 325"
    title               VARCHAR        NOT NULL,
    content             TEXT           NOT NULL,
    denomination_scope  VARCHAR[]      NOT NULL,
    embedding           VECTOR(768)
);

CREATE INDEX IF NOT EXISTS history_docs_embedding_hnsw
    ON history_docs USING hnsw (embedding vector_cosine_ops);

CREATE INDEX IF NOT EXISTS history_docs_scope_gin
    ON history_docs USING gin (denomination_scope);

-- ---------------------------------------------------------------------------
-- conversations: per-turn memory; embedding enables semantic history recall
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS conversations (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id    VARCHAR        NOT NULL,
    role          VARCHAR        NOT NULL,  -- user | assistant
    content       TEXT           NOT NULL,
    denomination  VARCHAR        NOT NULL,
    embedding     VECTOR(768),
    created_at    TIMESTAMPTZ    NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS conversations_session_time
    ON conversations (session_id, created_at);

CREATE INDEX IF NOT EXISTS conversations_embedding_hnsw
    ON conversations USING hnsw (embedding vector_cosine_ops);
