"""
TrustCard - Every post gets a report card
Main FastAPI application entry point
"""
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging

from app.config import settings
from app.database import get_db
from app.api.routes import tasks, instagram, analysis, reports, cache, monitoring
from app.exceptions import (
    TrustCardException,
    InstagramScrapingError,
    AnalysisError,
    CacheError,
    RateLimitExceeded,
    InvalidInputError,
    DatabaseError,
    ResourceNotFoundError,
    TaskError,
    ConfigurationError,
    ExternalServiceError
)
from app.logging_config import setup_logging

# Initialize logging
setup_logging(
    log_level=settings.LOG_LEVEL,
    environment=settings.ENVIRONMENT,
    log_file=settings.LOG_FILE
)

logger = logging.getLogger(__name__)

# API metadata
API_DESCRIPTION = """
# TrustCard API

**"Every post gets a report card"**

TrustCard is a comprehensive fact-checking and content verification system for Instagram posts,
combining AI analysis, fact-checking, and community feedback to generate trust scores.

## Features

🤖 **AI-Powered Analysis**
- AI-generated content detection
- Deepfake detection for videos
- OCR for text extraction

✅ **Fact-Checking**
- Automated claim extraction
- Source credibility evaluation
- Citation verification

📊 **Trust Scoring**
- Comprehensive trust scores (0-100)
- Letter grades (A+ to F)
- Detailed score breakdowns

👥 **Community Feedback**
- Anonymous voting (Accurate/Misleading/False)
- IP-based duplicate prevention
- Community wisdom integration

📄 **Report Generation**
- Beautiful HTML report cards
- Shareable and print-ready
- Professional design

⚡ **Performance**
- Redis caching (28x faster for cached requests)
- Async processing with Celery
- Parallel ML pipeline

## Getting Started

1. Submit an Instagram post URL to `/api/analyze`
2. Poll `/api/results/{analysis_id}` for completion
3. View HTML report at `/api/reports/{analysis_id}`
4. Submit community feedback via `/api/reports/{analysis_id}/feedback`

## Rate Limits

- **Per Minute**: 10 requests per IP
- **Per Hour**: 100 requests per IP

Rate limit info is provided in response headers (`X-RateLimit-*`).

## Support

- 📖 API Documentation: [/docs](/docs)
- 💚 Health Check: [/health](/health)
- 📊 Metrics (Prometheus): [/metrics](/metrics)
- ℹ️ System Status: [/status](/status)
"""

# API tags metadata
tags_metadata = [
    {
        "name": "monitoring",
        "description": "Health checks, metrics, and system status endpoints"
    },
    {
        "name": "analysis",
        "description": "Core analysis submission and results retrieval"
    },
    {
        "name": "reports",
        "description": "HTML report generation and community feedback"
    },
    {
        "name": "cache",
        "description": "Cache management and statistics"
    },
    {
        "name": "tasks",
        "description": "Celery task management (debugging)"
    },
    {
        "name": "instagram",
        "description": "Instagram utilities (debugging)"
    }
]

app = FastAPI(
    title="TrustCard API",
    description=API_DESCRIPTION,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=tags_metadata,
    contact={
        "name": "TrustCard Team",
        "url": "https://github.com/yourusername/trustcard",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    terms_of_service="https://trustcard.example.com/terms"
)


# ============================================================================
# GLOBAL EXCEPTION HANDLERS
# ============================================================================

@app.exception_handler(TrustCardException)
async def trustcard_exception_handler(request: Request, exc: TrustCardException):
    """Handle all custom TrustCard exceptions"""
    logger.error(
        f"TrustCardException: {exc.error_code}",
        extra={
            "error_code": exc.error_code,
            "message": exc.message,
            "details": exc.details,
            "path": request.url.path,
            "method": request.method
        }
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict()
    )


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Handle rate limit errors with Retry-After header"""
    logger.warning(
        f"Rate limit exceeded: {request.client.host}",
        extra={"ip": request.client.host, "path": request.url.path}
    )
    headers = {}
    if exc.details.get("retry_after"):
        headers["Retry-After"] = str(exc.details["retry_after"])

    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict(),
        headers=headers
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Catch-all handler for unhandled exceptions"""
    logger.error(
        f"Unhandled exception: {type(exc).__name__}: {str(exc)}",
        extra={
            "exception_type": type(exc).__name__,
            "path": request.url.path,
            "method": request.method
        },
        exc_info=True  # Include stack trace in logs
    )

    # Never expose internal errors to users
    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred. Please try again later.",
            "details": {},
            "status_code": 500
        }
    )


# ============================================================================
# MIDDLEWARE
# ============================================================================

from app.middleware.rate_limiter import RateLimitMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware

# Security headers (applied first)
app.add_middleware(SecurityHeadersMiddleware)

# Rate limiting
app.add_middleware(RateLimitMiddleware, enabled=settings.RATE_LIMIT_ENABLED)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# Include routers
app.include_router(monitoring.router)  # Monitoring and health checks
app.include_router(analysis.router)    # Main API endpoints
app.include_router(reports.router)     # Report generation and community feedback
app.include_router(cache.router)       # Cache management
app.include_router(tasks.router)       # Task management (debugging)
app.include_router(instagram.router)   # Instagram utilities (debugging)

@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    # Initialize metrics
    if settings.ENABLE_METRICS:
        from app.monitoring.metrics import init_metrics
        init_metrics(
            version=settings.APP_VERSION,
            environment=settings.ENVIRONMENT
        )

    print("=" * 60)
    print("🚀 Starting TrustCard API")
    print("   Tagline: Every post gets a report card")
    print("=" * 60)
    print(f"   Environment: {settings.ENVIRONMENT}")
    print(f"   Version: {settings.APP_VERSION}")
    print("=" * 60)
    print("✅ Database connection ready")
    print("✅ Redis connection ready")
    print("✅ Celery configured")
    print("✅ Instagram service initialized")
    print(f"✅ Rate limiting: {'enabled' if settings.RATE_LIMIT_ENABLED else 'disabled'}")
    print(f"✅ Metrics: {'enabled' if settings.ENABLE_METRICS else 'disabled'}")
    print("=" * 60)
    print(f"📖 API Documentation: http://localhost:{settings.API_PORT}/docs")
    if settings.ENABLE_METRICS:
        print(f"📊 Metrics: http://localhost:{settings.API_PORT}/metrics")
    print(f"💚 Health: http://localhost:{settings.API_PORT}/health")
    print("=" * 60)

@app.get("/")
async def root():
    """Welcome endpoint"""
    return {
        "message": "Welcome to TrustCard API",
        "tagline": "Every post gets a report card",
        "status": "operational",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "documentation": "/docs",
        "endpoints": {
            "health": "GET /health",
            "metrics": "GET /metrics" if settings.ENABLE_METRICS else None,
            "status": "GET /status",
            "submit_analysis": "POST /api/analyze",
            "get_results": "GET /api/results/{analysis_id}",
            "list_analyses": "GET /api/results",
            "get_report": "GET /api/reports/{analysis_id}",
            "submit_feedback": "POST /api/reports/{analysis_id}/feedback",
            "get_feedback": "GET /api/reports/{analysis_id}/feedback",
            "cache_stats": "GET /api/cache/stats",
            "clear_cache": "DELETE /api/cache/clear"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
