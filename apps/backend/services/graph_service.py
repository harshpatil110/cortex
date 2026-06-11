import logging
import uuid
from datetime import datetime

from services.embedding_service import embedding_service
from utils.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)


class GraphService:
    async def map_relationships(
        self, memory_id: str, user_id: str, new_embedding: list[float], metadata: dict
    ):
        logger.info(f"Mapping relationships for memory {memory_id}")
        supabase = get_supabase_client()
        if not supabase:
            logger.error("Supabase client not available.")
            return

        try:
            results = embedding_service.collection.query(
                query_embeddings=[new_embedding],
                n_results=16,  # 15 neighbors + itself
                where={"user_id": user_id},
                include=["metadatas", "distances"],
            )
        except Exception as e:
            logger.error(f"Failed to query ChromaDB for neighbors: {e}")
            return

        if not results or not results["ids"] or not results["ids"][0]:
            return

        memory_ids = results["ids"][0]
        distances = results["distances"][0]
        metadatas = results["metadatas"][0]

        neighbor_ids = []
        valid_neighbors = []
        for n_id, dist, meta in zip(memory_ids, distances, metadatas):
            if n_id == memory_id:
                continue
            if dist < 0.25:
                neighbor_ids.append(n_id)
                valid_neighbors.append({"id": n_id, "distance": dist, "metadata": meta})

        if not valid_neighbors:
            return

        all_ids_to_fetch = [memory_id] + neighbor_ids
        try:
            db_res = (
                supabase.table("user_memories")
                .select("id, creator_handle")
                .in_("id", all_ids_to_fetch)
                .execute()
            )
        except Exception as e:
            logger.error(f"Failed to fetch memory handles: {e}")
            return

        rows = db_res.data or []
        handles = {row["id"]: row.get("creator_handle", "") for row in rows}

        source_handle = handles.get(memory_id, "")
        source_tech = (
            set(metadata.get("tech_stack_csv", "").split(","))
            if metadata.get("tech_stack_csv")
            else set()
        )
        source_tech = {t.strip() for t in source_tech if t.strip()}

        for neighbor in valid_neighbors:
            target_id = neighbor["id"]
            distance = neighbor["distance"]
            target_meta = neighbor["metadata"] or {}

            target_handle = handles.get(target_id, "")
            target_tech = (
                set(target_meta.get("tech_stack_csv", "").split(","))
                if target_meta.get("tech_stack_csv")
                else set()
            )
            target_tech = {t.strip() for t in target_tech if t.strip()}

            relationship_type = "conceptual_link"
            if source_handle and target_handle and source_handle == target_handle:
                relationship_type = "same_creator"
            elif len(source_tech.intersection(target_tech)) >= 2:
                relationship_type = "shares_technology"

            weight = round(1 - distance, 4)

            try:
                query_str = (
                    f"and(source_asset_id.eq.{memory_id},"
                    f"target_asset_id.eq.{target_id}),"
                    f"and(source_asset_id.eq.{target_id},"
                    f"target_asset_id.eq.{memory_id})"
                )
                dup_res = (
                    supabase.table("entity_relationships")
                    .select("id")
                    .or_(query_str)
                    .execute()
                )

                if dup_res.data:
                    continue

                supabase.table("entity_relationships").insert(
                    {
                        "id": str(uuid.uuid4()),
                        "source_asset_id": memory_id,
                        "target_asset_id": target_id,
                        "relationship_type": relationship_type,
                        "weight": weight,
                        "created_at": datetime.utcnow().isoformat(),
                    }
                ).execute()
            except Exception as e:
                logger.error(
                    f"Failed to insert edge between {memory_id} and {target_id}: {e}"
                )


graph_service = GraphService()
