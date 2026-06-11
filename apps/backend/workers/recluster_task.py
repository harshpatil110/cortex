import asyncio
import logging
import math
import uuid
from collections import Counter
from datetime import datetime, timezone

import numpy as np
from celery import shared_task
from postgrest.types import CountMethod
from sklearn.cluster import KMeans

from services.clustering_service import clustering_service
from services.embedding_service import embedding_service
from utils.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)


@shared_task(name="recluster_all_memories")
def recluster_all_memories():
    logger.info("Starting nightly re-clustering task.")
    supabase = get_supabase_client()
    if not supabase:
        logger.error("Supabase client not available.")
        return

    try:
        users_res = supabase.table("user_memories").select("user_id").execute()
        user_ids = list(
            set(
                [
                    row["user_id"]
                    for row in users_res.data
                    if isinstance(row, dict) and row.get("user_id")
                ]
            )
        )
    except Exception as e:
        logger.error(f"Failed to fetch users: {e}")
        return

    for user_id in user_ids:
        try:
            count_res = (
                supabase.table("user_memories")
                .select("id", count=CountMethod.exact)
                .eq("user_id", user_id)
                .execute()
            )
            total_memories = (
                count_res.count
                if hasattr(count_res, "count") and count_res.count is not None
                else len(count_res.data)
            )

            if total_memories <= 10:
                logger.info(
                    f"User {user_id} has {total_memories} memories (<=10), "
                    "skipping re-clustering."
                )
                continue

            results = embedding_service.collection.get(
                where={"user_id": user_id},  # type: ignore
                include=["embeddings", "metadatas", "documents"],
            )

            if not results or not results.get("embeddings"):
                continue

            ids = results["ids"]
            embeddings = results["embeddings"]
            metadatas = results["metadatas"]

            if len(ids) <= 10:
                continue

            num_clusters = int(math.sqrt(len(ids)))
            logger.info(
                f"Re-clustering {len(ids)} memories into {num_clusters} "
                f"plates for user {user_id}."
            )

            X = np.array(embeddings)
            kmeans = KMeans(
                n_clusters=num_clusters, random_state=42, n_init="auto"
            ).fit(X)
            labels = kmeans.labels_

            clusters = {}
            for i, label in enumerate(labels):
                if label not in clusters:
                    clusters[label] = {"ids": [], "embeddings": [], "tags": []}
                clusters[label]["ids"].append(ids[i])
                clusters[label]["embeddings"].append(embeddings[i])

                meta = metadatas[i] if metadatas else {}
                tags_csv = meta.get("tags_csv", "")
                if isinstance(tags_csv, str) and tags_csv:
                    clusters[label]["tags"].extend(tags_csv.split(","))

            # Delete old plates and memory_plates safely
            old_plates = (
                supabase.table("plates").select("id").eq("user_id", user_id).execute()
            )
            old_plate_ids = [p["id"] for p in old_plates.data if isinstance(p, dict)]
            if old_plate_ids:
                # supabase rest api has limit on how many items can be deleted
                # via in_, but usually fine for plate ids
                supabase.table("memory_plates").delete().in_(
                    "plate_id", old_plate_ids
                ).execute()
            supabase.table("plates").delete().eq("user_id", user_id).execute()

            async def process_cluster(cluster_data):
                plate_id = str(uuid.uuid4())

                top_tags = [
                    tag for tag, _ in Counter(cluster_data["tags"]).most_common(5)
                ]

                plate_name = await clustering_service._generate_plate_name(top_tags)

                centroid_ids = cluster_data["ids"][:50]

                supabase.table("plates").insert(
                    {
                        "id": plate_id,
                        "user_id": user_id,
                        "name": plate_name,
                        "item_count": len(cluster_data["ids"]),
                        "centroid_member_ids": centroid_ids,
                        "created_at": datetime.now(timezone.utc).isoformat(),
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    }
                ).execute()

                memory_plates_data = [
                    {"memory_id": mid, "plate_id": plate_id}
                    for mid in cluster_data["ids"]
                ]

                for i in range(0, len(memory_plates_data), 1000):
                    supabase.table("memory_plates").insert(
                        memory_plates_data[i : i + 1000]
                    ).execute()

                for mid in cluster_data["ids"]:
                    doc = embedding_service.get_by_ids([mid])
                    if doc and len(doc) > 0:
                        meta = doc[0].get("metadata")
                        if meta:
                            meta["plate_id"] = plate_id
                            embedding_service.collection.update(
                                ids=[mid], metadatas=[meta]
                            )

            async def run_all():
                tasks = [process_cluster(c) for c in clusters.values()]
                await asyncio.gather(*tasks)

            asyncio.run(run_all())

        except Exception as e:
            logger.error(f"Re-clustering failed for user {user_id}: {e}")
