import os
import tempfile
import uuid

import httpx
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from middleware.auth import get_current_user
from schemas.ingest import IngestResponse, UrlIngestRequest
from services.scrapers.instagram_scraper import InstagramScraper
from services.storage_service import process_upload, supabase
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


@router.post(
    "/url", response_model=IngestResponse, status_code=status.HTTP_202_ACCEPTED
)
async def ingest_url(
    payload: UrlIngestRequest, user_id: str = Depends(get_current_user)
):
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID not found in token")

    if payload.content_type != "instagram_reel":
        raise HTTPException(
            status_code=400, detail="Only 'instagram_reel' is currently supported"
        )

    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase client not configured")

    scraper = InstagramScraper()
    try:
        scraped_data = await scraper.scrape(payload.url)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")

    # Download assets to temporary files using httpx
    short_id = str(uuid.uuid4())[:8]
    mp4_path = os.path.join(tempfile.gettempdir(), f"{short_id}.mp4")
    thumb_path = os.path.join(tempfile.gettempdir(), f"{short_id}.jpg")

    async with httpx.AsyncClient() as client:
        # Download MP4
        async with client.stream("GET", scraped_data["mp4_url"]) as response:
            if response.status_code != 200:
                raise HTTPException(
                    status_code=500, detail="Failed to download video stream"
                )
            with open(mp4_path, "wb") as f:
                async for chunk in response.aiter_bytes():
                    f.write(chunk)

        # Download thumbnail if present
        if scraped_data.get("thumbnail_url"):
            try:
                thumb_resp = await client.get(
                    scraped_data["thumbnail_url"], timeout=15.0
                )
                if thumb_resp.status_code == 200:
                    with open(thumb_path, "wb") as f:
                        f.write(thumb_resp.content)
            except Exception:
                pass  # Thumbnail is non-critical, we can ignore failure

    # Upload to Supabase Storage
    safe_name = f"ig_reel_{short_id}"
    video_storage_path = f"{user_id}/{safe_name}.mp4"
    thumb_storage_path = f"{user_id}/{safe_name}.jpg"

    try:
        with open(mp4_path, "rb") as f:
            supabase.storage.from_("raw-media").upload(
                video_storage_path, f.read(), file_options={"content-type": "video/mp4"}
            )

        if os.path.exists(thumb_path):
            with open(thumb_path, "rb") as f:
                supabase.storage.from_("thumbnails").upload(
                    thumb_storage_path,
                    f.read(),
                    file_options={"content-type": "image/jpeg"},
                )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Storage upload failed: {str(e)}")
    finally:
        # Cleanup temporary files
        if os.path.exists(mp4_path):
            os.remove(mp4_path)
        if os.path.exists(thumb_path):
            os.remove(thumb_path)

    # Insert Database Records
    try:
        mem_res = (
            supabase.table("user_memories")
            .insert(
                {
                    "user_id": user_id,
                    "content_type": payload.content_type,
                    "storage_path": f"raw-media/{video_storage_path}",
                    "source_url": scraped_data["webpage_url"],
                    "creator_metadata": scraped_data["creator_metadata"],
                    "ai_summary": {},
                    "indexed": False,
                }
            )
            .execute()
        )
        memory_id = mem_res.data[0]["id"]

        job_res = (
            supabase.table("job_tracking")
            .insert(
                {
                    "user_id": user_id,
                    "memory_id": memory_id,
                    "status": "QUEUED",
                    "current_stage": "UPLOADED",
                }
            )
            .execute()
        )
        job_id = job_res.data[0]["id"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database insert failed: {str(e)}")

    process_memory_task.delay(
        job_id=job_id, memory_id=memory_id, content_type=payload.content_type
    )

    return IngestResponse(job_id=job_id, memory_id=memory_id, status="QUEUED")
