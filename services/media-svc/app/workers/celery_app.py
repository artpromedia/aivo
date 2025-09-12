"""Celery application for background video processing tasks."""

import os

from celery import Celery

# Redis configuration for Celery
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Create Celery app
celery_app = Celery(
    "media-worker",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["app.workers.transcode"],
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    task_routes={
        "app.workers.transcode.transcode_to_hls": {"queue": "transcode"},
        "app.workers.transcode.cleanup_temp_files": {"queue": "cleanup"},
    },
    task_annotations={
        "app.workers.transcode.transcode_to_hls": {
            "rate_limit": "2/m",  # 2 transcoding tasks per minute
        },
    },
)

# Auto-discover tasks
celery_app.autodiscover_tasks(["app.workers"])
