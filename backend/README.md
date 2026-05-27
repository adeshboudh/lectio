# Christianity AI Assistant — Backend

Grounded, denomination-aware Christianity assistant. FastAPI + LangGraph + pgvector.
See [`../docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md) for the full design.

## Stack

| Concern | Choice |
| :-- | :-- |
| Language | Python 3.12 |
| Package manager | uv |
| Web | FastAPI + uvicorn |
| Agent | LangGraph |
| LLM | Gemini 2.5 Pro (main) + 2.5 Flash (safety/router) |
| Embeddings | `bge-base-en-v1.5` (sentence-transformers, local) |
| Data | PostgreSQL 16 + pgvector |
| Images | Imagen 3 via google-genai |
| Logging | structlog (console in dev, JSON in prod) |

## Setup

```bash
# 1. start postgres + pgvector
docker compose up -d            # from repo root

# 2. install deps
cd backend
uv sync --extra dev

# 3. configure env
cp .env.example .env            # fill GEMINI_API_KEY

# 4. run
uv run uvicorn app.main:app --reload
```

Health check: `curl localhost:8000/health`

## Layout

```
app/
  main.py            FastAPI app, request-id logging middleware
  config.py          pydantic-settings (env-driven)
  logging_config.py  structlog setup
  api/routes.py      /health, /chat
  agent/             LangGraph nodes + state (WIP)
  core/              embeddings, db, safety (WIP)
scripts/             corpus ingestion (WIP)
```
