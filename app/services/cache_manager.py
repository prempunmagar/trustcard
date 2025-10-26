"""
Redis Cache Manager

Handles caching of analysis results and Instagram content for performance optimization.
"""

import redis
import json
import logging
from typing import Optional, Dict, Any
from datetime import timedelta

from app.config import settings

logger = logging.getLogger(__name__)


class CacheManager:
    """Redis cache manager for TrustCard"""

    def __init__(self):
        self.redis_client = None
        self._connect()

    def _connect(self):
        """Connect to Redis"""
        try:
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True
            )
            # Test connection
            self.redis_client.ping()
            logger.info("✅ Connected to Redis cache")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Redis: {e}")
            self.redis_client = None

    def _get_analysis_key(self, instagram_url: str) -> str:
        """Generate cache key for analysis results"""
        return f"trustcard:analysis:{instagram_url}"

    def _get_instagram_content_key(self, post_id: str) -> str:
        """Generate cache key for Instagram content"""
        return f"trustcard:instagram:{post_id}"

    def _get_source_key(self, domain: str) -> str:
        """Generate cache key for source credibility"""
        return f"trustcard:source:{domain}"

    def cache_analysis_result(
        self,
        instagram_url: str,
        analysis_data: Dict[str, Any],
        ttl_days: int = 7
    ) -> bool:
        """
        Cache complete analysis results.

        Args:
            instagram_url: Instagram post URL
            analysis_data: Complete analysis results
            ttl_days: Time to live in days

        Returns:
            bool: Success status
        """
        if not self.redis_client:
            return False

        try:
            key = self._get_analysis_key(instagram_url)
            value = json.dumps(analysis_data)
            ttl = timedelta(days=ttl_days)

            self.redis_client.setex(
                key,
                ttl,
                value
            )

            logger.info(f"✅ Cached analysis for {instagram_url}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to cache analysis: {e}")
            return False

    def get_cached_analysis(self, instagram_url: str) -> Optional[Dict[str, Any]]:
        """
        Get cached analysis results.

        Args:
            instagram_url: Instagram post URL

        Returns:
            dict: Cached analysis data or None
        """
        if not self.redis_client:
            return None

        try:
            key = self._get_analysis_key(instagram_url)
            cached = self.redis_client.get(key)

            if cached:
                logger.info(f"🚀 Cache HIT for {instagram_url}")
                return json.loads(cached)
            else:
                logger.info(f"❌ Cache MISS for {instagram_url}")
                return None

        except Exception as e:
            logger.error(f"❌ Failed to get cached analysis: {e}")
            return None

    def cache_instagram_content(
        self,
        post_id: str,
        content: Dict[str, Any],
        ttl_hours: int = 24
    ) -> bool:
        """
        Cache Instagram content.

        Args:
            post_id: Instagram post ID
            content: Scraped Instagram content
            ttl_hours: Time to live in hours

        Returns:
            bool: Success status
        """
        if not self.redis_client:
            return False

        try:
            key = self._get_instagram_content_key(post_id)
            value = json.dumps(content)
            ttl = timedelta(hours=ttl_hours)

            self.redis_client.setex(
                key,
                ttl,
                value
            )

            logger.info(f"✅ Cached Instagram content for {post_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to cache Instagram content: {e}")
            return False

    def get_cached_instagram_content(self, post_id: str) -> Optional[Dict[str, Any]]:
        """
        Get cached Instagram content.

        Args:
            post_id: Instagram post ID

        Returns:
            dict: Cached content or None
        """
        if not self.redis_client:
            return None

        try:
            key = self._get_instagram_content_key(post_id)
            cached = self.redis_client.get(key)

            if cached:
                logger.info(f"🚀 Instagram cache HIT for {post_id}")
                return json.loads(cached)
            else:
                logger.info(f"❌ Instagram cache MISS for {post_id}")
                return None

        except Exception as e:
            logger.error(f"❌ Failed to get cached Instagram content: {e}")
            return None

    def invalidate_analysis(self, instagram_url: str) -> bool:
        """
        Invalidate cached analysis.

        Args:
            instagram_url: Instagram post URL

        Returns:
            bool: Success status
        """
        if not self.redis_client:
            return False

        try:
            key = self._get_analysis_key(instagram_url)
            self.redis_client.delete(key)
            logger.info(f"✅ Invalidated cache for {instagram_url}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to invalidate cache: {e}")
            return False

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            dict: Cache statistics including hit rate, memory usage, key counts
        """
        if not self.redis_client:
            return {"status": "disconnected"}

        try:
            info = self.redis_client.info()

            # Count TrustCard keys
            analysis_keys = len(self.redis_client.keys("trustcard:analysis:*"))
            instagram_keys = len(self.redis_client.keys("trustcard:instagram:*"))

            return {
                "status": "connected",
                "total_keys": info.get("db0", {}).get("keys", 0),
                "analysis_cached": analysis_keys,
                "instagram_cached": instagram_keys,
                "memory_used": info.get("used_memory_human", "N/A"),
                "hit_rate": self._calculate_hit_rate()
            }
        except Exception as e:
            logger.error(f"❌ Failed to get cache stats: {e}")
            return {"status": "error", "error": str(e)}

    def _calculate_hit_rate(self) -> float:
        """
        Calculate cache hit rate.

        Returns:
            float: Hit rate percentage
        """
        try:
            stats = self.redis_client.info("stats")
            hits = stats.get("keyspace_hits", 0)
            misses = stats.get("keyspace_misses", 0)

            if hits + misses == 0:
                return 0.0

            return round(hits / (hits + misses) * 100, 2)
        except:
            return 0.0

    def clear_all_cache(self) -> bool:
        """
        Clear all TrustCard cache.

        ⚠️ Use with caution in production!

        Returns:
            bool: Success status
        """
        if not self.redis_client:
            return False

        try:
            # Only delete TrustCard keys
            for pattern in ["trustcard:analysis:*", "trustcard:instagram:*"]:
                keys = self.redis_client.keys(pattern)
                if keys:
                    self.redis_client.delete(*keys)

            logger.info("✅ Cleared all TrustCard cache")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to clear cache: {e}")
            return False


# Singleton instance
cache_manager = CacheManager()
