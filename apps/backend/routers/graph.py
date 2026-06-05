from fastapi import APIRouter

router = APIRouter(prefix="/api/graph", tags=["graph"])


@router.get("/")
async def dummy_endpoint():
    return {"message": "graph routing works"}
