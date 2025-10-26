"""
Configuration management using Pydantic settings
"""
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Application settings"""

    # App
    APP_NAME: str = "TrustCard"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "postgresql://trustcard:trustcard@db:5432/trustcard"

    # Redis (will configure in Step 3)
    REDIS_URL: str = "redis://redis:6379/0"

    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
