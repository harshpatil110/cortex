from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from middleware.auth import get_current_user
from services.rag_service import rag_service

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    messages: list[dict]
    user_message: str


@router.post("")
@router.post("/")
async def chat_endpoint(req: ChatRequest, user_id: str = Depends(get_current_user)):
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID not found in token")

    return StreamingResponse(
        rag_service.stream_chat(user_id, req.messages, req.user_message),
        media_type="text/event-stream",
    )
