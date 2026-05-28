# Christianity AI Assistant

Grounded, denomination-aware Christianity Q&A assistant built for the SoluLab technical assessment.

## Architecture at a Glance

```
User → FastAPI → LangGraph Agent → pgvector RAG → Gemini Pro (grounded)
                      ↓
             Safety Router (regex + Gemini Flash)
                      ↓
             Citation Validator + Semantic Drift Check
                      ↓
             Image Generator (Imagen 3) — if image intent
                      ↓
             Conversation Memory (window/semantic)
```

Full design: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | HLD: [`docs/HLD.md`](docs/HLD.md)

## Features

| Feature | Implementation |
| :-- | :-- |
| Scripture RAG | pgvector HNSW cosine, bge-base-en-v1.5 embeddings, KJV+WEB corpus |
| Denomination awareness | Protestant / Catholic / Orthodox canon filtering via `@>` SQL |
| Hallucination prevention | Citation validator (regex → `verse_exists()`) + semantic drift check |
| Safety moderation | Two-stage: regex (0ms) + Gemini Flash classifier |
| Image generation | Imagen 3 with pre/post rewrite safety validation |
| Conversation memory | Window (≤10 turns) or semantic (>10), denomination-switch guard |
| Evaluation harness | 20-case PASS/PARTIAL/FAIL suite with category grouping |

## Stack

| Concern | Choice |
| :-- | :-- |
| Backend | Python 3.12, FastAPI, uvicorn |
| Agent | LangGraph StateGraph |
| LLM | Gemini 2.5 Pro (grounded gen) + 2.5 Flash (safety/router) |
| Embeddings | `BAAI/bge-base-en-v1.5` (local, sentence-transformers) |
| Data | PostgreSQL 16 + pgvector |
| Images | Imagen 3 (google-genai) |
| Frontend | Next.js 15, Tailwind CSS |
| Logging | structlog |
| Package mgr | uv |

## Quick Start

### Prerequisites

- Docker + Docker Compose
- Python 3.12 (via `uv`)
- Node 20+
- Gemini API key (set in `backend/.env`)

### 1. Start the database

```bash
docker compose up -d
```

### 2. Backend setup

```bash
cd backend
cp .env.example .env          # add GEMINI_API_KEY
uv sync
uv run python -m scripts.init_db
uv run python -m scripts.ingest_bible    # ~30 min, embeds 31k KJV verses
uv run python -m scripts.ingest_history  # ~5 min, embeds creed/council chunks
uv run uvicorn app.main:app --reload
```

### 3. Frontend setup

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`.

### 4. Run evaluation

```bash
cd backend
uv run python ../eval/run_eval.py
```

Expected: ≥18/20 PASS/PARTIAL (2 historical cases require history_docs ingest).

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── agent/          # LangGraph graph, nodes, state
│   │   ├── api/            # FastAPI routes
│   │   └── core/           # db, embeddings, llm, retrieval, safety, memory, image
│   └── scripts/
│       ├── init_db.py      # schema init
│       ├── ingest_bible.py # KJV verse embeddings
│       └── ingest_history.py # creed/council document embeddings
├── eval/
│   ├── dataset.json        # 20 eval cases
│   └── run_eval.py         # harness with PASS/PARTIAL/FAIL scoring
├── frontend/
│   ├── app/page.tsx        # chat UI
│   └── components/         # DenominationSelector, CitationBadge, MessageBubble
├── docs/
│   ├── ARCHITECTURE.md
│   ├── HLD.md
│   ├── PHASES.md
│   └── SYSTEM_DESIGN.md
└── docker-compose.yml
```

## Evaluation Categories

| Category | Cases | What it tests |
| :-- | :-- | :-- |
| adversarial | 5 | Jailbreak, rewrite, extremism — must be flagged + blocked |
| fake_verse | 2 | Non-existent references — must detect, not hallucinate |
| hallucination | 2 | Common misquotes + topics not in scripture |
| image_safety | 3 | Imagen safety pre/post rewrite + policy block |
| historical | 3 | Council dates, creed attribution |
| denomination | 2 | Catholic vs Protestant framing (purgatory, papal infallibility) |
| theology | 2 | Predestination paradox, resurrection significance |
| scripture | 1 | Normal retrieval with citation verification |

## Key Design Decisions

**Retrieval-first grounding** — System prompt forbids citing anything outside the injected context block. Hallucinated refs are detected post-generation and stripped before the response reaches the user.

**Two-stage safety** — Regex catches obvious violations in <1ms. Gemini Flash handles nuanced manipulation attempts. Either stage can block.

**Public-domain corpus only** — KJV and WEB translations avoid copyright. NIV/ESV are not used.

**Denomination filtering** — Each denomination has an associated canon list. Queries filter `denomination_canon @> ARRAY[denomination]` so Orthodox/Catholic users see deuterocanon results.
