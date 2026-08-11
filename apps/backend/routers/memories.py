from fastapi import APIRouter, Depends, HTTPException

from middleware.auth import get_current_user
from services.cache_service import cache_service
from services.storage_service import supabase

router = APIRouter(prefix="/api/memories", tags=["memories"])


@router.get("")
@router.get("/")
async def get_memories(user_id: str = Depends(get_current_user)):
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    cache_key = f"memories:{user_id}"
    cached_data = await cache_service.get(cache_key)
    if cached_data:
        return {"results": cached_data}

    res = (
        supabase.table("user_memories")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )

    if res.data:
        await cache_service.set(cache_key, res.data, 300)

    return {"results": res.data or []}


@router.get("/{memory_id}")
async def get_memory(memory_id: str, user_id: str = Depends(get_current_user)):
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    res = (
        supabase.table("user_memories")
        .select("*")
        .eq("id", memory_id)
        .eq("user_id", user_id)
        .execute()
    )

    if not res.data:
        raise HTTPException(status_code=404, detail="Memory not found")

    return res.data[0]
