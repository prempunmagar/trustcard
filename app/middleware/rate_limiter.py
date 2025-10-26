"""
Rate Limiting Middleware

Implements in-memory rate limiting per IP address.
For production with multiple servers, consider using Redis-based rate limiting.
"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import time
import logging
from collections import defaultdict
from typing import Dict, Tuple

from app.config import settings
from app.exceptions import RateLimitExceeded

logger = logging.getLogger(__name__)


class InMemoryRateLimiter:
    """
    In-memory rate limiter with sliding window algorithm

    Tracks requests per IP with two windows:
    - Per minute (short-term burst protection)
    - Per hour (sustained traffic control)
    """

    def __init__(
        self,
        requests_per_minute: int = 10,
        requests_per_hour: int = 100
    ):
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour

        # Storage: {ip: [(timestamp1, timestamp2, ...)]}
        self.request_history: Dict[str, list] = defaultdict(list)

        # Cleanup counter
        self.cleanup_counter = 0
        self.cleanup_interval = 100  # Clean up every 100 requests

    def _cleanup_old_entries(self):
        """Remove old entries to prevent memory leak"""
        current_time = time.time()
        hour_ago = current_time - 3600

        # Remove IPs with no recent requests
        ips_to_remove = []
        for ip, timestamps in self.request_history.items():
            # Remove timestamps older than 1 hour
            self.request_history[ip] = [
                ts for ts in timestamps if ts > hour_ago
            ]
            # If no recent requests, mark for removal
            if not self.request_history[ip]:
                ips_to_remove.append(ip)

        for ip in ips_to_remove:
            del self.request_history[ip]

    def is_allowed(self, ip: str) -> Tuple[bool, int, str]:
        """
        Check if request is allowed

        Returns:
            (allowed: bool, retry_after: int, reason: str)
        """
        current_time = time.time()

        # Periodic cleanup
        self.cleanup_counter += 1
        if self.cleanup_counter >= self.cleanup_interval:
            self._cleanup_old_entries()
            self.cleanup_counter = 0

        # Get request history for this IP
        timestamps = self.request_history[ip]

        # Calculate time windows
        minute_ago = current_time - 60
        hour_ago = current_time - 3600

        # Count requests in each window
        requests_last_minute = sum(1 for ts in timestamps if ts > minute_ago)
        requests_last_hour = sum(1 for ts in timestamps if ts > hour_ago)

        # Check minute limit
        if requests_last_minute >= self.requests_per_minute:
            # Find oldest request in the minute window
            minute_timestamps = [ts for ts in timestamps if ts > minute_ago]
            if minute_timestamps:
                oldest = min(minute_timestamps)
                retry_after = int(60 - (current_time - oldest)) + 1
                return False, retry_after, "per-minute limit exceeded"

        # Check hour limit
        if requests_last_hour >= self.requests_per_hour:
            # Find oldest request in the hour window
            hour_timestamps = [ts for ts in timestamps if ts > hour_ago]
            if hour_timestamps:
                oldest = min(hour_timestamps)
                retry_after = int(3600 - (current_time - oldest)) + 1
                return False, retry_after, "per-hour limit exceeded"

        # Request allowed, record it
        self.request_history[ip].append(current_time)

        return True, 0, "allowed"

    def get_stats(self, ip: str) -> Dict:
        """Get rate limit stats for an IP"""
        current_time = time.time()
        minute_ago = current_time - 60
        hour_ago = current_time - 3600

        timestamps = self.request_history[ip]

        requests_last_minute = sum(1 for ts in timestamps if ts > minute_ago)
        requests_last_hour = sum(1 for ts in timestamps if ts > hour_ago)

        return {
            "requests_last_minute": requests_last_minute,
            "requests_last_hour": requests_last_hour,
            "limit_per_minute": self.requests_per_minute,
            "limit_per_hour": self.requests_per_hour,
            "remaining_minute": max(0, self.requests_per_minute - requests_last_minute),
            "remaining_hour": max(0, self.requests_per_hour - requests_last_hour)
        }


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for rate limiting

    Applies rate limiting to all requests except health checks and metrics.
    """

    def __init__(self, app, enabled: bool = True):
        super().__init__(app)
        self.enabled = enabled

        if enabled:
            self.rate_limiter = InMemoryRateLimiter(
                requests_per_minute=settings.RATE_LIMIT_PER_MINUTE,
                requests_per_hour=settings.RATE_LIMIT_PER_HOUR
            )
            logger.info(
                "Rate limiting enabled",
                extra={
                    "per_minute": settings.RATE_LIMIT_PER_MINUTE,
                    "per_hour": settings.RATE_LIMIT_PER_HOUR
                }
            )
        else:
            logger.info("Rate limiting disabled")

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting if disabled
        if not self.enabled:
            return await call_next(request)

        # Exempt paths from rate limiting
        exempt_paths = [
            "/health",
            "/metrics",
            "/docs",
            "/redoc",
            "/openapi.json"
        ]

        if any(request.url.path.startswith(path) for path in exempt_paths):
            return await call_next(request)

        # Get client IP
        client_ip = request.client.host if request.client else "unknown"

        # Check rate limit
        allowed, retry_after, reason = self.rate_limiter.is_allowed(client_ip)

        if not allowed:
            logger.warning(
                f"Rate limit exceeded: {client_ip}",
                extra={
                    "ip": client_ip,
                    "reason": reason,
                    "retry_after": retry_after,
                    "path": request.url.path
                }
            )

            # Return rate limit error
            return JSONResponse(
                status_code=429,
                content={
                    "error": "RATE_LIMIT_EXCEEDED",
                    "message": f"Rate limit exceeded: {reason}",
                    "details": {
                        "retry_after": retry_after,
                        "limit_per_minute": settings.RATE_LIMIT_PER_MINUTE,
                        "limit_per_hour": settings.RATE_LIMIT_PER_HOUR
                    },
                    "status_code": 429
                },
                headers={"Retry-After": str(retry_after)}
            )

        # Request allowed, add rate limit headers
        response = await call_next(request)

        # Add rate limit info to response headers
        stats = self.rate_limiter.get_stats(client_ip)
        response.headers["X-RateLimit-Limit-Minute"] = str(settings.RATE_LIMIT_PER_MINUTE)
        response.headers["X-RateLimit-Limit-Hour"] = str(settings.RATE_LIMIT_PER_HOUR)
        response.headers["X-RateLimit-Remaining-Minute"] = str(stats["remaining_minute"])
        response.headers["X-RateLimit-Remaining-Hour"] = str(stats["remaining_hour"])

        return response
