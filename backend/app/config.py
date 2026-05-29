from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # app
    app_name: str = "christianity-ai-assistant"
    env: Literal["dev", "prod"] = "dev"
    log_level: str = "INFO"
    log_json: bool = False  # True -> JSON logs (prod), False -> console (dev)
    cors_origins: str = ""  # comma-separated; empty = localhost only

    # database
    database_url: str = Field(
        default="postgresql://postgres:postgres@localhost:5433/christianity_ai"
    )

    # gemini (google-genai)
    gemini_api_key: str = Field(default="")
    model_main: str = "gemini-2.5-pro"
    model_safety: str = "gemini-2.5-flash"

    # embeddings (local sentence-transformers, no API)
    embedding_model: str = "BAAI/bge-base-en-v1.5"
    embedding_dim: int = 768

    # image generation (FLUX.1-dev via NVIDIA)
    nvidia_api_key: str = Field(default="")
    image_model: str = "black-forest-labs/flux.1-dev"

    # retrieval
    rag_top_k: int = 5
    retrieval_confidence_threshold: float = 0.45
    drift_threshold: float = 0.55

    # memory
    memory_window_turns: int = 10
    memory_semantic_switch_at: int = 20


@lru_cache
def get_settings() -> Settings:
    return Settings()
