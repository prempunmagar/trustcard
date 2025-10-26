# Step 3: Redis & Celery Setup - Progress Log

**Status**: ✅ COMPLETED
**Date**: 2025-10-26

## Overview
Set up Redis as a message broker and Celery as a distributed task queue for asynchronous processing of ML models and long-running analysis tasks.

## Architecture Implemented

```
┌─────────────────────────────────────────────────────────────┐
│                    TrustCard Async Flow                      │
└─────────────────────────────────────────────────────────────┘

User Request
     │
     ▼
┌─────────────────────┐
│   FastAPI Server    │  (Port 8000)
│   /tasks/test/add   │
└─────────────────────┘
     │
     │ (1) Submit task to Celery
     │ Returns: {"task_id": "abc-123", "status": "submitted"}
     │
     ▼
┌─────────────────────┐
│   Redis (Broker)    │  (Port 6379, DB 0)
│   Task Queue        │
└─────────────────────┘
     │
     │ (2) Worker pulls task from queue
     │
     ▼
┌─────────────────────┐
│  Celery Worker      │  (Container: trustcard-celery-worker)
│  Executes task      │  - 24 concurrent workers (prefork)
└─────────────────────┘  - Analysis queue
     │
     │ (3) Store result
     │
     ▼
┌─────────────────────┐
│ Redis (Backend)     │  (Port 6379, DB 1)
│ Task Results        │
└─────────────────────┘
     │
     │ (4) Client checks status
     │
     ▼
┌─────────────────────┐
│   GET /tasks/{id}   │  Returns: {"status": "completed", "result": 15}
└─────────────────────┘
```

## Files Created

### 1. Celery Configuration
**File**: `app/celery_app.py`
- Created Celery app instance
- Configured Redis as broker and backend
- Set task time limits and worker policies
- Configured task routing to "analysis" queue

### 2. Test Tasks
**File**: `app/tasks/test_tasks.py`
- `test.add` - Simple addition task
- `test.sleep` - Sleep for N seconds
- `test.long_task` - 10-second simulation with 5 stages

### 3. Analysis Tasks Placeholder
**File**: `app/tasks/analysis_tasks.py`
- `analysis.process_post` - Main Instagram analysis task (placeholder)
- Will be filled with ML models in Steps 6-9

### 4. Task Service
**File**: `app/services/task_service.py`
- `get_task_status()` - Query task status from Celery
- `cancel_task()` - Terminate running task
- `get_active_tasks()` - List currently executing tasks

### 5. Task API Endpoints
**File**: `app/api/routes/tasks.py`
- `POST /tasks/test/add` - Submit addition task
- `POST /tasks/test/sleep` - Submit sleep task
- `POST /tasks/test/long` - Submit long-running simulation
- `GET /tasks/{task_id}` - Check task status
- `DELETE /tasks/{task_id}` - Cancel task
- `GET /tasks/` - List active tasks

### 6. Documentation
**File**: `docs/celery_guide.md`
- Complete guide to Celery setup
- API endpoint documentation
- Testing procedures
- Troubleshooting tips

## Files Modified

### 1. Configuration
**File**: `app/config.py`
- Added `REDIS_URL` setting
- Added `CELERY_BROKER_URL` setting
- Added `CELERY_RESULT_BACKEND` setting
- Added `SECRET_KEY` field (required by Pydantic Settings)

### 2. Main Application
**File**: `app/main.py`
- Imported and included task router
- Updated health check to test Redis connection

### 3. Docker Compose
**File**: `docker-compose.yml`
- Added `celery_worker` service
- Configured worker command: `celery -A app.celery_app worker --loglevel=info --queues=analysis`
- Connected to database, Redis, and mounted code volume

### 4. Environment Variables
**File**: `.env`
- Added `CELERY_BROKER_URL=redis://redis:6379/0`
- Added `CELERY_RESULT_BACKEND=redis://redis:6379/1`

### 5. Task Exports
**File**: `app/tasks/__init__.py`
- Exported all test tasks and analysis tasks

**File**: `app/services/__init__.py`
- Exported task_service instance

## Issues Encountered & Resolved

### Issue 1: SECRET_KEY Validation Error
**Problem**: Celery worker failed to start with `ValidationError: Extra inputs are not permitted - SECRET_KEY`

**Root Cause**: The `.env` file contained `SECRET_KEY` but the `Settings` class didn't have it as a field. Pydantic Settings was rejecting it.

**Solution**: Added `SECRET_KEY: str` field to `Settings` class in `app/config.py`

### Issue 2: Tasks Staying in "Pending" Status
**Problem**: Submitted tasks never executed, status remained "pending"

**Root Cause**: Task routing configuration used `"app.tasks.test_tasks.*"` pattern, but tasks were named `"test.add"`, `"test.sleep"`, etc. The routing pattern didn't match actual task names.

**Solution**: Updated task routing in `app/celery_app.py`:
```python
# Before
"app.tasks.test_tasks.*": {"queue": "analysis"}

# After
"test.*": {"queue": "analysis"}
```

