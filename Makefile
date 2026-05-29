.PHONY: help \
        db-up db-down db-reset \
        backend-install backend-init \
        backend-ingest backend-ingest-bible backend-ingest-history \
        backend-dev \
        frontend-install frontend-dev frontend-build \
        eval \
        dev

BACKEND_DIR  := backend
FRONTEND_DIR := frontend
EVAL_DIR     := eval

# ──────────────────────────────────────────────────────────────
help:
	@echo ""
	@echo "  Lectio — Scripture Companion"
	@echo ""
	@echo "  Database"
	@echo "    make db-up          start postgres+pgvector container"
	@echo "    make db-down        stop container"
	@echo "    make db-reset       stop + wipe volume + restart"
	@echo ""
	@echo "  Backend"
	@echo "    make backend-install  uv sync (creates .venv + installs all deps)"
	@echo "    make backend-init     run DB migrations (init_db.py)"
	@echo "    make backend-ingest   ingest KJV bible + church history"
	@echo "    make backend-dev      start API server on :8000"
	@echo ""
	@echo "  Frontend"
	@echo "    make frontend-install  npm install"
	@echo "    make frontend-dev      start Next.js on :3000"
	@echo "    make frontend-build    production build"
	@echo ""
	@echo "  Eval"
	@echo "    make eval           run 20-case evaluation harness"
	@echo ""
	@echo "  Shortcuts"
	@echo "    make dev            start backend API on :8000"
	@echo ""

# ──────────────────────────────────────────────────────────────
# DATABASE
# ──────────────────────────────────────────────────────────────
db-up:
	docker compose up -d db
	@echo "Waiting for postgres..."
	@docker compose exec db sh -c 'until pg_isready -U postgres -d christianity_ai; do sleep 1; done'

db-down:
	docker compose down

db-reset:
	docker compose down -v
	docker compose up -d db
	@docker compose exec db sh -c 'until pg_isready -U postgres -d christianity_ai; do sleep 1; done'

# ──────────────────────────────────────────────────────────────
# BACKEND
# ──────────────────────────────────────────────────────────────
backend-install:
	cd $(BACKEND_DIR) && uv sync --extra dev

backend-init:
	cd $(BACKEND_DIR) && uv run python -m scripts.init_db

backend-ingest-bible:
	cd $(BACKEND_DIR) && uv run python -m scripts.ingest_bible

backend-ingest-history:
	cd $(BACKEND_DIR) && uv run python -m scripts.ingest_history

backend-ingest:
	cd $(BACKEND_DIR) && uv run python -m scripts.ingest_bible
	cd $(BACKEND_DIR) && uv run python -m scripts.ingest_history

backend-dev:
	cd $(BACKEND_DIR) && uv run uvicorn app.main:app --reload --port 8000

# ──────────────────────────────────────────────────────────────
# FRONTEND
# ──────────────────────────────────────────────────────────────
frontend-install:
	cd $(FRONTEND_DIR) && npm install

frontend-dev:
	cd $(FRONTEND_DIR) && npm run dev

frontend-build:
	cd $(FRONTEND_DIR) && npm run build

# ──────────────────────────────────────────────────────────────
# EVAL
# ──────────────────────────────────────────────────────────────
eval:
	cd $(EVAL_DIR) && uv run --project ../$(BACKEND_DIR) run_eval.py

# ──────────────────────────────────────────────────────────────
# DEV — all three services (requires tmux or GNU parallel)
# ──────────────────────────────────────────────────────────────
dev:
	cd $(BACKEND_DIR) && uv run uvicorn app.main:app --reload --port 8000
