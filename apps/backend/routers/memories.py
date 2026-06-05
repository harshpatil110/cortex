from fastapi import APIRouter

router = APIRouter(prefix="/api/memories", tags=["memories"])


@router.get("/")
async def dummy_endpoint():
    return {"message": "memories routing works"}
