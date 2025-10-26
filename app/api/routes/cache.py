"""
Cache Management API Endpoints

Provides endpoints for monitoring and managing the Redis cache.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict

from app.services.cache_manager import cache_manager

router = APIRouter(prefix="/api/cache", tags=["cache"])


@router.get("/stats")
async def get_cache_stats() -> Dict:
    """
    Get cache statistics.

    Returns:
        - Connection status
        - Number of cached items
        - Memory usage
        - Cache hit rate

    Useful for monitoring cache performance.
    """
    stats = cache_manager.get_cache_stats()
    return stats


@router.delete("/clear")
async def clear_cache():
    """
    Clear all TrustCard cache.

    **⚠️ Use with caution in production!**

    This will force all subsequent requests to re-analyze content,
    even if it was previously analyzed.

    Use cases:
    - Development/testing
    - After major algorithm updates
    - When cache data is suspected to be stale
    """
    success = cache_manager.clear_all_cache()

    if success:
        return {
            "message": "Cache cleared successfully",
            "status": "success"
        }
    else:
        raise HTTPException(
            status_code=500,
            detail="Failed to clear cache"
        )


@router.delete("/analysis/{instagram_url:path}")
async def invalidate_analysis_cache(instagram_url: str):
    """
    Invalidate cache for specific Instagram URL.

    Forces re-analysis on next request for this URL.

    Use cases:
    - Post content has been updated/edited
    - Need to refresh analysis with latest algorithm
    - Incorrect analysis needs to be redone

    Args:
        instagram_url: Full Instagram post URL (path parameter)

    Returns:
        Confirmation message
    """
    success = cache_manager.invalidate_analysis(instagram_url)

    if success:
        return {
            "message": f"Cache invalidated for {instagram_url}",
            "status": "success"
        }
    else:
        raise HTTPException(
            status_code=500,
            detail="Failed to invalidate cache"
        )
