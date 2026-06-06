import os

from celery import Celery
from celery.schedules import crontab
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL")

if REDIS_URL and REDIS_URL.startswith("rediss://") and "ssl_cert_reqs" not in REDIS_URL:
    if "?" in REDIS_URL:
        REDIS_URL += "&ssl_cert_reqs=CERT_NONE"
    else:
        REDIS_URL += "?ssl_cert_reqs=CERT_NONE"

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
    broker_use_ssl=(
        {"ssl_cert_reqs": "CERT_NONE"}
        if REDIS_URL and REDIS_URL.startswith("rediss://")
        else None
    ),
    redis_backend_use_ssl=(
        {"ssl_cert_reqs": "CERT_NONE"}
        if REDIS_URL and REDIS_URL.startswith("rediss://")
        else None
    ),
)

celery_app.conf.beat_schedule = {
    "nightly-reclustering": {
        "task": "workers.process_memory.recluster_task",
        "schedule": crontab(hour=3, minute=0),
    },
}
