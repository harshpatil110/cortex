import hashlib
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from middleware.auth import get_current_user
from services.cache_service import cache_service
from services.search_service import search_service
from utils.limiter import limiter

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("")
@router.get("/")
@limiter.limit("100/minute")
async def search_memories(
    request: Request,
    response: Response,
    q: str,
    limit: int = 20,
    offset: int = 0,
    content_type: Optional[str] = None,
    plate_id: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    mode: str = "hybrid",
    user_id: str = Depends(get_current_user),
):
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID not found in token")

    if offset < 0:
        offset = 0

    cache_key = None
    if mode == "hybrid":
        cache_key_str = (
            f"{user_id}:{q}:{limit}:{offset}:{content_type}:"
            f"{plate_id}:{date_from}:{date_to}"
        )
        cache_key = f"search:{hashlib.sha256(cache_key_str.encode()).hexdigest()}"
        cached_result = await cache_service.get(cache_key)
        if cached_result:
            response.headers["X-Total-Count"] = str(cached_result.get("total_count", 0))
            return {"results": cached_result.get("cards", [])}

    if mode == "lexical":
        try:
            cards, total_count = await search_service.lexical_search(
                user_id=user_id,
                q=q,
                limit=limit,
                offset=offset,
                content_type=content_type,
                plate_id=plate_id,
                date_from=date_from,
                date_to=date_to,
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    elif mode == "semantic":
        try:
            cards, total_count = await search_service.semantic_search(
                user_id=user_id,
                q=q,
                limit=limit,
                offset=offset,
                content_type=content_type,
                plate_id=plate_id,
                date_from=date_from,
                date_to=date_to,
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    elif mode == "hybrid":
        try:
            cards, total_count = await search_service.hybrid_search(
                user_id=user_id,
                q=q,
                limit=limit,
                offset=offset,
                content_type=content_type,
                plate_id=plate_id,
                date_from=date_from,
                date_to=date_to,
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    else:
        raise HTTPException(
            status_code=400,
            detail="Invalid mode. Must be 'lexical', 'semantic', or 'hybrid'.",
        )

    if mode == "hybrid" and cache_key:
        await cache_service.set(
            cache_key, {"cards": cards, "total_count": total_count}, 300
        )

    response.headers["X-Total-Count"] = str(total_count)
    return {"results": cards}
