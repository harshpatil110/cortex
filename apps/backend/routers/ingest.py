from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from middleware.auth import get_current_user
from schemas.ingest import IngestResponse
from services.storage_service import process_upload
from workers.process_memory import process_memory_task

router = APIRouter(prefix="/api/ingest", tags=["ingest"])


@router.post(
    "/file", response_model=IngestResponse, status_code=status.HTTP_202_ACCEPTED
)
async def upload_file(
    file: UploadFile = File(...), user_id: str = Depends(get_current_user)
):
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID not found in token")

    result = await process_upload(file, user_id)

    process_memory_task.delay(
        job_id=result["job_id"],
        memory_id=result["memory_id"],
        content_type=result["content_type"],
    )

    return IngestResponse(
        job_id=result["job_id"], memory_id=result["memory_id"], status="QUEUED"
    )
