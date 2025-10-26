"""
Monitoring and Health Check Endpoints

Provides endpoints for:
- Prometheus metrics
- Health checks
- System status
"""
from fastapi import APIRouter, Depends
from fastapi.responses import Response, JSONResponse
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging

from app.config import settings
from app.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(tags=["monitoring"])


@router.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint

    Returns metrics in Prometheus text format.
    Should be scraped by Prometheus server.
    """
    if not settings.ENABLE_METRICS:
        return JSONResponse(
            status_code=404,
            content={"error": "Metrics disabled"}
        )

    # Generate Prometheus metrics
    metrics_output = generate_latest()

    return Response(
        content=metrics_output,
        media_type=CONTENT_TYPE_LATEST
    )


@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """
    Comprehensive health check

    Returns:
    - Overall status (healthy/unhealthy)
    - Database connection status
    - Redis connection status
    - Celery status
    - Instagram service status
    """
    health_status = {
        "status": "healthy",
        "checks": {}
    }

    # Database check
    try:
        db.execute(text("SELECT 1"))
        health_status["checks"]["database"] = {
            "status": "up",
            "message": "Database connection successful"
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_status["status"] = "unhealthy"
        health_status["checks"]["database"] = {
            "status": "down",
            "message": f"Database error: {str(e)}"
        }

    # Redis check
    try:
        from app.celery_app import celery_app
        celery_app.backend.client.ping()
        health_status["checks"]["redis"] = {
            "status": "up",
            "message": "Redis connection successful"
        }
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        health_status["status"] = "unhealthy"
        health_status["checks"]["redis"] = {
            "status": "down",
            "message": f"Redis error: {str(e)}"
        }

    # Celery check
    try:
        from app.celery_app import celery_app
        # Check if Celery is configured
        health_status["checks"]["celery"] = {
            "status": "configured",
            "message": "Celery broker configured"
        }
    except Exception as e:
        logger.error(f"Celery health check failed: {e}")
        health_status["checks"]["celery"] = {
            "status": "unknown",
            "message": f"Celery error: {str(e)}"
        }

    # Instagram service check
    try:
        from app.services.instagram_service import instagram_service
        instagram_status = "authenticated" if instagram_service._authenticated else "not_authenticated"
        health_status["checks"]["instagram"] = {
            "status": instagram_status,
            "message": f"Instagram service is {instagram_status}"
        }
    except Exception as e:
        logger.error(f"Instagram health check failed: {e}")
        health_status["checks"]["instagram"] = {
            "status": "error",
            "message": f"Instagram service error: {str(e)}"
        }

    # Return appropriate status code
    status_code = 200 if health_status["status"] == "healthy" else 503

    return JSONResponse(
        status_code=status_code,
        content=health_status
    )


@router.get("/health/live")
async def liveness_probe():
    """
    Kubernetes liveness probe

    Simple check that the application is running.
    Returns 200 if the app is alive.
    """
    return {"status": "alive"}


@router.get("/health/ready")
async def readiness_probe(db: Session = Depends(get_db)):
    """
    Kubernetes readiness probe

    Checks if the application is ready to serve traffic.
    Returns 200 if ready, 503 if not ready.
    """
    try:
        # Check database connection
        db.execute(text("SELECT 1"))

        # Check Redis connection
        from app.celery_app import celery_app
        celery_app.backend.client.ping()

        return {"status": "ready"}

    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "error": str(e)
            }
        )


@router.get("/status")
async def system_status(db: Session = Depends(get_db)):
    """
    Detailed system status

    Returns:
    - Application version and environment
    - System components status
    - Configuration summary
    """
    # Get database stats
    try:
        from app.models.analysis import Analysis
        total_analyses = db.query(Analysis).count()
        completed_analyses = db.query(Analysis).filter(Analysis.status == "completed").count()
        pending_analyses = db.query(Analysis).filter(Analysis.status == "pending").count()
        processing_analyses = db.query(Analysis).filter(Analysis.status == "processing").count()

        db_stats = {
            "total_analyses": total_analyses,
            "completed": completed_analyses,
            "pending": pending_analyses,
            "processing": processing_analyses
        }
    except Exception as e:
        logger.error(f"Failed to get database stats: {e}")
        db_stats = {"error": str(e)}

    # Get cache stats
    try:
        from app.services.cache_manager import cache_manager
        cache_stats = cache_manager.get_cache_stats()
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        cache_stats = {"error": str(e)}

    return {
        "application": {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT
        },
        "configuration": {
            "rate_limiting_enabled": settings.RATE_LIMIT_ENABLED,
            "metrics_enabled": settings.ENABLE_METRICS,
            "debug_mode": settings.DEBUG
        },
        "database": db_stats,
        "cache": cache_stats
    }
