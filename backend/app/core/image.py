"""Image generation via FLUX.1-dev (NVIDIA AI API).

Prompt rewriting and two-pass safety are enforced by the graph nodes;
this module handles only the API call and response packaging.
"""

import base64

import httpx

from app.config import get_settings
from app.logging_config import get_logger

log = get_logger(__name__)
_s = get_settings()

_NVIDIA_URL = "https://ai.api.nvidia.com/v1/genai/{model}"

_REWRITE_PROMPT = """Rewrite the following image request as a safe, reverential Christian \
fine-art prompt suitable for a painting in the style of Renaissance religious art. \
Remove any politically sensitive, interfaith-mocking, or policy-violating elements. \
Return ONLY the rewritten prompt, no explanation.

Original request: {request}"""


def rewrite_image_prompt(user_request: str, denomination: str) -> str:
    """Convert raw user request into a safe Christian-art prompt."""
    from app.core.llm import generate_grounded

    return generate_grounded(
        query=_REWRITE_PROMPT.format(request=user_request),
        context_block="",
        denomination=denomination,
        max_output_tokens=200,
        temperature=0.2,
    ).strip()


def generate_image(prompt: str) -> str:
    """Call FLUX.1-dev via NVIDIA API, return data URI or empty string on failure."""
    try:
        url = _NVIDIA_URL.format(model=_s.image_model)
        headers = {
            "Authorization": f"Bearer {_s.nvidia_api_key}",
            "Accept": "application/json",
        }
        payload = {
            "prompt": prompt,
            "mode": "base",
            "cfg_scale": 3.5,
            "width": 1024,
            "height": 1024,
            "seed": 0,
            "steps": 50,
        }

        resp = httpx.post(url, headers=headers, json=payload, timeout=120.0)
        resp.raise_for_status()
        body = resp.json()

        artifacts = body.get("artifacts") or []
        if artifacts:
            b64 = artifacts[0].get("base64", "")
            if b64:
                log.info("image.generated", model=_s.image_model, bytes=len(b64))
                return f"data:image/jpeg;base64,{b64}"

        log.warning("image.empty_response", model=_s.image_model, body=body)
        return ""
    except Exception as exc:
        log.error("image.generation_failed", error=str(exc))
        return ""
