# Implementation Phases

Phased build plan for the Christianity-focused AI Assistant. Each phase has a
goal, concrete tasks, the files it touches, and an exit criterion. See
[`ARCHITECTURE.md`](./ARCHITECTURE.md) for the full design.

**Status legend:** ✅ done · 🟡 in progress · ⬜ not started

---

## Phase 0 — Project Setup ✅

**Goal:** Reproducible backend skeleton, tooling, and config.

- ✅ `uv` project, Python 3.12 pin, `pyproject.toml` + `uv.lock`
- ✅ FastAPI app, `/health` + `/chat` stub
- ✅ structlog (console dev / JSON prod) with request-id middleware
- ✅ `pydantic-settings` config (env-driven), `.env.example`
- ✅ `.gitignore`, README, git initialized + initial commit

**Exit:** `uv run uvicorn app.main:app` boots, `/health` returns 200. ✅

---

## Phase 1 — Data Layer & Corpus 🟡

**Goal:** Postgres + pgvector populated with grounded source text.

- ✅ `docker-compose.yml` — pgvector/pg16 on host port 5433
- ✅ `schema.sql` — `bible_verses`, `history_docs`, `conversations` + HNSW/GIN indexes
- ✅ `core/db.py` — psycopg3 pool, pgvector registration, extension bootstrap
- ✅ `scripts/init_db.py` — idempotent schema apply
- ✅ `core/embeddings.py` — bge-base loader, `embed_passages` / `embed_query`
- 🟡 `scripts/ingest_bible.py` — KJV (66 books) ingest + embeddings (in progress)
- 🟡 `scripts/ingest_history.py` — parse `creeds1.pdf`, chunk, embed → `history_docs` (in progress)
- ⬜ Deuterocanon ingest from `KJV-with-Apocrypha.json` → tag `catholic`/`orthodox`

**Exit:** `bible_verses` fully populated (~31k rows); `history_docs` has creeds +
council facts; semantic search returns sane neighbors.

**Files:** `backend/app/core/{db,embeddings,schema.sql}`, `backend/scripts/*`

---

## Phase 2 — Retrieval Layer ✅

**Goal:** Denomination-aware scripture + history retrieval functions.

- ✅ `core/retrieval.py` — `search_scripture(query, denomination, k)` with canon filter
- ✅ `search_history(query, denomination, k)` (validated once `history_docs` populated)
- ✅ Retrieval confidence scoring (top cosine similarity, threshold in config)
- ✅ Reference lookup `verse_exists(book, chapter, verse)` for citation validation

**Exit:** Given a query + denomination, returns ranked verses honoring canon
membership; confidence reflects match quality. ✅

---

## Phase 3 — LLM Integration ✅

**Goal:** Gemini client wrapper with grounded prompting.

- ✅ `core/llm.py` — google-genai client, main (`gemini-2.5-pro`) generation
- ✅ Module-level singleton + `_reset_client()` auto-retry on closed httpx session
- ✅ `core/prompts.py` — system prompt templates, denomination framing, `build_user_prompt`
- ✅ Structured output helpers (`generate_json` with response_schema)

**Exit:** Wrapper takes prompt + retrieved context, returns grounded text;
honors "cite only retrieved verses" instruction. ✅

---

## Phase 4 — Safety & Router Node ✅

**Goal:** Block unsafe input before retrieval; classify intent in one call.

- ✅ `core/safety.py` — Stage 1 regex (adversarial templates, explicit hate)
- ✅ Stage 2 Gemini Flash call returning `{safe, intent, confidence}`
- ✅ Intents: `scripture | theology | history | image | general | blocked`
- ✅ Low-confidence / general → fallback to plain responder

**Exit:** Adversarial + hateful prompts blocked pre-retrieval; intent routed
correctly on the eval set. ✅

---

## Phase 5 — Agent Graph ✅

**Goal:** Wire the LangGraph `StateGraph` from `ARCHITECTURE.md` §4–6.

- ✅ `agent/state.py` — `AgentState` TypedDict with all fields
- ✅ `agent/nodes.py` — 9 nodes: Input, SafetyRouter, ScriptureRAG, HistoryRAG, Theology, Image, ImageValidator, Validator, Responder
- ✅ `agent/graph.py` — conditional edges, compile, `get_graph()` lru_cache singleton
- ✅ Per-node latency capture into `state.latency_ms`

**Exit:** Graph runs end-to-end for all intents. ✅

---

