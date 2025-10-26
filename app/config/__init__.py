"""
Configuration package for TrustCard
"""

from app.config.scoring_config import (
    TrustScoreConfig,
    DEFAULT_CONFIG,
    get_grade_from_score,
    get_grade_description
)

__all__ = [
    "TrustScoreConfig",
    "DEFAULT_CONFIG",
    "get_grade_from_score",
    "get_grade_description"
]
