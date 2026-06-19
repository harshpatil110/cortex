from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from middleware.auth import get_current_user
from services.syllabus_service import syllabus_service

router = APIRouter()


class GenerateSyllabusRequest(BaseModel):
    memory_ids: List[str]
    topic_title: str


@router.post("/api/syllabus")
async def generate_syllabus(
    req: GenerateSyllabusRequest, user_id: str = Depends(get_current_user)
):
    try:
        res = await syllabus_service.generate_syllabus(
            user_id, req.memory_ids, req.topic_title
        )
        return {"status": "success", "data": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/syllabus")
async def get_syllabuses(user_id: str = Depends(get_current_user)):
    res = await syllabus_service.get_syllabuses(user_id)
    return {"status": "success", "data": res}


@router.get("/api/syllabus/{syllabus_id}")
async def get_syllabus(syllabus_id: str, user_id: str = Depends(get_current_user)):
    try:
        res = await syllabus_service.get_syllabus(user_id, syllabus_id)
        return {"status": "success", "data": res}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
