import logging

from celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="workers.process_memory.process_memory_task")
def process_memory_task(job_id: str, memory_id: str, content_type: str):
    logger.info(
        f"Starting process_memory_task for Job: {job_id}, "
        f"Memory: {memory_id}, Type: {content_type}"
    )

    if content_type == "video":
        logger.info("Routing to video processor pipeline...")
    elif content_type == "document":
        logger.info("Routing to document processor pipeline...")
    else:
        logger.info("Routing to generic processor pipeline...")

    return {"status": "success", "job_id": job_id}


@celery_app.task(name="workers.process_memory.recluster_task")
def recluster_task():
    logger.info("Starting nightly re-clustering task...")
    return {"status": "success"}
