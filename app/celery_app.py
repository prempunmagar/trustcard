"""
Celery application configuration for TrustCard
"""
from celery import Celery
from app.config import settings

# Create Celery app
celery_app = Celery(
    "trustcard",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.analysis_tasks",
        "app.tasks.ai_detection_task",
        "app.tasks.ocr_task",
        "app.tasks.deepfake_task",
        "app.tasks.fact_checking_task",
        "app.tasks.source_evaluation_task",
        "app.tasks.test_tasks"
    ]  # Import task modules
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes max per task
    task_soft_time_limit=240,  # 4 minutes soft limit
    worker_prefetch_multiplier=1,  # Take one task at a time
    worker_max_tasks_per_child=50,  # Restart worker after 50 tasks (prevent memory leaks)
)

# Task routing (can add more queues later for different priorities)
celery_app.conf.task_routes = {
    "analysis.*": {"queue": "analysis"},
    "test.*": {"queue": "analysis"},
}

@celery_app.task(bind=True)
def debug_task(self):
    """Debug task to test Celery is working"""
    return f"Request: {self.request!r}"
