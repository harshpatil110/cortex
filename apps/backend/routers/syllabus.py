from fastapi import APIRouter

router = APIRouter(prefix="/api/syllabus", tags=["syllabus"])


@router.get("/")
async def dummy_endpoint():
    return {"message": "syllabus routing works"}
