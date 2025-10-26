# Parallel Processing Guide

## Overview

TrustCard uses Celery's parallel processing (`group()` pattern) to run independent analyses simultaneously, reducing total analysis time by ~30-50%.

## Architecture

### Sequential Processing (Before Step 11)
```
Instagram (5s) → AI (10s) → OCR (8s) → Deepfake (15s) → Fact-Check (20s) → Source (3s)
TOTAL: ~61 seconds
```

### Parallel Processing (After Step 11)
```
Instagram (5s)
     ↓
  ┌──┴───┬─────┬────────┐
  │      │     │        │
 AI    OCR  Deepfake  (PARALLEL - run simultaneously)
10s     8s     15s
  │      │     │
  └──┬───┴─────┘
     ↓  (15s = longest task)
Fact-Check (20s) ← needs OCR text
     ↓
Source Eval (3s) ← needs text
     ↓
  Results

TOTAL: 5 + 15 + 20 + 3 = ~43 seconds (30% faster!)
```

## How It Works

### Celery Group Pattern

```python
from celery import group

# Create parallel task group
parallel_tasks = group([
    run_ai_detection.s(images),
    run_ocr_extraction.s(images, caption),
    run_deepfake_detection.s(videos, images)
])

# Execute all tasks in parallel
parallel_job = parallel_tasks.apply_async()

# Wait for all to complete (max 2 minutes)
results = parallel_job.get(timeout=120)

# Unpack results
ai_result = results[0]
ocr_result = results[1]
deepfake_result = results[2]
```

### Task Dependencies

**Independent Tasks (Parallel)**:
- AI Detection - only needs images
- OCR Extraction - only needs images + caption
- Deepfake Detection - only needs videos/images

**Dependent Tasks (Sequential)**:
- Fact-Checking - needs OCR extracted text
- Source Evaluation - needs text for URL extraction

## Task Modules

Created separate task modules for each analysis component:

1. **`ai_detection_task.py`** - AI image detection
2. **`ocr_task.py`** - OCR text extraction
3. **`deepfake_task.py`** - Deepfake/manipulation detection
4. **`fact_checking_task.py`** - Claim extraction & credibility analysis
5. **`source_evaluation_task.py`** - Source credibility evaluation

## Orchestrator

**`analysis_tasks.py`** coordinates the entire pipeline:

1. Extract Instagram content (sequential)
2. Launch parallel tasks (AI, OCR, Deepfake)
3. Wait for parallel completion
4. Run fact-checking (needs OCR text)
5. Run source evaluation (needs text)
6. Calculate trust score
7. Update database

## Performance Gains

| Component | Sequential | Parallel |
|-----------|-----------|----------|
| Instagram | 5s | 5s |
| AI Detection | 10s | - |
| OCR | 8s | - |
| Deepfake | 15s | - |
| **Parallel (all 3)** | **33s** | **15s*** |
| Fact-Check | 20s | 20s |
| Source Eval | 3s | 3s |
| **TOTAL** | **~61s** | **~43s** |

*Parallel time = longest individual task, not sum!

**Speed Improvement: ~30% faster**

## Testing

```bash
# Run performance test
python test_parallel_performance.py

# Enter Instagram URL when prompted
# Observe timing breakdown
```

## Configuration

**Celery Configuration** (`celery_app.py`):
- Includes all task modules
- Task time limit: 5 minutes
- Result expiry: 1 hour

**Worker Concurrency**:
```bash
# For better parallelization
celery -A app.celery_app worker --concurrency=4
```

## Monitoring

```bash
# View active tasks
celery -A app.celery_app inspect active

# View worker stats
celery -A app.celery_app inspect stats

# View registered tasks
celery -A app.celery_app inspect registered
```

## Benefits

✅ **Faster Analysis** - 30-50% reduction in total time
✅ **Better Resource Utilization** - Multiple CPU cores used
✅ **Modular Architecture** - Each task is independent
✅ **Easier Testing** - Individual tasks can be tested separately
✅ **Scalability** - Can add more workers for higher throughput

## Future Enhancements

- Dynamic task routing to multiple worker pools
- Priority queues for VIP users
- Streaming partial results as they complete
- Auto-scaling based on queue depth

---

**Implementation**: Step 11
**Status**: ✅ Complete
**Performance**: 30% faster than sequential processing
