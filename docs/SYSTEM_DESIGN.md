# System Design Document (SDD)

**System:** Christianity-Focused AI Assistant
**Version:** 1.0
**Companion docs:** [`HLD.md`](./HLD.md), [`ARCHITECTURE.md`](./ARCHITECTURE.md), [`PHASES.md`](./PHASES.md)

---

## 1. Introduction

### 1.1 Scope
A full-stack AI assistant for Christianity-related Q&A, content, and image
generation. It grounds answers in a verified scripture and church-history
corpus, is aware of denominational differences (Catholic / Protestant /
Orthodox), and enforces safety and anti-hallucination controls as explicit
pipeline stages.

### 1.2 Goals
- Accurate, cited, scripture-grounded answers.
- No fabricated verses, references, or historical claims.
- Denomination-correct canon and framing.
- Robust refusal of adversarial, hateful, or manipulative requests.
- Safe Christian-themed image generation.

### 1.3 Non-Goals
- UI polish (explicitly not graded).
- Exhaustive multi-translation coverage (public-domain KJV/WEB + deuterocanon only).
- Real-time multi-user scale (single-instance demo target).

---

## 2. Requirements

### 2.1 Functional
| ID | Requirement |
| :-- | :-- |
| F1 | Answer Christianity questions grounded in retrieved scripture |
| F2 | Cite verses as `Book Chapter:Verse`, validated against the corpus |
| F3 | Generate Christian content (prayers, reflections, explanations) |
| F4 | Generate Christian-themed images via a safe prompt pipeline |
| F5 | Maintain conversation memory across turns |
| F6 | Apply denomination-aware canon, retrieval, and framing |
| F7 | Moderate input and output for safety |
| F8 | Detect and correct fake verses and paraphrase misquotes |
| F9 | Ground or abstain on non-scripture historical claims |
| F10 | Handle difficult/contested theology by naming the tradition |

### 2.2 Non-Functional
| ID | Requirement | Target |
| :-- | :-- | :-- |
| N1 | Text response latency | ~2.0–2.6 s |
| N2 | Image response latency | ~5–8 s |
| N3 | Observability | structured logs with request-id per request |
| N4 | Reproducibility | pinned deps (uv.lock), idempotent ingestion |
| N5 | Cost control | local embeddings, single combined safety+router call |
| N6 | Safety | adversarial/hate prompts blocked before generation |
| N7 | Data licensing | public-domain text only |

---

## 3. Architecture Overview

Layered, agent-orchestrated system. Requests enter FastAPI, run through a
LangGraph state machine (safety → routing → retrieval → generation →
validation → response), backed by PostgreSQL + pgvector and Gemini APIs. See
[`HLD.md`](./HLD.md) §2–4 for context and flow diagrams.

---

## 4. Component Design

### 4.1 Backend API (`app/main.py`, `app/api/routes.py`)
- FastAPI app, lifespan-managed.
- Middleware binds `request_id` to structlog contextvars for the request.
- Endpoints: `GET /health`, `POST /chat` (graph invocation — Phase 9).
- Interface: `ChatRequest{session_id, message, denomination}` →
  `ChatResponse{session_id, response, citations[], flagged}`.

### 4.2 Configuration (`app/config.py`)
- `pydantic-settings`, env-driven, `lru_cache` singleton.
- Holds model names, DB URL, thresholds (rag_top_k, retrieval/drift), memory params.

### 4.3 Logging (`app/logging_config.py`)
- structlog: console renderer (dev) / JSON (prod), level + format from config.
- contextvars merge → request-id appears on every line.

### 4.4 Data Layer (`app/core/db.py`, `schema.sql`)
- psycopg3 `ConnectionPool`; pgvector registered per connection.
- One-time extension bootstrap before pool open (avoids CREATE EXTENSION race).
- Schema: `bible_verses`, `history_docs`, `conversations`; HNSW (vectors) + GIN (canon).

### 4.5 Embeddings (`app/core/embeddings.py`)
- bge-base-en-v1.5 via sentence-transformers, lazy-loaded singleton.
- `embed_passages` (corpus, no instruction) / `embed_query` (retrieval instruction).
- Normalized vectors → cosine = dot product.

### 4.6 Retrieval (`app/core/retrieval.py`)
- `search_scripture` / `search_history`: cosine search, canon filter in SQL (`@>`),
  returns rows + top-similarity confidence.
- `verse_exists(book, chapter, verse)`: citation-validation primitive.

### 4.7 LLM (`app/core/llm.py` — Phase 3)
- google-genai client; Gemini Pro for generation, Flash for classification.
- Prompt templates enforce retrieval-first citing + denomination framing.

### 4.8 Safety + Router (`app/core/safety.py` — Phase 4)
- Stage 1 regex; Stage 2 Flash returns `{safe, intent, confidence}`.

