import uuid
from typing import Literal

import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.agent.graph import get_graph
from app.config import get_settings
from app.logging_config import get_logger

router = APIRouter()
log = get_logger(__name__)
settings = get_settings()


@router.get("/health")
async def health() -> dict:
    return {"status": "ok", "app": settings.app_name, "env": settings.env}


class ChatRequest(BaseModel):
    session_id: str
    message: str
    denomination: Literal["protestant", "catholic", "orthodox"] = "protestant"


class CitationOut(BaseModel):
    ref: str
    book: str
    chapter: int
    verse: int


class ChatResponse(BaseModel):
    session_id: str
    request_id: str
    response: str
    citations: list[CitationOut] = []
    hallucinated_refs: list[str] = []
    flagged: bool = False
    drift_warning: bool = False
    intent: str = ""
    latency_ms: dict = {}
    image_url: str = ""


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    request_id = structlog.contextvars.get_contextvars().get("request_id", str(uuid.uuid4()))
    log.info("chat.received", session_id=req.session_id, denomination=req.denomination)

    try:
        graph = get_graph()
        result = await _run_graph(graph, req, request_id)
    except Exception as exc:
        log.error("chat.error", error=str(exc))
        raise HTTPException(status_code=500, detail="Internal agent error") from exc

    return ChatResponse(
        session_id=req.session_id,
        request_id=request_id,
        response=result["final_response"],
        citations=[CitationOut(**c) for c in result.get("verified_citations", [])],
        hallucinated_refs=result.get("hallucinated_refs", []),
        flagged=result.get("flagged", False),
        drift_warning=result.get("drift_warning", False),
        intent=result.get("intent", ""),
        latency_ms=result.get("latency_ms", {}),
        image_url=result.get("image_url", ""),
    )


async def _run_graph(graph, req: ChatRequest, request_id: str) -> dict:
    """Run graph in threadpool so it doesn't block the event loop."""
    import asyncio

    state = {
        "session_id": req.session_id,
        "user_message": req.message,
        "denomination": req.denomination,
        "request_id": request_id,
        "messages": [],
        "latency_ms": {},
        "memory_turns": [],
    }
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, graph.invoke, state)
