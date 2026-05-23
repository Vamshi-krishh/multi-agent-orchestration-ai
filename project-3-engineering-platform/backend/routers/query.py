"""
READ-ONLY router. These endpoints NEVER write to disk or modify any file.
Question mode = intelligence only.
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
from backend.services import rag_client

router = APIRouter(prefix="/query", tags=["query"])


class ChatRequest(BaseModel):
    question: str
    conversation_history: Optional[List[dict]] = []


class ChatResponse(BaseModel):
    answer: str
    sources: List[str]
    rewritten_question: str
    confidence_score: int


@router.post("", response_model=ChatResponse)
def chat(request: ChatRequest):
    result = rag_client.query(request.question, request.conversation_history)
    return ChatResponse(
        answer=result.get("answer", ""),
        sources=result.get("sources", []),
        rewritten_question=result.get("rewritten_question", request.question),
        confidence_score=result.get("confidence_score", 0)
    )
