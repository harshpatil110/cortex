from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException

from middleware.auth import get_current_user
from utils.supabase_client import get_supabase_client

router = APIRouter(prefix="/api/graph", tags=["graph"])


@router.get("")
@router.get("/")
async def get_graph(user_id: str = Depends(get_current_user)):
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID not found in token")

    supabase = get_supabase_client()
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase client not available")

    try:
        mem_res = (
            supabase.table("user_memories")
            .select("id, content_type, ai_summary")
            .eq("user_id", user_id)
            .execute()
        )
        user_memories = mem_res.data or []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if not user_memories:
        return {"nodes": [], "edges": []}

    memory_ids = [m["id"] for m in user_memories]

    all_edges = []
    for i in range(0, len(memory_ids), 500):
        chunk = memory_ids[i : i + 500]
        try:
            edges_res = (
                supabase.table("entity_relationships")
                .select("*")
                .in_("source_asset_id", chunk)
                .execute()
            )
            all_edges.extend(edges_res.data or [])
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    connection_count = defaultdict(int)
    for edge in all_edges:
        connection_count[edge["source_asset_id"]] += 1
        connection_count[edge["target_asset_id"]] += 1

    sorted_memories = sorted(
        user_memories, key=lambda x: connection_count[x["id"]], reverse=True
    )[:200]
    top_200_ids = {m["id"] for m in sorted_memories}

    nodes = []
    for m in sorted_memories:
        ai_summary = m.get("ai_summary", {})
        title = (
            ai_summary.get("title", "Untitled")
            if isinstance(ai_summary, dict)
            else "Untitled"
        )
        nodes.append(
            {
                "id": m["id"],
                "title": title,
                "content_type": m.get("content_type", ""),
                "connection_count": connection_count[m["id"]],
            }
        )

    edges = []
    for edge in all_edges:
        if (
            edge["source_asset_id"] in top_200_ids
            and edge["target_asset_id"] in top_200_ids
        ):
            edges.append(
                {
                    "id": edge["id"],
                    "source": edge["source_asset_id"],
                    "target": edge["target_asset_id"],
                    "relationship_type": edge.get("relationship_type", ""),
                    "weight": edge.get("weight", 1.0),
                }
            )

    return {"nodes": nodes, "edges": edges}
