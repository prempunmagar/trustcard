"""
Trust Score Scoring Configuration

Centralized configuration for trust score weights and thresholds.
All scoring parameters are defined here for easy tuning.
"""

from dataclasses import dataclass
from typing import Dict


@dataclass
class AIDetectionWeights:
    """Weights for AI-generated content detection"""
    max_penalty: float = 30.0  # Maximum penalty for AI detection
    confidence_multiplier: float = 1.0  # Scale penalty by confidence


@dataclass
class DeepfakeWeights:
    """Weights for deepfake/manipulation detection"""
    deepfake_penalty: float = 40.0  # Penalty for detected deepfakes


@dataclass
class FactCheckWeights:
    """Weights for fact-checking analysis"""
    # Credibility score thresholds
    high_credibility_threshold: float = 80.0  # Score >= 80 = high credibility
    questionable_threshold: float = 70.0      # Score >= 70 = questionable
    low_credibility_threshold: float = 50.0   # Score < 50 = low credibility

    # Penalties and bonuses
    low_credibility_multiplier: float = 0.8   # Up to -40 points
    questionable_multiplier: float = 0.5      # Up to -10 points
    high_credibility_multiplier: float = 0.2  # Up to +4 points

    # Red flag penalties
    medical_claims_penalty: float = 15.0
    conspiracy_language_penalty: float = 12.0
    urgent_language_penalty: float = 8.0
    absolutist_claims_penalty: float = 6.0
    unverified_sources_penalty: float = 10.0
    emotional_manipulation_penalty: float = 7.0
    sensationalism_penalty: float = 5.0


@dataclass
class SourceCredibilityWeights:
    """Weights for source credibility evaluation"""
    # Major source penalties
    conspiracy_sources_penalty: float = 25.0
    unreliable_sources_penalty: float = 20.0
    satire_penalty: float = 15.0

    # Reliability score adjustments
    low_reliability_threshold: float = 0.5   # Avg reliability < 0.5
    high_reliability_threshold: float = 0.7  # Avg reliability > 0.7
    low_reliability_multiplier: float = 20.0  # Up to -10 points
    high_reliability_multiplier: float = 10.0  # Up to +3 points


@dataclass
class GradeThresholds:
    """Grade conversion thresholds"""
    a_plus: float = 95.0   # A+ grade
    a: float = 90.0        # A grade
    a_minus: float = 85.0  # A- grade
    b_plus: float = 80.0   # B+ grade
    b: float = 75.0        # B grade
    b_minus: float = 70.0  # B- grade
    c_plus: float = 65.0   # C+ grade
    c: float = 60.0        # C grade
    c_minus: float = 55.0  # C- grade
    d_plus: float = 50.0   # D+ grade
    d: float = 45.0        # D grade
    d_minus: float = 40.0  # D- grade
    # Below 40.0 = F


@dataclass
class TrustScoreConfig:
    """Master configuration for trust score calculation"""
    base_score: float = 100.0  # Starting score

    # Component weights
    ai_detection: AIDetectionWeights = None
    deepfake: DeepfakeWeights = None
    fact_check: FactCheckWeights = None
    source_credibility: SourceCredibilityWeights = None
    grade_thresholds: GradeThresholds = None

    def __post_init__(self):
        """Initialize nested dataclasses"""
        if self.ai_detection is None:
            self.ai_detection = AIDetectionWeights()
        if self.deepfake is None:
            self.deepfake = DeepfakeWeights()
        if self.fact_check is None:
            self.fact_check = FactCheckWeights()
        if self.source_credibility is None:
            self.source_credibility = SourceCredibilityWeights()
        if self.grade_thresholds is None:
            self.grade_thresholds = GradeThresholds()


# Default configuration instance
DEFAULT_CONFIG = TrustScoreConfig()


def get_grade_from_score(score: float, config: TrustScoreConfig = None) -> str:
    """
    Convert numerical trust score to letter grade.

    Args:
        score: Trust score (0-100)
        config: Optional custom configuration

    Returns:
        str: Letter grade (A+ to F)
    """
    if config is None:
        config = DEFAULT_CONFIG

    thresholds = config.grade_thresholds

    if score >= thresholds.a_plus:
        return "A+"
    elif score >= thresholds.a:
        return "A"
    elif score >= thresholds.a_minus:
        return "A-"
    elif score >= thresholds.b_plus:
        return "B+"
    elif score >= thresholds.b:
        return "B"
    elif score >= thresholds.b_minus:
        return "B-"
    elif score >= thresholds.c_plus:
        return "C+"
    elif score >= thresholds.c:
        return "C"
    elif score >= thresholds.c_minus:
        return "C-"
    elif score >= thresholds.d_plus:
        return "D+"
    elif score >= thresholds.d:
        return "D"
    elif score >= thresholds.d_minus:
        return "D-"
    else:
        return "F"


def get_grade_description(grade: str) -> Dict[str, str]:
    """
    Get description and color for a grade.

    Args:
        grade: Letter grade

    Returns:
        dict: Description and color information
    """
    descriptions = {
        "A+": {
            "description": "Excellent - Highly trustworthy content",
            "color": "#059669",  # green-600
            "emoji": "✅"
        },
        "A": {
            "description": "Excellent - Very trustworthy",
            "color": "#10b981",  # green-500
            "emoji": "✅"
        },
        "A-": {
            "description": "Very Good - Trustworthy",
            "color": "#34d399",  # green-400
            "emoji": "✅"
        },
        "B+": {
            "description": "Good - Generally trustworthy",
            "color": "#22c55e",  # green-500
            "emoji": "👍"
        },
        "B": {
            "description": "Good - Mostly reliable",
            "color": "#84cc16",  # lime-500
            "emoji": "👍"
        },
        "B-": {
            "description": "Satisfactory - Some concerns",
            "color": "#a3e635",  # lime-400
            "emoji": "👍"
        },
        "C+": {
            "description": "Fair - Multiple concerns",
            "color": "#facc15",  # yellow-400
            "emoji": "⚠️"
        },
        "C": {
            "description": "Fair - Questionable reliability",
            "color": "#fbbf24",  # yellow-500
            "emoji": "⚠️"
        },
        "C-": {
            "description": "Poor - Significant concerns",
            "color": "#fb923c",  # orange-400
            "emoji": "⚠️"
        },
        "D+": {
            "description": "Poor - Low credibility",
            "color": "#f97316",  # orange-500
            "emoji": "❌"
        },
        "D": {
            "description": "Very Poor - Not trustworthy",
            "color": "#ef4444",  # red-500
            "emoji": "❌"
        },
        "D-": {
            "description": "Very Poor - Unreliable",
            "color": "#dc2626",  # red-600
            "emoji": "❌"
        },
        "F": {
            "description": "Failing - Highly unreliable",
            "color": "#991b1b",  # red-800
            "emoji": "❌"
        }
    }

    return descriptions.get(grade, {
        "description": "Unknown",
        "color": "#6b7280",
        "emoji": "❓"
    })
