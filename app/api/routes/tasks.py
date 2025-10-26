"""
API endpoints for task management and testing
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Any

from app.tasks.test_tasks import add, sleep_task, long_running_task
from app.services.task_service import task_service

router = APIRouter(prefix="/tasks", tags=["tasks"])

class TaskSubmitResponse(BaseModel):
    task_id: str
    status: str
    message: str

class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[Any] = None
    error: Optional[str] = None

@router.post("/test/add", response_model=TaskSubmitResponse)
async def test_add_task(x: int, y: int):
    """Test task: Add two numbers asynchronously"""
    task = add.delay(x, y)
    return {
        "task_id": task.id,
        "status": "submitted",
        "message": f"Task submitted to add {x} + {y}"
    }

@router.post("/test/sleep", response_model=TaskSubmitResponse)
async def test_sleep_task(seconds: int = 5):
    """Test task: Sleep for specified seconds"""
    if seconds > 30:
        raise HTTPException(status_code=400, detail="Maximum sleep time is 30 seconds")

    task = sleep_task.delay(seconds)
    return {
        "task_id": task.id,
        "status": "submitted",
        "message": f"Task submitted to sleep for {seconds} seconds"
    }

@router.post("/test/long", response_model=TaskSubmitResponse)
async def test_long_task():
    """Test task: Simulate long-running analysis"""
    task = long_running_task.delay()
    return {
        "task_id": task.id,
        "status": "submitted",
        "message": "Long-running task submitted (simulates analysis process)"
    }

@router.get("/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """Get status of any task by ID"""
    status = task_service.get_task_status(task_id)
    return status

@router.delete("/{task_id}")
async def cancel_task(task_id: str):
    """Cancel a running task"""
    success = task_service.cancel_task(task_id)
    return {
        "task_id": task_id,
        "cancelled": success,
        "message": "Task cancellation requested"
    }

@router.get("/")
async def get_active_tasks():
    """Get list of currently active tasks"""
    active = task_service.get_active_tasks()
    return {
        "active_tasks": active,
        "count": len(active) if active else 0
    }
