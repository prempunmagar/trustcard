"""
Custom Exceptions for TrustCard

Defines domain-specific exceptions for better error handling and user feedback.
"""
from typing import Optional


class TrustCardException(Exception):
    """Base exception for all TrustCard errors"""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: Optional[str] = None,
        details: Optional[dict] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self):
        """Convert exception to API response format"""
        return {
            "error": self.error_code,
            "message": self.message,
            "details": self.details,
            "status_code": self.status_code
        }


class InstagramScrapingError(TrustCardException):
    """Instagram scraping or API errors"""

    def __init__(self, message: str, post_id: Optional[str] = None, details: Optional[dict] = None):
        super().__init__(
            message=message,
            status_code=502,  # Bad Gateway - external service error
            error_code="INSTAGRAM_SCRAPING_ERROR",
            details={"post_id": post_id, **(details or {})}
        )


class AnalysisError(TrustCardException):
    """Analysis processing errors"""

    def __init__(self, message: str, analysis_id: Optional[str] = None, stage: Optional[str] = None):
        super().__init__(
            message=message,
            status_code=500,
            error_code="ANALYSIS_ERROR",
            details={"analysis_id": analysis_id, "stage": stage}
        )


class CacheError(TrustCardException):
    """Redis cache errors"""

    def __init__(self, message: str, operation: Optional[str] = None):
        super().__init__(
            message=message,
            status_code=503,  # Service Unavailable
            error_code="CACHE_ERROR",
            details={"operation": operation}
        )


class RateLimitExceeded(TrustCardException):
    """Rate limit exceeded"""

    def __init__(self, message: str = "Rate limit exceeded", retry_after: Optional[int] = None):
        super().__init__(
            message=message,
            status_code=429,  # Too Many Requests
            error_code="RATE_LIMIT_EXCEEDED",
            details={"retry_after": retry_after}
        )


class InvalidInputError(TrustCardException):
    """Invalid input validation errors"""

    def __init__(self, message: str, field: Optional[str] = None, value: Optional[str] = None):
        super().__init__(
            message=message,
            status_code=400,  # Bad Request
            error_code="INVALID_INPUT",
            details={"field": field, "value": value}
        )


class DatabaseError(TrustCardException):
    """Database operation errors"""

    def __init__(self, message: str, operation: Optional[str] = None):
        super().__init__(
            message=message,
            status_code=500,
            error_code="DATABASE_ERROR",
            details={"operation": operation}
        )


class ResourceNotFoundError(TrustCardException):
    """Resource not found errors"""

    def __init__(self, message: str, resource_type: Optional[str] = None, resource_id: Optional[str] = None):
        super().__init__(
            message=message,
            status_code=404,  # Not Found
            error_code="RESOURCE_NOT_FOUND",
            details={"resource_type": resource_type, "resource_id": resource_id}
        )


class TaskError(TrustCardException):
    """Celery task errors"""

    def __init__(self, message: str, task_id: Optional[str] = None, task_name: Optional[str] = None):
        super().__init__(
            message=message,
            status_code=500,
            error_code="TASK_ERROR",
            details={"task_id": task_id, "task_name": task_name}
        )


class ConfigurationError(TrustCardException):
    """Configuration or environment errors"""

    def __init__(self, message: str, config_key: Optional[str] = None):
        super().__init__(
            message=message,
            status_code=500,
            error_code="CONFIGURATION_ERROR",
            details={"config_key": config_key}
        )


class ExternalServiceError(TrustCardException):
    """External service (non-Instagram) errors"""

    def __init__(self, message: str, service_name: Optional[str] = None):
        super().__init__(
            message=message,
            status_code=502,  # Bad Gateway
            error_code="EXTERNAL_SERVICE_ERROR",
            details={"service": service_name}
        )
