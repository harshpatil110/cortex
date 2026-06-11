import asyncio
import logging

from celery import shared_task

from services.graph_service import graph_service

logger = logging.getLogger(__name__)


@shared_task(name="map_relations")
def map_relations_task(
    memory_id: str, user_id: str, new_embedding: list[float], metadata: dict
):
    logger.info(f"Starting graph relationships mapping for {memory_id}")
    asyncio.run(
        graph_service.map_relationships(memory_id, user_id, new_embedding, metadata)
    )
