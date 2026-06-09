import asyncio
import logging
import os
import uuid
from datetime import datetime

import numpy as np

try:
    import google.generativeai as genai

    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

from services.embedding_service import embedding_service
from utils.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)


class ClusteringService:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if GENAI_AVAILABLE and self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel("gemini-1.5-flash")
        else:
            self.model = None

    def _cosine_similarity(self, vec1: list[float], vec2: list[float]) -> float:
        v1 = np.array(vec1)
        v2 = np.array(vec2)
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(np.dot(v1, v2) / (norm1 * norm2))

    async def _generate_plate_name(self, tags: list[str]) -> str:
        if not self.model or not tags:
            return "New Category"

        prompt = (
            "Given these technical tags, return a 2-3 word descriptive title "
            "for a category folder. Return ONLY the title string, no quotes, "
            f"no markdown. Tags: {', '.join(tags)}"
        )

        def _call_gemini():
            response = self.model.generate_content(prompt)
            return response.text.strip().replace('"', "").replace("'", "")

        try:
            return await asyncio.to_thread(_call_gemini)
        except Exception as e:
            logger.error(f"Gemini API failed to generate plate name: {e}")
            return "New Category"

    async def cluster_new_memory(
        self, memory_id: str, user_id: str, embedding: list[float], tags: list[str]
    ) -> None:
        """Assigns a new memory to an existing Plate or creates a new one."""
        supabase = get_supabase_client()
        if not supabase:
            logger.error("Supabase client not available for clustering.")
            return

        try:

            def _get_plates():
                return (
                    supabase.table("plates")
                    .select("*")
                    .eq("user_id", user_id)
                    .execute()
                )

            plates_res = await asyncio.to_thread(_get_plates)
            plates = plates_res.data
        except Exception as e:
            logger.error(f"Failed to fetch plates for user {user_id}: {e}")
            return

        best_plate_id = None
        max_sim = -1.0

        for plate in plates:
            centroid_ids = plate.get("centroid_member_ids", [])
            if not centroid_ids:
                continue

            def _get_embeddings():
                return embedding_service.get_by_ids(centroid_ids)

            docs = await asyncio.to_thread(_get_embeddings)

            valid_embeddings = []
            for doc in docs:
                if doc.get("embedding"):
                    valid_embeddings.append(doc["embedding"])

            if not valid_embeddings:
                continue

            centroid = np.mean(valid_embeddings, axis=0).tolist()

            sim = self._cosine_similarity(embedding, centroid)
            if sim > max_sim:
                max_sim = sim
                best_plate_id = plate.get("id")

        if max_sim > 0.72 and best_plate_id:
            target_plate_id = best_plate_id
            logger.info(
                f"Assigned memory {memory_id} to plate {target_plate_id} "
                f"(sim: {max_sim:.2f})"
            )

            target_plate = next((p for p in plates if p["id"] == target_plate_id), None)
            new_centroid_ids = (
                target_plate.get("centroid_member_ids", []) if target_plate else []
            )
            new_centroid_ids.append(memory_id)
            new_centroid_ids = new_centroid_ids[-50:]

            def _update_existing_plate():
                supabase.table("memory_plates").insert(
                    {"memory_id": memory_id, "plate_id": target_plate_id}
                ).execute()

                item_count = (target_plate.get("item_count") or 0) + 1
                supabase.table("plates").update(
                    {
                        "item_count": item_count,
                        "centroid_member_ids": new_centroid_ids,
                        "updated_at": datetime.utcnow().isoformat(),
                    }
                ).eq("id", target_plate_id).execute()

            try:
                await asyncio.to_thread(_update_existing_plate)
            except Exception as e:
                logger.error(f"Failed to update existing plate {target_plate_id}: {e}")

        else:
            plate_name = await self._generate_plate_name(tags)
            target_plate_id = str(uuid.uuid4())
            logger.info(
                f"Creating new plate '{plate_name}' (id: {target_plate_id}) "
                f"for memory {memory_id}"
            )

            def _create_new_plate():
                supabase.table("plates").insert(
                    {
                        "id": target_plate_id,
                        "user_id": user_id,
                        "name": plate_name,
                        "item_count": 1,
                        "centroid_member_ids": [memory_id],
                        "created_at": datetime.utcnow().isoformat(),
                        "updated_at": datetime.utcnow().isoformat(),
                    }
                ).execute()

                supabase.table("memory_plates").insert(
                    {"memory_id": memory_id, "plate_id": target_plate_id}
                ).execute()

            try:
                await asyncio.to_thread(_create_new_plate)
            except Exception as e:
                logger.error(f"Failed to create new plate for memory {memory_id}: {e}")

        def _update_chroma():
            doc = embedding_service.get_by_ids([memory_id])
            if doc and len(doc) > 0:
                meta = doc[0].get("metadata")
                if meta:
                    meta["plate_id"] = target_plate_id
                    embedding_service.collection.update(
                        ids=[memory_id], metadatas=[meta]
                    )

        try:
            await asyncio.to_thread(_update_chroma)
        except Exception as e:
            logger.error(f"Failed to update ChromaDB metadata for {memory_id}: {e}")


clustering_service = ClusteringService()
