import os
import uuid
from typing import Dict

import magic
from fastapi import HTTPException, UploadFile
from slugify import slugify
from supabase import Client, create_client

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
# Prefer service role key for backend operations if available
SUPABASE_KEY = os.getenv(
    "SUPABASE_SERVICE_ROLE_KEY", os.getenv("SUPABASE_ANON_KEY", "")
)

supabase: Client | None = (
    create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None
)

ALLOWED_MIMES = {
    "application/pdf": {
        "limit": 50 * 1024 * 1024,
        "bucket": "pdfs",
        "type": "document",
    },
    "image/png": {"limit": 20 * 1024 * 1024, "bucket": "screenshots", "type": "image"},
    "image/jpeg": {"limit": 20 * 1024 * 1024, "bucket": "screenshots", "type": "image"},
    "image/webp": {"limit": 20 * 1024 * 1024, "bucket": "screenshots", "type": "image"},
    "video/mp4": {"limit": 500 * 1024 * 1024, "bucket": "raw-media", "type": "video"},
}


async def process_upload(file: UploadFile, user_id: str) -> Dict[str, str]:
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase client not configured")

    # Read first 2048 bytes for magic MIME detection
    header = await file.read(2048)
    if not header:
        raise HTTPException(status_code=400, detail="Empty file")

    mime_type = magic.from_buffer(header, mime=True)
    if mime_type not in ALLOWED_MIMES:
        raise HTTPException(
            status_code=415, detail=f"Unsupported file type: {mime_type}"
        )

    config = ALLOWED_MIMES[mime_type]

    # Check file size without loading it entirely
    file.file.seek(0, 2)
    file_size = file.file.tell()
    # Reset cursor so it can be read properly later
    file.file.seek(0)

    if file_size > int(config["limit"]):
        limit_mb = int(config["limit"]) // (1024 * 1024)
        raise HTTPException(
            status_code=413, detail=f"File exceeds limit of {limit_mb}MB"
        )

    # Sanitize filename
    original_name = file.filename or "uploaded_file"
    name, ext = os.path.splitext(original_name)
    safe_name = slugify(name)
    short_id = str(uuid.uuid4())[:8]
    sanitized_filename = f"{safe_name}_{short_id}{ext}"

    bucket_name = config["bucket"]
    storage_path = f"{user_id}/{sanitized_filename}"

    # Read the full file for upload
    full_bytes = await file.read()

    # 1. Upload to Supabase Storage
    try:
        supabase.storage.from_(str(bucket_name)).upload(
            storage_path, full_bytes, file_options={"content-type": mime_type}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Storage upload failed: {str(e)}")

    content_type_str = config["type"]
    full_storage_path = f"{bucket_name}/{storage_path}"

    # 2. Database Inserts
    try:
        # Insert user memory
        mem_res = (
            supabase.table("user_memories")
            .insert(
                {
                    "user_id": user_id,
                    "content_type": content_type_str,
                    "storage_path": full_storage_path,
                    "ai_summary": {},
                    "indexed": False,
                }
            )
            .execute()
        )
        mem_data = (
            mem_res.data[0]
            if mem_res.data and isinstance(mem_res.data[0], dict)
            else {}
        )
        memory_id = str(mem_data.get("id", ""))

        # Insert job tracking
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
        job_data = (
            job_res.data[0]
            if job_res.data and isinstance(job_res.data[0], dict)
            else {}
        )
        job_id = str(job_data.get("id", ""))

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database insert failed: {str(e)}")

    return {
        "job_id": str(job_id),
        "memory_id": str(memory_id),
        "content_type": str(content_type_str),
    }
