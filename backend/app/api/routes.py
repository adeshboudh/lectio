from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

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


class ChatResponse(BaseModel):
    session_id: str
    response: str
    citations: list[dict] = []
    flagged: bool = False


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    # Placeholder until the LangGraph agent is wired in.
    log.info("chat.received", session_id=req.session_id, denomination=req.denomination)
    return ChatResponse(
        session_id=req.session_id,
        response="Agent not yet implemented.",
    )
