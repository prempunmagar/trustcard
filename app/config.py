"""
Configuration management using Pydantic settings
"""
from pydantic_settings import BaseSettings
from typing import Optional, List

class Settings(BaseSettings):
    """Application settings"""

    # ============================================================================
    # APP SETTINGS
    # ============================================================================
    APP_NAME: str = "TrustCard"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"  # development, staging, production
    DEBUG: bool = True

    # ============================================================================
    # DATABASE
    # ============================================================================
    DATABASE_URL: str = "postgresql://trustcard:trustcard@db:5432/trustcard"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    # ============================================================================
    # REDIS & CELERY
    # ============================================================================
    REDIS_URL: str = "redis://redis:6379/0"
    CELERY_BROKER_URL: str = "redis://redis:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/1"

    # ============================================================================
    # INSTAGRAM
    # ============================================================================
    INSTAGRAM_USERNAME: Optional[str] = None
    INSTAGRAM_PASSWORD: Optional[str] = None

    # ============================================================================
    # API
    # ============================================================================
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    # ============================================================================
    # SECURITY
    # ============================================================================
    SECRET_KEY: str = "dev-secret-key-change-in-production"

    # ============================================================================
    # ANTHROPIC API
    # ============================================================================
    ANTHROPIC_API_KEY: Optional[str] = None

    # CORS
    CORS_ORIGINS: List[str] = ["*"]  # Set specific origins in production
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]

    # ============================================================================
    # RATE LIMITING
    # ============================================================================
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 10   # Requests per minute per IP
    RATE_LIMIT_PER_HOUR: int = 100    # Requests per hour per IP

    # ============================================================================
    # LOGGING
    # ============================================================================
    LOG_LEVEL: str = "INFO"           # DEBUG, INFO, WARNING, ERROR
    LOG_FILE: Optional[str] = None    # Path to log file (None = stdout only)
    LOG_JSON: bool = False            # True = JSON logs (production), False = colored (dev)

    # ============================================================================
    # MONITORING
    # ============================================================================
    ENABLE_METRICS: bool = True       # Prometheus metrics
    METRICS_PATH: str = "/metrics"    # Prometheus metrics endpoint

    # ============================================================================
    # VALIDATION
    # ============================================================================
    MAX_URL_LENGTH: int = 2000
    MAX_COMMENT_LENGTH: int = 1000

    class Config:
        env_file = ".env"
        case_sensitive = True

    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.ENVIRONMENT.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.ENVIRONMENT.lower() == "development"

settings = Settings()
