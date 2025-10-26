"""
Celery tasks for TrustCard
"""
from app.tasks.test_tasks import add, sleep_task, long_running_task
from app.tasks.analysis_tasks import process_instagram_post, retry_failed_analyses

__all__ = [
    "add",
    "sleep_task",
    "long_running_task",
    "process_instagram_post",
    "retry_failed_analyses"
]
