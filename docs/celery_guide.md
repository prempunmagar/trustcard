# Celery Task Queue Guide

## Overview

TrustCard uses Celery for asynchronous task processing. This allows ML models and long-running analysis tasks to run in the background without blocking API responses.

## Architecture

```
API Request → Submit Task → Redis Queue → Celery Worker → Execute Task
     ↓                                                            ↓
  Return task_id ← ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ Store result in Redis
     ↓
Status Check → Redis → Return result
```

## Components

### 1. Redis (Message Broker & Result Backend)
- **Broker**: Stores task queue (redis://redis:6379/0)
- **Backend**: Stores task results (redis://redis:6379/1)
- Running in Docker container `trustcard-redis`

### 2. Celery Worker
- Consumes tasks from Redis queue
- Executes tasks in background
- Stores results back in Redis
- Running in Docker container `trustcard-celery-worker`

### 3. FastAPI (Task Submission)
- Accepts task requests via API
- Submits tasks to Celery
- Returns task_id immediately
- Provides status check endpoints

## Task Types

### Test Tasks (`app/tasks/test_tasks.py`)
1. **test.add** - Simple addition for testing
2. **test.sleep** - Sleeps for N seconds to test async behavior
3. **test.long_task** - Simulates 5-stage analysis process (10 seconds)

### Analysis Tasks (`app/tasks/analysis_tasks.py`)
1. **analysis.process_post** - Main task for analyzing Instagram posts
   - Extracts content
   - Runs AI detection models (Steps 6-9)
   - Calculates trust score
   - Stores results in database

## API Endpoints

### Submit Tasks
```bash
# Test addition
POST /tasks/test/add?x=5&y=3
Response: {"task_id": "...", "status": "submitted", "message": "..."}

# Test sleep
POST /tasks/test/sleep?seconds=5
Response: {"task_id": "...", "status": "submitted", "message": "..."}

# Test long-running simulation
POST /tasks/test/long
Response: {"task_id": "...", "status": "submitted", "message": "..."}
```

### Check Status
```bash
GET /tasks/{task_id}
Response: {
  "task_id": "520a8582-b553-44c4-8099-df7ce310367c",
  "status": "completed",
  "result": 15,
  "error": null
}
```

Status values:
- `pending` - Task in queue, not started
- `processing` - Task currently executing
- `completed` - Task finished successfully
- `failed` - Task encountered error
- `retrying` - Task failed, retrying

### List Active Tasks
```bash
GET /tasks/
Response: {
  "active_tasks": {"celery@worker": [...]},
  "count": 0
}
```

### Cancel Task
```bash
DELETE /tasks/{task_id}
Response: {
  "task_id": "...",
  "cancelled": true,
  "message": "Task cancellation requested"
}
```

## Configuration

### Celery App (`app/celery_app.py`)
```python
celery_app = Celery(
    "trustcard",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.analysis_tasks", "app.tasks.test_tasks"]
)
```

### Task Configuration
- **task_time_limit**: 300s (5 minutes hard limit)
- **task_soft_time_limit**: 240s (4 minutes soft warning)
- **worker_prefetch_multiplier**: 1 (take one task at a time)
- **worker_max_tasks_per_child**: 50 (restart worker after 50 tasks to prevent memory leaks)

### Task Routing
All tasks route to the `analysis` queue:
```python
celery_app.conf.task_routes = {
    "analysis.*": {"queue": "analysis"},
    "test.*": {"queue": "analysis"},
}
```

## Docker Setup

### docker-compose.yml
```yaml
celery_worker:
  build: .
  container_name: trustcard-celery-worker
  volumes:
    - .:/app
  environment:
    - DEBUG=True
    - DATABASE_URL=postgresql://trustcard:trustcard@db:5432/trustcard
    - REDIS_URL=redis://redis:6379/0
  depends_on:
    - db
    - redis
  command: celery -A app.celery_app worker --loglevel=info --queues=analysis
```

## Development Workflow

### Start Services
```bash
docker compose up -d
```

### Check Celery Worker Status
```bash
docker compose logs celery_worker
```

### Monitor Tasks
```bash
# Watch worker logs in real-time
docker compose logs -f celery_worker

# Check active tasks
curl http://localhost:8000/tasks/
```

### Restart Worker (after code changes)
```bash
docker compose restart celery_worker
```

## Testing

### 1. Simple Task Test
```bash
# Submit task
curl -X POST "http://localhost:8000/tasks/test/add?x=5&y=3"
# Returns: {"task_id": "abc-123", ...}

# Check status
curl http://localhost:8000/tasks/abc-123
# Returns: {"status": "completed", "result": 8, ...}
```

### 2. Long-Running Task Test
```bash
# Submit long task (10 seconds)
curl -X POST "http://localhost:8000/tasks/test/long"
# Returns: {"task_id": "def-456", ...}

# Check status while running
curl http://localhost:8000/tasks/def-456
# Returns: {"status": "processing", ...}

# Check after completion
curl http://localhost:8000/tasks/def-456
# Returns: {"status": "completed", "result": {...progress stages...}, ...}
```

## Troubleshooting

### Task stays "pending"
1. Check if Celery worker is running:
   ```bash
   docker compose ps celery_worker
   ```
2. Check worker logs for errors:
   ```bash
   docker compose logs celery_worker --tail 50
   ```
3. Verify task routing matches queue configuration

### Task fails
1. Check task logs:
   ```bash
   docker compose logs celery_worker | grep ERROR
   ```
2. Check task status for error message:
   ```bash
   curl http://localhost:8000/tasks/{task_id}
   ```

### Worker not connecting to Redis
1. Verify Redis is running:
   ```bash
   docker compose ps redis
   ```
2. Check Redis connection:
   ```bash
   curl http://localhost:8000/health
   ```

## Next Steps

In Steps 6-9, we'll fill the `analysis.process_post` task with actual ML models:
- Step 6: AI-generated content detection
- Step 7: Deepfake detection
- Step 8: Fact-checking verification
- Step 9: Trust score calculation

The Celery infrastructure is now ready to handle these long-running ML tasks asynchronously.
