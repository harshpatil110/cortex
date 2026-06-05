from fastapi import APIRouter

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("/")
async def dummy_endpoint():
    return {"message": "search routing works"}
