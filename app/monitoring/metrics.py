"""
Prometheus Metrics for TrustCard

Tracks key performance indicators and system health metrics.
"""
from prometheus_client import Counter, Histogram, Gauge, Info
import time
from functools import wraps
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# HTTP METRICS
# ============================================================================

# Request counter
http_requests_total = Counter(
    'trustcard_http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

# Request duration
http_request_duration_seconds = Histogram(
    'trustcard_http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0)
)

# Active requests
http_requests_in_progress = Gauge(
    'trustcard_http_requests_in_progress',
    'Number of HTTP requests currently being processed',
    ['method', 'endpoint']
)

# ============================================================================
# ANALYSIS METRICS
# ============================================================================

# Analysis submissions
analyses_submitted_total = Counter(
    'trustcard_analyses_submitted_total',
    'Total number of analysis requests submitted'
)

# Analysis completions
analyses_completed_total = Counter(
    'trustcard_analyses_completed_total',
    'Total number of analyses completed',
    ['status']  # completed, failed
)

# Analysis duration
analysis_duration_seconds = Histogram(
    'trustcard_analysis_duration_seconds',
    'Time taken to complete analysis',
    buckets=(1.0, 5.0, 10.0, 20.0, 30.0, 60.0, 120.0, 300.0)
)

# Active analyses
analyses_in_progress = Gauge(
    'trustcard_analyses_in_progress',
    'Number of analyses currently being processed'
)

# Trust score distribution
trust_score_distribution = Histogram(
    'trustcard_trust_score',
    'Distribution of trust scores',
    buckets=(0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100)
)

# ============================================================================
# CACHE METRICS
# ============================================================================

# Cache hits
cache_hits_total = Counter(
    'trustcard_cache_hits_total',
    'Total number of cache hits',
    ['cache_type']  # analysis, instagram
)

# Cache misses
cache_misses_total = Counter(
    'trustcard_cache_misses_total',
    'Total number of cache misses',
    ['cache_type']
)

# Cache size
cache_size_bytes = Gauge(
    'trustcard_cache_size_bytes',
    'Current size of cache in bytes',
    ['cache_type']
)

# ============================================================================
# DATABASE METRICS
# ============================================================================

# Database connections
db_connections_active = Gauge(
    'trustcard_db_connections_active',
    'Number of active database connections'
)

# Database query duration
db_query_duration_seconds = Histogram(
    'trustcard_db_query_duration_seconds',
    'Database query duration in seconds',
    ['operation'],  # select, insert, update, delete
    buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0)
)

# ============================================================================
# CELERY METRICS
# ============================================================================

# Task queue size
celery_queue_size = Gauge(
    'trustcard_celery_queue_size',
    'Number of tasks waiting in Celery queue'
)

# Task execution time
celery_task_duration_seconds = Histogram(
    'trustcard_celery_task_duration_seconds',
    'Celery task execution time',
    ['task_name'],
    buckets=(1.0, 5.0, 10.0, 20.0, 30.0, 60.0, 120.0, 300.0)
)

# Task status
celery_tasks_total = Counter(
    'trustcard_celery_tasks_total',
    'Total number of Celery tasks',
    ['task_name', 'status']  # success, failure, retry
)

# ============================================================================
# ML MODEL METRICS
# ============================================================================

# AI detection results
ai_detection_results_total = Counter(
    'trustcard_ai_detection_results_total',
    'AI detection results',
    ['result']  # ai_generated, human_made
)

# Deepfake detection results
deepfake_detection_results_total = Counter(
    'trustcard_deepfake_detection_results_total',
    'Deepfake detection results',
    ['result']  # suspicious, clean
)

# Model inference time
model_inference_duration_seconds = Histogram(
    'trustcard_model_inference_duration_seconds',
    'ML model inference time',
    ['model_name'],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0)
)

# ============================================================================
# COMMUNITY FEEDBACK METRICS
# ============================================================================

# Feedback submissions
feedback_submissions_total = Counter(
    'trustcard_feedback_submissions_total',
    'Total feedback submissions',
    ['vote_type']  # accurate, misleading, false
)

# ============================================================================
# SYSTEM INFO
# ============================================================================

# Application info
app_info = Info(
    'trustcard_app',
    'TrustCard application information'
)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def track_request_metrics(method: str, endpoint: str, status_code: int, duration: float):
    """Track HTTP request metrics"""
    http_requests_total.labels(
        method=method,
        endpoint=endpoint,
        status_code=status_code
    ).inc()

    http_request_duration_seconds.labels(
        method=method,
        endpoint=endpoint
    ).observe(duration)


def track_analysis_submitted():
    """Track analysis submission"""
    analyses_submitted_total.inc()
    analyses_in_progress.inc()


def track_analysis_completed(status: str, duration: float, trust_score: float = None):
    """Track analysis completion"""
    analyses_completed_total.labels(status=status).inc()
    analyses_in_progress.dec()

    if status == "completed" and duration:
        analysis_duration_seconds.observe(duration)

    if trust_score is not None:
        trust_score_distribution.observe(trust_score)


def track_cache_hit(cache_type: str):
    """Track cache hit"""
    cache_hits_total.labels(cache_type=cache_type).inc()


def track_cache_miss(cache_type: str):
    """Track cache miss"""
    cache_misses_total.labels(cache_type=cache_type).inc()


def track_feedback(vote_type: str):
    """Track community feedback"""
    feedback_submissions_total.labels(vote_type=vote_type).inc()


def track_ai_detection(is_ai_generated: bool):
    """Track AI detection result"""
    result = "ai_generated" if is_ai_generated else "human_made"
    ai_detection_results_total.labels(result=result).inc()


def track_deepfake_detection(is_suspicious: bool):
    """Track deepfake detection result"""
    result = "suspicious" if is_suspicious else "clean"
    deepfake_detection_results_total.labels(result=result).inc()


def track_model_inference(model_name: str, duration: float):
    """Track ML model inference time"""
    model_inference_duration_seconds.labels(model_name=model_name).observe(duration)


def time_function(metric_histogram, label_value: str = None):
    """
    Decorator to time function execution

    Usage:
        @time_function(celery_task_duration_seconds, "task_name")
        def my_task():
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                if label_value:
                    metric_histogram.labels(label_value).observe(duration)
                else:
                    metric_histogram.observe(duration)
        return wrapper
    return decorator


# Initialize app info
def init_metrics(version: str, environment: str):
    """Initialize metrics with app info"""
    app_info.info({
        'version': version,
        'environment': environment,
        'app_name': 'TrustCard'
    })
    logger.info(f"Metrics initialized: version={version}, environment={environment}")
