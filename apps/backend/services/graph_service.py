import logging

from services.embedding_service import embedding_service
from utils.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)


class GraphService:
    def map_relationships(
        self, memory_id: str, user_id: str, new_embedding: list[float], metadata: dict
    ) -> None:
        supabase = get_supabase_client()
        if not supabase:
            logger.error("Supabase client not available.")
            return

        try:
            results = embedding_service.collection.query(
                query_embeddings=[new_embedding],
                n_results=16,  # 15 neighbors + 1 self
                where={"user_id": user_id},
                include=["metadatas", "distances"],
            )
        except Exception as e:
            logger.error(f"Failed to query ChromaDB for relationships: {e}")
            return

        if not results or not results.get("ids") or not results["ids"][0]:
            return

        neighbor_ids = results["ids"][0]
        distances = results["distances"][0]
        metadatas = results["metadatas"][0]

        source_creator = metadata.get("creator_handle", "")
        source_tech_csv = metadata.get("tech_stack_csv", "")
        source_tech = set(source_tech_csv.split(",")) if source_tech_csv else set()
        source_tech.discard("")

        for n_id, dist, n_meta in zip(neighbor_ids, distances, metadatas):
            if n_id == memory_id:
                continue
            if dist >= 0.25:
                continue

            weight = round(1.0 - dist, 4)
            relationship_type = "conceptual_link"

            n_creator = n_meta.get("creator_handle", "")
            n_tech_csv = n_meta.get("tech_stack_csv", "")
            n_tech = set(n_tech_csv.split(",")) if n_tech_csv else set()
            n_tech.discard("")

            if source_creator and source_creator == n_creator:
                relationship_type = "same_creator"
            elif len(source_tech.intersection(n_tech)) >= 2:
                relationship_type = "shares_technology"

            try:
                # Prevent bidirectional duplicates
                check_res = (
                    supabase.table("entity_relationships")
                    .select("id, source_asset_id, target_asset_id")
                    .eq("user_id", user_id)
                    .in_("source_asset_id", [memory_id, n_id])
                    .in_("target_asset_id", [memory_id, n_id])
                    .execute()
                )

                edge_exists = False
                for edge in check_res.data:
                    if (
                        edge["source_asset_id"] == memory_id
                        and edge["target_asset_id"] == n_id
                    ) or (
                        edge["source_asset_id"] == n_id
                        and edge["target_asset_id"] == memory_id
                    ):
                        edge_exists = True
                        break

                if edge_exists:
                    continue

                supabase.table("entity_relationships").insert(
                    {
                        "user_id": user_id,
                        "source_asset_id": memory_id,
                        "target_asset_id": n_id,
                        "relationship_type": relationship_type,
                        "weight": weight,
                    }
                ).execute()

            except Exception as e:
                logger.error(f"Failed to process edge {memory_id} <-> {n_id}: {e}")


graph_service = GraphService()
