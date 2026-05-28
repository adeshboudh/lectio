"""Gemini (google-genai) client wrapper.

Gemini Pro for grounded generation, Gemini Flash for fast structured
classification (safety + routing). Generation is retrieval-first: the caller
injects retrieved context into the prompt and the system instruction forbids
citing anything outside it.
"""

import json
import re
from typing import Any

from google import genai
from google.genai import types

from app.config import get_settings
from app.core.prompts import build_system_prompt, build_user_prompt
from app.logging_config import get_logger

log = get_logger(__name__)
_settings = get_settings()


_gemini_client: genai.Client | None = None


def _client() -> genai.Client:
    """Return module-level Gemini client, recreating if closed (stale httpx session)."""
    global _gemini_client
    if not _settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")
    if _gemini_client is None:
        _gemini_client = genai.Client(api_key=_settings.gemini_api_key)
    return _gemini_client


def _reset_client() -> None:
    """Force client recreation on next call (call after catching closed-client errors)."""
    global _gemini_client
    _gemini_client = None


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
    try:
        resp = _client().models.generate_content(
            model=_settings.model_main,
            contents=user,
            config=types.GenerateContentConfig(
                system_instruction=system,
                temperature=temperature,
                max_output_tokens=max_output_tokens,
            ),
        )
    except Exception as exc:
        if "closed" in str(exc).lower():
            _reset_client()
            resp = _client().models.generate_content(
                model=_settings.model_main,
                contents=user,
                config=types.GenerateContentConfig(
                    system_instruction=system,
                    temperature=temperature,
                    max_output_tokens=max_output_tokens,
                ),
            )
        else:
            raise
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
    """Structured output via Gemini. Returns the parsed schema instance."""
    model = model or _settings.model_safety

    def _call():
        return _client().models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=response_schema,
                temperature=temperature,
            ),
        )

    try:
        resp = _call()
    except Exception as exc:
        if "closed" in str(exc).lower():
            _reset_client()
            resp = _call()
        else:
            raise
    log.info("llm.generate_json", model=model)
    if resp.parsed is not None:
        return resp.parsed
    # Fallback: model wrapped JSON in a markdown code block — strip and parse manually
    raw = resp.text or ""
    raw = re.sub(r"^```(?:json)?\s*", "", raw.strip(), flags=re.IGNORECASE)
    raw = re.sub(r"\s*```$", "", raw.strip())
    try:
        data = json.loads(raw)
        return response_schema(**data)
    except Exception:
        return None
