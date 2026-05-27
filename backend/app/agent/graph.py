"""LangGraph StateGraph wiring.

Flow:
    input → safety_router ──blocked──────────────────────→ responder → END
                           ──scripture──→ scripture_rag ─→ generate → validator → responder
                           ──theology───→ theology      ─→ generate → validator → responder
                           ──history────→ history_rag   ─→ generate → validator → responder
                           ──image──────→ image         → image_validator ──blocked──→ responder
                                                                          ──safe─────→ responder
                           ──general────────────────────→ generate → validator → responder
"""

from functools import lru_cache

from langgraph.graph import END, StateGraph

from app.agent.nodes import (
    node_generate,
    node_history_rag,
    node_image,
    node_image_validator,
    node_input,
    node_responder,
    node_safety_router,
    node_scripture_rag,
    node_theology,
    node_validator,
)
from app.agent.state import AgentState


def _route_after_safety(state: AgentState) -> str:
    if state["flagged"]:
        return "responder"
    intent = state["intent"]
    if intent == "scripture":
        return "scripture_rag"
    if intent == "theology":
        return "theology"
    if intent == "history":
        return "history_rag"
    if intent == "image":
        return "image"
    return "generate"   # general + low-confidence fallback


def _route_after_image_validator(state: AgentState) -> str:
    return "responder"   # responder handles both safe (with image_url) and blocked


def _build_graph() -> StateGraph:
    g = StateGraph(AgentState)

    g.add_node("input", node_input)
    g.add_node("safety_router", node_safety_router)
    g.add_node("scripture_rag", node_scripture_rag)
    g.add_node("theology", node_theology)
    g.add_node("history_rag", node_history_rag)
    g.add_node("image", node_image)
    g.add_node("image_validator", node_image_validator)
    g.add_node("generate", node_generate)
    g.add_node("validator", node_validator)
    g.add_node("responder", node_responder)

    g.set_entry_point("input")
    g.add_edge("input", "safety_router")

    g.add_conditional_edges(
        "safety_router",
        _route_after_safety,
        {
            "responder": "responder",
            "scripture_rag": "scripture_rag",
            "theology": "theology",
            "history_rag": "history_rag",
            "image": "image",
            "generate": "generate",
        },
    )

    # RAG branches → shared generate → validator → responder
    for rag_node in ("scripture_rag", "theology", "history_rag"):
        g.add_edge(rag_node, "generate")
    g.add_edge("generate", "validator")
    g.add_edge("validator", "responder")

    # Image branch → image_validator → responder
    g.add_edge("image", "image_validator")
    g.add_conditional_edges(
        "image_validator",
        _route_after_image_validator,
        {"responder": "responder"},
    )

    g.add_edge("responder", END)
    return g


@lru_cache
def get_graph():
    """Compiled graph singleton — thread-safe after first call."""
    return _build_graph().compile()
