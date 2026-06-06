import asyncio

from fastapi import APIRouter, Depends, HTTPException
from sse_starlette.sse import EventSourceResponse

from middleware.auth import get_current_user
from schemas.base import JobStatus
from services.storage_service import supabase

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.get("/{job_id}/stream")
async def stream_job_status(job_id: str, user_id: str = Depends(get_current_user)):
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase client not configured")

    async def event_generator():
        while True:
            try:
                res = await asyncio.to_thread(
                    lambda: supabase.table("job_tracking")
                    .select("*")
                    .eq("id", job_id)
                    .execute()
                )
            except Exception:
                error_job = JobStatus(
                    id=job_id, status="FAILED", error_message="Database error"
                )
                yield f"data: {error_job.model_dump_json()}\n\n"
                break

            if not res.data:
                error_job = JobStatus(
                    id=job_id, status="FAILED", error_message="Job not found"
                )
                yield f"data: {error_job.model_dump_json()}\n\n"
                break

            job_dict = res.data[0]

            if job_dict.get("user_id") != user_id:
                error_job = JobStatus(
                    id=job_id, status="FAILED", error_message="Unauthorized"
                )
                yield f"data: {error_job.model_dump_json()}\n\n"
                break

            job_model = JobStatus(**job_dict)
            yield f"data: {job_model.model_dump_json()}\n\n"

            if job_model.status in ["COMPLETE", "FAILED"]:
                break

            await asyncio.sleep(1.5)

    return EventSourceResponse(event_generator())


@router.get("/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str, user_id: str = Depends(get_current_user)):
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase client not configured")

    res = supabase.table("job_tracking").select("*").eq("id", job_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Job not found")

    job_dict = res.data[0]
    if job_dict.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    return JobStatus(**job_dict)
