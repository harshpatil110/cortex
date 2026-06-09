import asyncio
import logging

from celery import shared_task

from services.clustering_service import clustering_service
from services.embedding_service import embedding_service

# Supabase import removed

logger = logging.getLogger(__name__)


@shared_task(name="cluster_single_memory")
def cluster_single_memory_task(memory_id: str, user_id: str, tags: list[str]):
    """Background task to cluster a newly embedded memory immediately."""
    logger.info(f"Starting auto-clustering for memory {memory_id}")

    # Fetch embedding from ChromaDB
    try:
        docs = embedding_service.get_by_ids([memory_id])
        if not docs or not docs[0].get("embedding"):
            logger.warning(
                f"No embedding found in ChromaDB for memory {memory_id}. "
                "Skipping clustering."
            )
            return

        embedding = docs[0]["embedding"]
        asyncio.run(
            clustering_service.cluster_new_memory(memory_id, user_id, embedding, tags)
        )
    except Exception as e:
        logger.error(f"Failed to execute clustering for {memory_id}: {e}")
