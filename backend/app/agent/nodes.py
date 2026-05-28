"""LangGraph node functions. Each takes AgentState, returns partial state update."""

import re
import time
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage

from app.agent.state import AgentState
from app.config import get_settings
from app.core.embeddings import embed_query
from app.core.llm import generate_grounded
from app.core.prompts import build_history_context, build_scripture_context
from app.core.retrieval import search_history, search_scripture, verse_exists
from app.core.safety import classify
from app.logging_config import get_logger

log = get_logger(__name__)
_s = get_settings()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _tick() -> float:
    return time.monotonic()


def _ms(start: float) -> float:
    return round((time.monotonic() - start) * 1000, 1)


def _memory_block(turns: list[dict]) -> str:
    if not turns:
        return ""
    lines = [f"{t['role'].upper()}: {t['content']}" for t in turns]
    return "CONVERSATION HISTORY:\n" + "\n".join(lines)


# ---------------------------------------------------------------------------
# Node: input
# ---------------------------------------------------------------------------

def node_input(state: AgentState) -> dict[str, Any]:
    """Initialize defaults, load conversation memory, add user turn to messages."""
    from app.core.memory import load_memory

    t = _tick()
    turns, strategy, guard_note = load_memory(
        state["session_id"], state["user_message"], state["denomination"]
    )

    # Prepend denomination-switch note as a system turn when framing changed
    if guard_note:
        turns = [{"role": "system", "content": guard_note}] + turns

    return {
        "intent": "general",
        "router_confidence": 0.0,
        "flagged": False,
        "retrieved_docs": [],
        "retrieval_confidence": 0.0,
        "raw_response": "",
        "verified_citations": [],
        "hallucinated_refs": [],
        "semantic_drift_score": 0.0,
        "drift_warning": False,
        "sanitized_image_prompt": "",
        "image_safety_passed": False,
        "image_url": "",
        "final_response": "",
        "memory_strategy": strategy,
        "memory_turns": turns,
        "latency_ms": {"memory_load": _ms(t)},
        "messages": [HumanMessage(content=state["user_message"])],
    }


# ---------------------------------------------------------------------------
# Node: safety + router
# ---------------------------------------------------------------------------

_HISTORY_KEYWORDS = re.compile(
    r"\b(council|creed|nicaea|chalcedon|trent|nicea|constantine|arius|athanasius|"
    r"reformation|schism|pope|patriarch|catechism|confession|synod|ecumenical)\b",
    re.IGNORECASE,
)
_IMAGE_KEYWORDS = re.compile(r"\b(generate|create|draw|paint|image|picture|illustration)\b", re.IGNORECASE)


def _fallback_intent(message: str) -> str:
    """Keyword-based intent estimate used when Gemini Flash is unavailable."""
    if _IMAGE_KEYWORDS.search(message):
        return "image"
    if _HISTORY_KEYWORDS.search(message):
        return "history"
    return "general"


def node_safety_router(state: AgentState) -> dict[str, Any]:
    t = _tick()
    try:
        result = classify(state["user_message"])
        intent = result.intent
        confidence = result.confidence
        flagged = not result.safe
    except Exception as exc:
        # Gemini transient error → fail safe: allow through, keyword-route intent
        intent = _fallback_intent(state["user_message"])
        log.warning("safety_router.fallback", error=str(exc), fallback_intent=intent)
        confidence = 0.5
        flagged = False
    return {
        "intent": intent,
        "router_confidence": confidence,
        "flagged": flagged,
        "latency_ms": {**state.get("latency_ms", {}), "safety_router": _ms(t)},
    }


# ---------------------------------------------------------------------------
# Node: scripture RAG
# ---------------------------------------------------------------------------

def node_scripture_rag(state: AgentState) -> dict[str, Any]:
    t = _tick()
    verses, confidence = search_scripture(
        state["user_message"], state["denomination"]
    )
    return {
        "retrieved_docs": verses,
        "retrieval_confidence": confidence,
        "latency_ms": {**state.get("latency_ms", {}), "scripture_rag": _ms(t)},
    }


# ---------------------------------------------------------------------------
# Node: history RAG
# ---------------------------------------------------------------------------

def node_history_rag(state: AgentState) -> dict[str, Any]:
    t = _tick()
    docs, confidence = search_history(
        state["user_message"], state["denomination"]
    )
    return {
        "retrieved_docs": docs,
        "retrieval_confidence": confidence,
        "latency_ms": {**state.get("latency_ms", {}), "history_rag": _ms(t)},
    }


# ---------------------------------------------------------------------------
# Node: theology (denomination-framed, uses scripture retrieval)
# ---------------------------------------------------------------------------

def node_theology(state: AgentState) -> dict[str, Any]:
    t = _tick()
    verses, confidence = search_scripture(
        state["user_message"], state["denomination"]
    )
    return {
        "retrieved_docs": verses,
        "retrieval_confidence": confidence,
        "latency_ms": {**state.get("latency_ms", {}), "theology_rag": _ms(t)},
    }


# ---------------------------------------------------------------------------
# Node: image (prompt rewrite → Imagen via Gemini)
# ---------------------------------------------------------------------------

def node_image(state: AgentState) -> dict[str, Any]:
    """Rewrite user prompt into safe Christian-art form; store for post-rewrite validation."""
    from app.core.image import rewrite_image_prompt

    t = _tick()
    try:
        sanitized = rewrite_image_prompt(state["user_message"], state["denomination"])
    except Exception as exc:
        log.error("node_image.rewrite_failed", error=str(exc))
        sanitized = state["user_message"]   # fallback: pass original; validator will re-check
    return {
        "sanitized_image_prompt": sanitized,
        "latency_ms": {**state.get("latency_ms", {}), "image_rewrite": _ms(t)},
    }


