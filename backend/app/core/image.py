"""Image generation via Imagen (google-genai).

Prompt rewriting and two-pass safety are enforced by the graph nodes;
this module handles only the Imagen API call and response packaging.
"""

import base64

from app.config import get_settings
from app.core.llm import _client
from app.logging_config import get_logger

log = get_logger(__name__)
_s = get_settings()

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
    """Call Imagen API, return data URI or empty string on failure."""
    try:
        from google.genai import types as gtypes

        resp = _client().models.generate_images(
            model=_s.image_model,
            prompt=prompt,
            config=gtypes.GenerateImagesConfig(
                number_of_images=1,
                output_mime_type="image/jpeg",
            ),
        )
        if resp.generated_images:
            img_bytes = resp.generated_images[0].image.image_bytes
            data = base64.b64encode(img_bytes).decode()
            log.info("image.generated", model=_s.image_model, bytes=len(img_bytes))
            return f"data:image/jpeg;base64,{data}"
        log.warning("image.empty_response", model=_s.image_model)
        return ""
    except Exception as exc:
        log.error("image.generation_failed", error=str(exc))
        return ""
