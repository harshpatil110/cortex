import logging
from typing import Any, Dict, List, cast

from fastapi import APIRouter, Depends, HTTPException
from postgrest.types import CountMethod

from middleware.auth import get_current_user
from utils.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/plates", tags=["plates"])


@router.get("/")
async def list_plates(user_id: str = Depends(get_current_user)):
    """List all plates for the authenticated user."""
    supabase = get_supabase_client()
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase client not configured")

    try:
        res = (
            supabase.table("plates")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )
        plates: List[Dict[str, Any]] = [
            cast(Dict[str, Any], p) for p in (res.data or [])
        ]

        # Enrich each plate with item_count
        for plate in plates:
            try:
                count_res = (
                    supabase.table("memory_plates")
                    .select("id", count=CountMethod.exact)
                    .eq("plate_id", str(plate["id"]))
                    .execute()
                )
                plate["item_count"] = (
                    count_res.count if count_res.count is not None else 0
                )
            except Exception:
                plate["item_count"] = 0

        return {"data": plates}
    except Exception as e:
        logger.error(f"Failed to list plates for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list plates: {str(e)}")


@router.get("/{plate_id}")
async def get_plate(plate_id: str, user_id: str = Depends(get_current_user)):
    """Get a single plate by ID."""
    supabase = get_supabase_client()
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase client not configured")

    try:
        res = (
            supabase.table("plates")
            .select("*")
            .eq("id", plate_id)
            .eq("user_id", user_id)
            .single()
            .execute()
        )
        if not res.data:
            raise HTTPException(status_code=404, detail="Plate not found")

        plate = cast(Dict[str, Any], res.data)

        # Fetch associated memory IDs
        mem_res = (
            supabase.table("memory_plates")
            .select("memory_id")
            .eq("plate_id", plate_id)
            .execute()
        )
        mem_list: List[Dict[str, Any]] = [
            cast(Dict[str, Any], m) for m in (mem_res.data or [])
        ]
        plate["memory_ids"] = [m["memory_id"] for m in mem_list]
        plate["item_count"] = len(plate["memory_ids"])

        return plate
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get plate {plate_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get plate: {str(e)}")
