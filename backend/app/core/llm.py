"""Gemini (google-genai) client wrapper.

Gemini Pro for grounded generation, Gemini Flash for fast structured
classification (safety + routing). Generation is retrieval-first: the caller
injects retrieved context into the prompt and the system instruction forbids
citing anything outside it.
"""

from functools import lru_cache
from typing import Any

from google import genai
from google.genai import types

from app.config import get_settings
from app.core.prompts import build_system_prompt, build_user_prompt
from app.logging_config import get_logger

log = get_logger(__name__)
_settings = get_settings()


@lru_cache
def _client() -> genai.Client:
    if not _settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")
    return genai.Client(api_key=_settings.gemini_api_key)


def generate_grounded(
    query: str,
    context_block: str,
    denomination: str,
    memory_block: str = "",
    temperature: float = 0.3,
    max_output_tokens: int = 1024,
) -> str:
    """Grounded text generation. Context is injected; model cites only from it."""
    system = build_system_prompt(denomination)
    user = build_user_prompt(query, context_block, memory_block)
    resp = _client().models.generate_content(
        model=_settings.model_main,
        contents=user,
        config=types.GenerateContentConfig(
            system_instruction=system,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
        ),
    )
    text = resp.text or ""
    log.info("llm.generate", model=_settings.model_main, chars=len(text))
    return text


def generate_json(
    prompt: str,
    response_schema: Any,
    system_instruction: str | None = None,
    model: str | None = None,
    temperature: float = 0.0,
) -> Any:
    """Structured output via Gemini. Returns the parsed schema instance.

    Used by the safety+router stage (Phase 4) for {safe, intent, confidence}.
    """
    model = model or _settings.model_safety
    resp = _client().models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
            response_schema=response_schema,
            temperature=temperature,
        ),
    )
    log.info("llm.generate_json", model=model)
    return resp.parsed
