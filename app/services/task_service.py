"""
Service for managing Celery tasks
"""
from celery.result import AsyncResult
from typing import Dict, Optional
from app.celery_app import celery_app

class TaskService:
    """Service for task status and management"""

    @staticmethod
    def get_task_status(task_id: str) -> Dict:
        """
        Get status of a Celery task

        Returns:
            dict: Task status information
        """
        task = AsyncResult(task_id, app=celery_app)

        response = {
            "task_id": task_id,
            "status": task.state,
            "result": None,
            "error": None
        }

        if task.state == "PENDING":
            response["status"] = "pending"
        elif task.state == "STARTED":
            response["status"] = "processing"
        elif task.state == "SUCCESS":
            response["status"] = "completed"
            response["result"] = task.result
        elif task.state == "FAILURE":
            response["status"] = "failed"
            response["error"] = str(task.info)
        elif task.state == "RETRY":
            response["status"] = "retrying"

        return response

    @staticmethod
    def cancel_task(task_id: str) -> bool:
        """
        Cancel a running task

        Returns:
            bool: True if cancelled successfully
        """
        task = AsyncResult(task_id, app=celery_app)
        task.revoke(terminate=True)
        return True

    @staticmethod
    def get_active_tasks() -> list:
        """Get list of active tasks"""
        inspect = celery_app.control.inspect()
        active = inspect.active()
        return active if active else []

task_service = TaskService()
