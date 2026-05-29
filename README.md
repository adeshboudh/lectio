# Lectio — Scripture Companion

Grounded, denomination-aware Christianity AI assistant built for the SoluLab technical assessment.

## Architecture at a Glance

```
User → FastAPI → LangGraph Agent → pgvector RAG → Gemini Pro (grounded)
                      ↓
             Safety Router (regex + Gemini Flash)
                      ↓
             Citation Validator + Semantic Drift Check
                      ↓
             Image Generator (FLUX.1-dev via NVIDIA) — if image intent
                      ↓
             Conversation Memory (window/semantic)
```

Full design: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | HLD: [`docs/HLD.md`](docs/HLD.md)

## Features

| Feature | Implementation |
| :-- | :-- |
| Scripture RAG | pgvector HNSW cosine, bge-base-en-v1.5 embeddings, KJV corpus |
| Denomination awareness | Protestant / Catholic / Orthodox canon filtering via `@>` SQL |
| Hallucination prevention | Citation validator (regex → `verse_exists()`) + semantic drift check |
| Safety moderation | Two-stage: regex (0ms) + Gemini Flash classifier |
| Image generation | FLUX.1-dev (NVIDIA) with prompt rewrite to Renaissance art style |
| Conversation memory | Window (≤10 turns) or semantic (>20 turns), denomination-switch guard |
| Evaluation harness | 20-case PASS/PARTIAL/FAIL suite with category grouping |

## Stack

| Concern | Choice |
| :-- | :-- |
| Backend | Python 3.12, FastAPI, uvicorn |
| Agent | LangGraph StateGraph |
| LLM | Gemini 2.5 Pro (grounded gen) + Gemini Flash (safety/router) |
| Embeddings | `BAAI/bge-base-en-v1.5` (local, sentence-transformers) |
| Data | PostgreSQL 16 + pgvector |
| Images | FLUX.1-dev via NVIDIA AI API |
| Frontend | Next.js 16, pure CSS (Lectio design system) |
| Logging | structlog |
| Package mgr | uv |

## Quick Start

### Prerequisites

- Docker + Docker Compose
- Python 3.12 (via `uv`)
- Node 20+
- API keys in `backend/.env` (see `.env.example`)

### 1. Start the database

```bash
make db-up
```

### 2. Backend setup

```bash
make backend-install   # uv sync — creates .venv, installs all deps
make backend-init      # DB schema migration
make backend-ingest    # embed KJV verses + church history (~30 min first run)
make dev               # start API on :8000
```

### 3. Frontend

```bash
make frontend-install  # npm install
make frontend-dev      # Next.js on :3000
```

Open `http://localhost:3000`.

### 4. Run evaluation

```bash
make eval
```

Expected: ≥18/20 PASS/PARTIAL.

### Environment variables

```bash
# backend/.env
GEMINI_API_KEY=...
NVIDIA_API_KEY=...        # FLUX.1-dev image generation
DATABASE_URL=postgresql://postgres:postgres@localhost:5433/christianity_ai
```

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
│   ├── app/                # Next.js app router (page.tsx, layout.tsx, globals.css)
│   └── components/         # Composer, DenominationSelector, MessageBubble,
│                           # VerseBlock, EmptyState, Icons, Loading
├── docs/
│   ├── ARCHITECTURE.md
│   ├── HLD.md
│   ├── PHASES.md
│   └── SYSTEM_DESIGN.md
├── Makefile
└── docker-compose.yml
```

## Evaluation Categories

| Category | Cases | What it tests |
| :-- | :-- | :-- |
| adversarial | 5 | Jailbreak, rewrite, extremism — must be flagged + blocked |
| fake_verse | 2 | Non-existent references — must detect, not hallucinate |
| hallucination | 2 | Common misquotes + topics not in scripture |
| image_safety | 3 | Safety pre/post rewrite + policy block |
| historical | 3 | Council dates, creed attribution |
| denomination | 2 | Catholic vs Protestant framing (purgatory, papal infallibility) |
| theology | 2 | Predestination paradox, resurrection significance |
| scripture | 1 | Normal retrieval with citation verification |

## Key Design Decisions

**Retrieval-first grounding** — System prompt forbids citing anything outside the injected context block. Hallucinated refs are detected post-generation and flagged in the UI with strikethrough.

**Two-stage safety** — Regex catches obvious violations in <1ms. Gemini Flash handles nuanced manipulation attempts. Either stage can block.

**Public-domain corpus only** — KJV translation avoids copyright. NIV/ESV are not used.

**Denomination filtering** — Each denomination has an associated canon list. Queries filter `denomination_canon @> ARRAY[denomination]` so Orthodox/Catholic users see deuterocanon results.

**Image prompt rewriting** — User requests are rewritten by the LLM into safe Renaissance fine-art style before hitting FLUX.1-dev. Post-generation safety check runs on the rewritten prompt too.
