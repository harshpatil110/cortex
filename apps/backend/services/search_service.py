import logging
from typing import Optional

from services.embedding_service import embedding_service
from utils.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)


class SearchService:
    def lexical_search(
        self,
        user_id: str,
        q: str,
        limit: int = 20,
        offset: int = 0,
        content_type: Optional[str] = None,
        plate_id: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> tuple[list[dict], int]:
        supabase = get_supabase_client()
        if not supabase:
            raise RuntimeError("Supabase client is not available.")

        # Prepare parameters for the RPC call
        rpc_params = {
            "query_text": q,
            "p_user_id": user_id,
            "p_limit": limit,
            "p_offset": offset,
        }
        if content_type:
            rpc_params["p_content_type"] = content_type
        if plate_id:
            rpc_params["p_plate_id"] = plate_id
        if date_from:
            rpc_params["p_date_from"] = date_from
        if date_to:
            rpc_params["p_date_to"] = date_to

        # Execute RPC
        try:
            res = supabase.rpc("lexical_search_memories", rpc_params).execute()
        except Exception as e:
            logger.error(f"Failed to execute lexical_search_memories RPC: {e}")
            raise RuntimeError("Failed to perform lexical search.") from e

        rows = res.data or []

        # Count total rows
        # The RPC should ideally return total_count alongside rows.
        # But if the RPC returns total_count in the first row, we can extract it.
        # Without knowing the exact RPC return type, let's assume 'total_count'
        # is a column in the returned rows. Let's extract total_count if present,
        # otherwise default to len(rows).
        total_count = 0
        if rows and "total_count" in rows[0]:
            total_count = rows[0]["total_count"]
        else:
            total_count = len(rows)  # Fallback

        cards = []
        for row in rows:
            # Generate 1-hour signed URL for thumbnail
            thumbnail_url = None
            thumbnail_path = row.get("thumbnail_path")
            if thumbnail_path:
                try:
                    signed_url_res = supabase.storage.from_(
                        "thumbnails"
                    ).create_signed_url(thumbnail_path, 3600)
                    thumbnail_url = signed_url_res.get("signedURL")
                except Exception as e:
                    logger.warning(
                        f"Failed to generate signed URL for {thumbnail_path}: {e}"
                    )

            # AI summary extraction
            ai_summary = row.get("ai_summary", {})
            title = (
                ai_summary.get("title", "Untitled")
                if isinstance(ai_summary, dict)
                else "Untitled"
            )
            abstract = (
                ai_summary.get("abstract", "") if isinstance(ai_summary, dict) else ""
            )
            tags = ai_summary.get("tags", []) if isinstance(ai_summary, dict) else []

            card = {
                "id": row.get("id"),
                "title": title,
                "abstract": abstract,
                "thumbnail_url": thumbnail_url,
                "source_url": row.get("source_url", ""),
                "content_type": row.get("content_type", ""),
                "tags": tags,
                "snippet": row.get("snippet", ""),
                "rank": row.get("rank", 0.0),
            }
            cards.append(card)

        return cards, total_count

    async def semantic_search(
        self,
        user_id: str,
        q: str,
        limit: int = 20,
        offset: int = 0,
        content_type: Optional[str] = None,
        plate_id: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> tuple[list[dict], int]:
        supabase = get_supabase_client()
        if not supabase:
            raise RuntimeError("Supabase client is not available.")

        # Vectorize query
        try:
            query_vector = await embedding_service.embed_text(q)
        except Exception as e:
            logger.error(f"Failed to vectorize query: {e}")
            raise RuntimeError("Failed to vectorize query.") from e

        # Query ChromaDB
        where_clause = {"user_id": user_id}
        if content_type:
            where_clause["content_type"] = content_type
        if plate_id:
            where_clause["plate_id"] = plate_id

        try:
            results = embedding_service.collection.query(
                query_embeddings=[query_vector],
                n_results=25,
                where=where_clause,
                include=["metadatas", "distances"],
            )
        except Exception as e:
            logger.error(f"Failed to query ChromaDB: {e}")
            raise RuntimeError("Failed to query ChromaDB.") from e

        if not results or not results["ids"] or not results["ids"][0]:
            return [], 0

        memory_ids = results["ids"][0]
        distances = results["distances"][0]

        filtered_ids = []
        similarity_scores = {}

        # Distance filtering > 0.65 discarded
        for m_id, dist in zip(memory_ids, distances):
            if dist <= 0.65:
                filtered_ids.append(m_id)
                similarity_scores[m_id] = 1.0 - dist

        if not filtered_ids:
            return [], 0

        # Hydrate from Supabase
        try:
            query = supabase.table("user_memories").select("*").in_("id", filtered_ids)
            if date_from:
                query = query.gte("created_at", date_from)
            if date_to:
                query = query.lte("created_at", date_to)

            db_res = query.execute()
        except Exception as e:
            logger.error(f"Failed to fetch memories from Supabase: {e}")
            raise RuntimeError("Failed to fetch memories.") from e

        rows = db_res.data or []

        cards = []
        for row in rows:
            m_id = row.get("id")
            score = similarity_scores.get(m_id, 0.0)

            # Generate thumbnail signed URL
            thumbnail_url = None
            thumbnail_path = row.get("thumbnail_path")
            if thumbnail_path:
                try:
                    signed_url_res = supabase.storage.from_(
                        "thumbnails"
                    ).create_signed_url(thumbnail_path, 3600)
                    thumbnail_url = signed_url_res.get("signedURL")
                except Exception as e:
                    logger.warning(
                        f"Failed to generate signed URL for {thumbnail_path}: {e}"
                    )

            # Extract AI summary fields
            ai_summary = row.get("ai_summary", {})
            title = (
                ai_summary.get("title", "Untitled")
                if isinstance(ai_summary, dict)
                else "Untitled"
            )
            abstract = (
                ai_summary.get("abstract", "") if isinstance(ai_summary, dict) else ""
            )
            tags = ai_summary.get("tags", []) if isinstance(ai_summary, dict) else []

            card = {
                "id": m_id,
                "title": title,
                "abstract": abstract,
                "thumbnail_url": thumbnail_url,
                "source_url": row.get("source_url", ""),
                "content_type": row.get("content_type", ""),
                "tags": tags,
                "similarity_score": score,
            }
            cards.append(card)

        # Sort descending by similarity_score
        cards.sort(key=lambda x: x["similarity_score"], reverse=True)

        total_count = len(cards)

        # Slice for pagination
        paginated_cards = cards[offset : offset + limit]

        return paginated_cards, total_count


search_service = SearchService()
