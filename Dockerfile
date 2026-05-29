FROM python:3.12-slim

WORKDIR /app

RUN pip install uv --no-cache-dir

COPY backend/ ./
RUN uv sync --no-dev

# Pre-download embedding model so cold start doesn't time out
RUN uv run python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-base-en-v1.5')"

EXPOSE 7860

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
