from typing import Annotated, Literal
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages


Intent = Literal["scripture", "theology", "history", "image", "general", "blocked"]
Denomination = Literal["protestant", "catholic", "orthodox"]
MemoryStrategy = Literal["window", "semantic"]


class AgentState(TypedDict):
    # request
    session_id: str
    user_message: str
    denomination: Denomination
    request_id: str

    # safety + routing
    intent: Intent
    router_confidence: float
    flagged: bool

    # memory
    memory_strategy: MemoryStrategy
    memory_turns: list[dict]

    # retrieval
    retrieved_docs: list[dict]          # verses OR history chunks, tagged by source
    retrieval_confidence: float

    # generation
    raw_response: str

    # validation
    verified_citations: list[dict]
    hallucinated_refs: list[str]
    semantic_drift_score: float
    drift_warning: bool

    # image
    sanitized_image_prompt: str
    image_safety_passed: bool
    image_url: str

    # output
    final_response: str

    # langgraph message list (append-only)
    messages: Annotated[list, add_messages]

    # observability
    latency_ms: dict[str, float]