### 4.9 Agent Graph (`app/agent/*` — Phase 5)
- `AgentState` TypedDict; nodes for input, safety+router, scripture/history RAG,
  theology, image, image-validator, validator, responder; conditional edges.

### 4.10 Image (Phase 8)
- Prompt rewrite → Imagen 3 → post-rewrite re-validation node.

---

## 5. Data Design

### 5.1 Entities
- **bible_verses** — `(book, chapter, verse)` unique; `text_kjv`, `text_web`,
  `denomination_canon[]`, `embedding VECTOR(768)`.
- **history_docs** — `source`, `title`, `content`, `denomination_scope[]`, `embedding`.
- **conversations** — `session_id`, `role`, `content`, `denomination`,
  `embedding` (semantic memory), `created_at`.

### 5.2 Indexes
- HNSW `vector_cosine_ops` on all embedding columns (static corpora, recall-first).
- GIN on `denomination_canon` / `denomination_scope`.
- Btree on `(book, chapter, verse)` and `(session_id, created_at)`.

### 5.3 Canon model
All 66 KJV books tagged `{protestant, catholic, orthodox}`. Deuterocanon (from
`KJV-with-Apocrypha.json`) tagged `{catholic, orthodox}` only. Retrieval filters
by the active denomination so canon scope is enforced at the data layer.

---

## 6. Key Flows

### 6.1 Grounded text answer
input → regex/Flash safety+intent → (scripture|history|theology) retrieval →
Gemini generation with injected context → citation validation + drift check →
responder formats cited answer.

### 6.2 Fake-verse handling
Query references `John 4:99` → retrieval finds no such verse / model instructed
not to invent → citation validator confirms non-existence → response states the
verse does not exist.

### 6.3 Historical claim
"Council of Nicaea in 200 AD" → history RAG retrieves council facts (325 AD) →
model corrects date or, if low retrieval confidence, abstains.

### 6.4 Image generation
prompt → pre-routing safety → rewrite to safe Christian-art form →
ImageValidator re-checks rewritten prompt → Imagen 3 → return with metadata.

### 6.5 Memory
≤20 turns: load last 10 (window). >20: embed query, fetch top-5 past turns
(semantic). Denomination switch injects a framing-changed system note.

---

## 7. Cross-Cutting Concerns

### 7.1 Safety
Defense in depth across seven layers (see [`HLD.md`](./HLD.md) §6). Safety runs
before retrieval/generation; image path is double-moderated.

### 7.2 Hallucination control
Retrieval-first prompting + citation regex validation + semantic drift check +
separate history grounding. Fakes are stripped and logged in `hallucinated_refs`.

### 7.3 Observability
Per-request `request_id`, per-node latency in `state.latency_ms`, structured
JSON logs in prod. Supports the evaluation rubric's logging signal.

### 7.4 Configuration & secrets
Env-driven; `GEMINI_API_KEY` never committed; `.env` gitignored.

---

## 8. Reliability & Scalability

- **Stateless backend** — session state lives in Postgres; horizontally scalable.
- **Connection pooling** — psycopg3 pool (1–10) bounds DB connections.
- **Static corpora** — embeddings precomputed offline; query-time cost = 1 embed + 1 vector search.
- **Bottlenecks** — Gemini generation (~2 s) and Imagen (~3–5 s) dominate latency; embedding is local and cheap.
- **Failure modes** — Gemini error → safe fallback message; retrieval empty → abstain; image unsafe → block.

---

## 9. Trade-offs & Alternatives

| Decision | Chosen | Alternative | Why |
| :-- | :-- | :-- | :-- |
| Vector store | pgvector in Postgres | dedicated vector DB | small corpus, less ops |
| Embeddings | local bge-base | hosted embedding API | free, no rate limits for bulk |
| Safety+Router | one Flash call | separate calls | fewer round-trips, lower cost |
| LLM | Gemini Pro/Flash | open HF model | quality + simplicity for this build |
| Bible source | structured JSON | PDF | reliable verse-level parsing |

---

## 10. Risks & Mitigations

| Risk | Mitigation |
| :-- | :-- |
| Paraphrase hallucination (correct ref, wrong wording) | semantic drift check vs retrieved set |
| Post-rewrite unsafe image | second validation node after rewrite |
| Stale denomination framing after switch | memory denomination guard |
| Non-scripture fabrication | history corpus + abstain on low confidence |
| Copyright exposure | public-domain text only (KJV/WEB + KJV Apocrypha) |
| Embedding cost/latency on free tier | local model, corpus precomputed offline |

---

## 11. Open Items / Future Work

- Deuterocanon ingest + canon-scoped retrieval validation (Catholic/Orthodox).
- History corpus ingestion from `creeds1.pdf` + council sources.
- Evaluation harness with scored PASS/PARTIAL/FAIL over the dataset.
- Frontend, deployment, and walkthrough (Phases 10, 12, 13).
