from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response

from middleware.auth import get_current_user
from services.search_service import search_service

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("")
@router.get("/")
async def search_memories(
    response: Response,
    q: str,
    mode: str = "hybrid",
    page: int = 1,
    limit: int = 20,
    content_type: Optional[str] = None,
    plate_id: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    user_id: str = Depends(get_current_user),
):
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID not found in token")

    offset = (page - 1) * limit
    if offset < 0:
        offset = 0

    if mode == "lexical":
        try:
            cards, total_count = search_service.lexical_search(
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

    response.headers["X-Total-Count"] = str(total_count)
    return {"results": cards}