### Issue 3: Task Status Response Validation Error
**Problem**: API returned `ResponseValidationError: Input should be a valid dictionary, input: 15`

**Root Cause**: `TaskStatusResponse` model defined `result: Optional[dict]`, but test.add task returned integer (15).

**Solution**: Changed response model to accept any type:
```python
# Before
result: Optional[dict] = None

# After
result: Optional[Any] = None
```

## Testing Results

### Test 1: Simple Addition Task
```bash
$ curl -X POST "http://localhost:8000/tasks/test/add?x=7&y=8"
Response: {"task_id": "520a8582-b553-44c4-8099-df7ce310367c", "status": "submitted"}

$ curl http://localhost:8000/tasks/520a8582-b553-44c4-8099-df7ce310367c
Response: {"task_id": "...", "status": "completed", "result": 15, "error": null}
```
✅ **Result**: Task executed in 0.006s, returned correct result (15)

### Test 2: Sleep Task
```bash
$ curl -X POST "http://localhost:8000/tasks/test/sleep?seconds=2"
Response: {"task_id": "12cbb922-b6a6-48fc-ad32-bfc5be8ca6d7", "status": "submitted"}

$ curl http://localhost:8000/tasks/12cbb922-b6a6-48fc-ad32-bfc5be8ca6d7
Response: {"status": "completed", "result": "Slept for 2 seconds", "error": null}
```
✅ **Result**: Task executed in 2.001s, returned expected message

### Test 3: Long-Running Task
```bash
$ curl -X POST "http://localhost:8000/tasks/test/long"
Response: {"task_id": "f30f13e6-b191-4da8-9ce7-3cccde450dd0", "status": "submitted"}

$ curl http://localhost:8000/tasks/f30f13e6-b191-4da8-9ce7-3cccde450dd0
Response: {
  "status": "completed",
  "result": {
    "status": "completed",
    "progress": [
      "Extracting Instagram content...",
      "Running AI detection...",
      "Checking for deepfakes...",
      "Fact-checking claims...",
      "Calculating trust score..."
    ],
    "percent": 100
  }
}
```
✅ **Result**: Task executed in 10.005s, tracked all 5 stages successfully

### Test 4: Health Check
```bash
$ curl http://localhost:8000/health
Response: {
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "celery": "configured"
}
```
✅ **Result**: All services connected and operational

### Test 5: Worker Logs
```
[2025-10-26 05:21:11,820] celery@f54d596b007f ready.
[2025-10-26 05:21:23,149] Task test.add[520a8582-...] received
[2025-10-26 05:21:23,157] Task test.add[520a8582-...] succeeded in 0.006s: 15
[2025-10-26 05:22:15,300] Task test.sleep[12cbb922-...] received
[2025-10-26 05:22:17,302] Task test.sleep[12cbb922-...] succeeded in 2.001s: 'Slept for 2 seconds'
[2025-10-26 05:22:25,854] Task test.long_task[f30f13e6-...] succeeded in 10.005s: {...}
```
✅ **Result**: All tasks received and executed by worker

## Configuration Summary

### Celery Settings
- **Broker**: redis://redis:6379/0
- **Backend**: redis://redis:6379/1
- **Task time limit**: 300s (5 minutes)
- **Soft time limit**: 240s (4 minutes)
- **Worker prefetch**: 1 task at a time
- **Worker restart**: After 50 tasks
- **Queue**: analysis
- **Serializer**: JSON

### Docker Containers
1. `trustcard-api` - FastAPI server (port 8000)
2. `trustcard-celery-worker` - Celery worker (24 processes)
3. `trustcard-db` - PostgreSQL (port 5432)
4. `trustcard-redis` - Redis (port 6379)

## What's Next

### Step 4: Instagram Integration
- Set up Instagram Basic Display API
- Create scraping utilities
- Handle media downloads
- Test with real Instagram posts

### Steps 6-9: ML Models
The `analysis.process_post` task placeholder is ready to be filled with:
- **Step 6**: AI-generated content detection
- **Step 7**: Deepfake detection
- **Step 8**: Fact-checking verification
- **Step 9**: Trust score calculation

All ML models will run asynchronously through the Celery infrastructure we've built.

## Lessons Learned

1. **Pydantic Settings Validation**: All environment variables must have corresponding fields in the Settings class, even if they're not directly used by the application.

2. **Task Routing Patterns**: Task routing patterns must match the actual task names (defined by `name` parameter in `@shared_task`), not the module path.

3. **Response Model Flexibility**: When tasks return different types of results, use `Optional[Any]` instead of specific types like `dict` to avoid validation errors.

4. **Worker Queue Configuration**: The `--queues` flag in the worker command must match the queue names in task routing configuration.

5. **Incremental Testing**: Testing each component (simple task → sleep task → long task) helped identify and fix issues early.

## Success Metrics

✅ Redis running and accessible
✅ Celery worker connected to Redis
✅ Task submission working via API
✅ Task execution in background
✅ Task status tracking functional
✅ Task results stored and retrievable
✅ Worker logs showing task execution
✅ Health check confirming all services
✅ Documentation created
✅ All tests passing

**Step 3: COMPLETED** 🎉
