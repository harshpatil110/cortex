import logging

from fastapi import APIRouter, Depends, Query

from middleware.auth import get_current_user
from utils.supabase_client import get_supabase_client

router = APIRouter(prefix="/api/plates", tags=["plates"])
logger = logging.getLogger(__name__)


@router.get("/")
async def list_plates(
    user_id: str = Depends(get_current_user),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    """List all plates for the authenticated user."""
    supabase = get_supabase_client()

    res = (
        supabase.table("plates")
        .select("*")
        .eq("user_id", user_id)
        .order("updated_at", desc=True)
        .range(offset, offset + limit - 1)
        .execute()
    )

    plates = res.data or []

    # Enrich each plate with item_count
    for plate in plates:
        try:
            count_res = (
                supabase.table("memory_plates")
                .select("id", count="exact")
                .eq("plate_id", plate["id"])
                .execute()
            )
            plate["item_count"] = count_res.count or 0
        except Exception:
            plate["item_count"] = 0

    return {"data": plates}


@router.get("/{plate_id}")
async def get_plate(
    plate_id: str,
    user_id: str = Depends(get_current_user),
):
    """Get a specific plate by ID."""
    supabase = get_supabase_client()

    res = (
        supabase.table("plates")
        .select("*")
        .eq("id", plate_id)
        .eq("user_id", user_id)
        .execute()
    )

    if not res.data:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Plate not found")

    plate = res.data[0]

    # Get memories in this plate
    mem_res = (
        supabase.table("memory_plates")
        .select("memory_id")
        .eq("plate_id", plate_id)
        .execute()
    )
    plate["memory_ids"] = [m["memory_id"] for m in (mem_res.data or [])]
    plate["item_count"] = len(plate["memory_ids"])

    return plate