# ---------------------------------------------------------------------------
# Node: image validator (re-check rewritten prompt before generation)
# ---------------------------------------------------------------------------

def node_image_validator(state: AgentState) -> dict[str, Any]:
    """Re-classify rewritten prompt (closes post-rewrite safety gap), then generate."""
    from app.core.image import generate_image

    t = _tick()
    passed = False
    image_url = ""
    flagged = False

    try:
        result = classify(state["sanitized_image_prompt"])
        passed = result.safe  # intent re-checked as safe art; original intent already routed
    except Exception as exc:
        # Gemini transient error → fail safe: block the image
        log.warning("image_validator.fallback", error=str(exc))
        passed = False
        flagged = True

    if passed:
        image_url = generate_image(state["sanitized_image_prompt"])
    else:
        flagged = True

    return {
        "image_safety_passed": passed,
        "image_url": image_url,
        "flagged": flagged,
        "latency_ms": {**state.get("latency_ms", {}), "image_validator": _ms(t)},
    }


# ---------------------------------------------------------------------------
# Node: validator (citations + semantic drift)
# ---------------------------------------------------------------------------

_VERSE_REF_RE = re.compile(
    r"\b([1-3]?\s?[A-Z][a-z]+(?:\s[A-Z][a-z]+)?)\s+(\d+):(\d+)\b"
)


def node_validator(state: AgentState) -> dict[str, Any]:
    t = _tick()
    raw = state["raw_response"]

    # --- Citation validation ---
    verified, hallucinated = [], []
    for m in _VERSE_REF_RE.finditer(raw):
        book, ch, vs = m.group(1).strip(), int(m.group(2)), int(m.group(3))
        if verse_exists(book, ch, vs):
            verified.append({"ref": f"{book} {ch}:{vs}", "book": book, "chapter": ch, "verse": vs})
        else:
            hallucinated.append(f"{book} {ch}:{vs}")

    # Remove hallucinated refs from final text
    cleaned = raw
    for ref in hallucinated:
        cleaned = cleaned.replace(ref, "[invalid reference removed]")

    # --- Semantic drift check ---
    drift_score = 0.0
    drift_warning = False
    docs = state.get("retrieved_docs", [])
    if docs and raw and state.get("retrieval_confidence", 0) > _s.retrieval_confidence_threshold:
        import numpy as np
        resp_vec = embed_query(raw)
        doc_texts = [d.get("text") or d.get("content", "") for d in docs]
        if doc_texts:
            doc_vecs = __import__("app.core.embeddings", fromlist=["embed_passages"]).embed_passages(doc_texts)
            sims = [
                float(np.dot(resp_vec, dv))
                for dv in doc_vecs
            ]
            drift_score = 1.0 - max(sims)
            if drift_score > _s.drift_threshold:
                drift_warning = True
                cleaned += (
                    "\n\n*Note: portions of this response may not precisely reflect "
                    "the retrieved scripture — please verify wording directly.*"
                )

    if hallucinated:
        log.warning("validator.hallucinated_refs", refs=hallucinated)

    return {
        "raw_response": cleaned,
        "verified_citations": verified,
        "hallucinated_refs": hallucinated,
        "semantic_drift_score": round(drift_score, 4),
        "drift_warning": drift_warning,
        "latency_ms": {**state.get("latency_ms", {}), "validator": _ms(t)},
    }


# ---------------------------------------------------------------------------
# Node: generate (LLM call, shared by scripture/theology/history/general)
# ---------------------------------------------------------------------------

def node_generate(state: AgentState) -> dict[str, Any]:
    t = _tick()
    docs = state.get("retrieved_docs", [])

    if docs and ("book" in docs[0]):
        ctx = build_scripture_context(docs)
    elif docs:
        ctx = build_history_context(docs)
    else:
        ctx = build_scripture_context([])

    memory_block = _memory_block(state.get("memory_turns", []))
    try:
        raw = generate_grounded(
            query=state["user_message"],
            context_block=ctx,
            denomination=state["denomination"],
            memory_block=memory_block,
        )
    except Exception as exc:
        log.error("node_generate.failed", error=str(exc))
        raw = "I'm sorry, I encountered an error generating a response. Please try again."
    return {
        "raw_response": raw,
        "latency_ms": {**state.get("latency_ms", {}), "generate": _ms(t)},
    }


# ---------------------------------------------------------------------------
# Node: responder (assemble final output)
# ---------------------------------------------------------------------------

def node_responder(state: AgentState) -> dict[str, Any]:
    from app.core.memory import save_turn

    if state.get("flagged") and not state.get("raw_response"):
        final = (
            "I'm not able to help with that request. "
            "Please ask a question related to Christianity, scripture, or Christian life."
        )
    elif state.get("image_url"):
        final = state.get("raw_response", "") or "Here is the generated image."
    else:
        final = state.get("raw_response", "")

    # Persist both turns (skip if flagged — don't store adversarial content)
    if not state.get("flagged"):
        save_turn(state["session_id"], "user", state["user_message"], state["denomination"])
        save_turn(state["session_id"], "assistant", final, state["denomination"])

    return {
        "final_response": final,
        "messages": [AIMessage(content=final)],
    }
