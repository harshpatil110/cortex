from fastapi import APIRouter

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.get("/")
async def dummy_endpoint():
    return {"message": "jobs routing works"}
