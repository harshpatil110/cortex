import logging

from fastapi import APIRouter, Depends, HTTPException, Query

from middleware.auth import get_current_user
from services.cache_service import cache_service
from services.search_service import THUMBNAIL_BUCKET, THUMBNAIL_URL_TTL
from utils.storage_paths import strip_bucket_prefix
from utils.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/memories", tags=["memories"])


async def _signed_url_for(supabase, bucket: str, object_key: str | None):
    """Mint a cached signed URL for an in-bucket object key."""
    if not object_key:
        return None
    cache_key = f"media:{bucket}:{object_key}"
    cached = await cache_service.get(cache_key)
    if cached:
        return cached
    try:
        res = supabase.storage.from_(bucket).create_signed_url(
            object_key, THUMBNAIL_URL_TTL
        )
        url = res.get("signedURL")
        if url:
            await cache_service.set(cache_key, url, THUMBNAIL_URL_TTL)
        return url
    except Exception as e:
        logger.warning(f"Failed to generate signed URL for {bucket}/{object_key}: {e}")
        return None


def _split_storage_path(stored_path: str | None):
    """Split a stored "<bucket>/<key>" path into (bucket, key)."""
    if not stored_path or "/" not in stored_path:
        return None, None
    bucket, _, key = stored_path.partition("/")
    return bucket, key or None


async def _enrich_memory(supabase, memory: dict) -> dict:
    """Attach signed thumbnail/media URLs so the frontend can render them."""
    enriched = dict(memory)
    enriched["thumbnail_url"] = await _signed_url_for(
        supabase,
        THUMBNAIL_BUCKET,
        strip_bucket_prefix(memory.get("thumbnail_storage_path"), THUMBNAIL_BUCKET),
    )
    media_bucket, media_key = _split_storage_path(memory.get("storage_path"))
    enriched["media_url"] = (
        await _signed_url_for(supabase, media_bucket, media_key)
        if media_bucket
        else None
    )
    return enriched


@router.get("")
@router.get("/")
async def get_memories(
    user_id: str = Depends(get_current_user),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    supabase = get_supabase_client()
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase client not configured")

    # Only cache the first page; deeper pages are cheap to re-query.
    cache_key = f"memories:{user_id}:{limit}:{offset}" if offset == 0 else None
    if cache_key:
        cached_data = await cache_service.get(cache_key)
        if cached_data:
            return {"results": cached_data}

    res = (
        supabase.table("user_memories")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .range(offset, offset + limit - 1)
        .execute()
    )

    results = [await _enrich_memory(supabase, row) for row in (res.data or [])]

    if cache_key and results:
        await cache_service.set(cache_key, results, 300)

    return {"results": results}


@router.get("/{memory_id}")
async def get_memory(memory_id: str, user_id: str = Depends(get_current_user)):
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    supabase = get_supabase_client()
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase client not configured")

    res = (
        supabase.table("user_memories")
        .select("*")
        .eq("id", memory_id)
        .eq("user_id", user_id)
        .execute()
    )

    if not res.data:
        raise HTTPException(status_code=404, detail="Memory not found")

    return await _enrich_memory(supabase, res.data[0])
