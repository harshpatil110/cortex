from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from middleware.auth import get_current_user
from services.rag_service import rag_service
from utils.limiter import limiter

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    messages: list[dict]
    user_message: str


@router.post("")
@router.post("/")
@limiter.limit("30/hour")
async def chat_endpoint(
    request: Request, req: ChatRequest, user_id: str = Depends(get_current_user)
):
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID not found in token")

    return StreamingResponse(
        rag_service.stream_chat(user_id, req.messages, req.user_message),
        media_type="text/event-stream",
    )
