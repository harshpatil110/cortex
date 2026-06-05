from fastapi import APIRouter

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.get("/")
async def dummy_endpoint():
    return {"message": "chat routing works"}
