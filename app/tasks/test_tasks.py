"""
Test tasks to verify Celery is working
"""
from celery import shared_task
import time

@shared_task(name="test.add")
def add(x: int, y: int) -> int:
    """Simple addition task for testing"""
    return x + y

@shared_task(name="test.sleep")
def sleep_task(seconds: int) -> str:
    """Task that sleeps for testing async behavior"""
    time.sleep(seconds)
    return f"Slept for {seconds} seconds"

@shared_task(name="test.long_task")
def long_running_task() -> dict:
    """Simulates a long-running analysis task"""
    import time

    results = {
        "status": "started",
        "progress": []
    }

    # Simulate different stages of analysis
    stages = [
        "Extracting Instagram content...",
        "Running AI detection...",
        "Checking for deepfakes...",
        "Fact-checking claims...",
        "Calculating trust score..."
    ]

    for i, stage in enumerate(stages):
        time.sleep(2)  # Simulate work
        results["progress"].append(stage)
        results["percent"] = (i + 1) * 20

    results["status"] = "completed"
    return results
