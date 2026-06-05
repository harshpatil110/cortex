import os

from celery import Celery
from celery.schedules import crontab

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "cortex_backend",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["workers.process_memory"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

celery_app.conf.beat_schedule = {
    "nightly-reclustering": {
        "task": "workers.process_memory.recluster_task",
        "schedule": crontab(hour=3, minute=0),
    },
}