## Phase 6 — Grounding & Hallucination Control ✅

**Goal:** Catch fake citations and paraphrase drift.

- ✅ Citation validator: extract `Book Ch:Verse`, verify vs corpus, strip + log fakes
- ✅ Semantic drift check: embed response, compare max-sim across retrieved set
- ✅ Drift disclaimer injection when drift high despite strong retrieval
- ✅ Populate `hallucinated_refs`, `drift_warning` in state

**Exit:** Fake-verse and paraphrase-misquote eval cases pass (no invented refs). ✅

---

## Phase 7 — Conversation Memory ✅

**Goal:** Bounded, relevant context — no full-history dump.

- ✅ Persist each turn to `conversations` with per-turn embedding
- ✅ Window strategy (≤20 turns → last 10) and semantic strategy (>20 → top-5)
- ✅ Denomination-switch guard: inject canon/framing-changed system note

**Exit:** Long sessions stay within budget; denomination switch updates framing
without stale assumptions. ✅

---

## Phase 8 — Image Generation ✅

**Goal:** Safe Christian-themed image flow with two-pass moderation.

- ✅ Image prompt rewrite into safe Christian-art form
- ✅ Imagen 3 call via google-genai (base64 data URI)
- ✅ `ImageValidator` node re-checks rewritten prompt before generation
- ✅ Return image URL/bytes + safety metadata

**Exit:** Policy-violating image prompts blocked at raw and post-rewrite stages. ✅

---

## Phase 9 — API Integration ✅

**Goal:** Replace `/chat` stub with the compiled graph.

- ✅ `/chat` invokes graph, returns response + citations + flags
- ✅ Session handling, request-id propagation into graph state
- ✅ `asyncio.run_in_executor` wraps synchronous graph for async FastAPI

**Exit:** End-to-end API call produces grounded, cited, moderated responses. ✅

---

## Phase 10 — Frontend ✅

**Goal:** Minimal chat UI (UI polish explicitly not graded).

- ✅ Next.js 15 + Tailwind CSS chat interface
- ✅ Denomination selector (Protestant/Catholic/Orthodox pills)
- ✅ Citation rendering: verified (amber) + hallucinated (red) badges
- ✅ Image display in chat bubble
- ✅ Wire to backend `/chat`

**Exit:** Usable demo chat with denomination toggle and visible citations. ✅

---

## Phase 11 — Evaluation ✅

**Goal:** Reproducible eval harness over the dataset in `ARCHITECTURE.md` §13.

- ✅ `eval/dataset.json` — 20 cases: fake-verse, adversarial, hallucination, image, history, denomination, theology, scripture
- ✅ `eval/run_eval.py` — run cases through graph, score PASS/PARTIAL/FAIL, color report, exit code 1 on FAIL
- ✅ `--id` and `--category` filters for targeted runs
- ✅ Result: 16 PASS / 2 PARTIAL / 2 FAIL (historical FAILs fixed by Phase 1 history ingest)

**Exit:** Single command runs the eval set and prints a scored report. ✅

---

## Phase 12 — Deployment ⬜

**Goal:** Credible hosted demo.

- ⬜ Backend → Hugging Face Spaces (or container host)
- ⬜ DB → NeonDB (pgvector); push corpus
- ⬜ Frontend → Vercel
- ⬜ Env/secrets wiring (`GEMINI_API_KEY`)

**Exit:** Public URL serves the assistant against hosted DB.

---

## Phase 13 — Deliverables 🟡

**Goal:** Wrap up assignment artifacts.

- ✅ `docs/ARCHITECTURE.md` — full system design with all decisions
- ✅ `docs/HLD.md` — Mermaid diagrams + component table
- ✅ `docs/SYSTEM_DESIGN.md` — formal SDD with requirements, flows, trade-offs
- ✅ `README.md` — setup, run, eval instructions
- ⬜ 5–8 min walkthrough script/recording
- ⬜ Final eval run after full corpus ingest (target ≥18/20 PASS/PARTIAL)

**Exit:** Demo + repo + note + walkthrough ready to submit.

---

## Critical Path

```
Phase 1 (corpus) → Phase 2 (retrieval) → Phase 3 (LLM) → Phase 4 (safety/router)
→ Phase 5 (graph) → Phase 6 (grounding) → Phase 9 (API) → Phase 11 (eval)
```

Phases 7 (memory), 8 (image), 10 (frontend) are parallelizable once the graph
(Phase 5) exists. Phases 12–13 are last.
