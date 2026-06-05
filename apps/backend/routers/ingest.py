from fastapi import APIRouter

router = APIRouter(prefix="/api/ingest", tags=["ingest"])


@router.get("/")
async def dummy_endpoint():
    return {"message": "ingest routing works"}
