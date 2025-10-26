"""
Unit tests for trust score calculator.

Tests the core trust scoring algorithm and grade conversion.
"""
import pytest
from app.services.trust_score_calculator import calculate_trust_score


@pytest.mark.unit
class TestTrustScoreCalculator:
    """Test trust score calculation logic."""

    def test_perfect_score(self):
        """Perfect content should get high score."""
        results = {
            "ai_detection": {
                "overall_assessment": "real",
                "images": []
            },
            "deepfake": {
                "is_manipulated": False
            },
            "fact_checking": {
                "overall_verdict": "LIKELY_TRUE"
            },
            "source_credibility": {
                "overall_credibility": "highly_reliable"
            }
        }

        score_result = calculate_trust_score(results)

        assert score_result.final_score >= 90
        assert score_result.grade in ["A+", "A", "A-"]

    def test_ai_generated_penalty(self):
        """AI-generated content should reduce score."""
        results = {
            "ai_detection": {
                "overall_assessment": "ai_generated",
                "images": []
            },
            "deepfake": {"is_manipulated": False},
            "fact_checking": {"overall_verdict": "INCONCLUSIVE"},
            "source_credibility": {"overall_credibility": "unknown"}
        }

        score_result = calculate_trust_score(results)

        assert score_result.final_score < 90
        # Check that AI penalty is in adjustments
        ai_penalties = [adj for adj in score_result.adjustments if "AI" in adj.reason]
        assert len(ai_penalties) > 0

    def test_deepfake_severe_penalty(self):
        """Deepfake content should severely reduce score."""
        results = {
            "ai_detection": {"overall_assessment": "real", "images": []},
            "deepfake": {
                "is_manipulated": True,
                "confidence": 0.95
            },
            "fact_checking": {"overall_verdict": "INCONCLUSIVE"},
            "source_credibility": {"overall_credibility": "unknown"}
        }

        score_result = calculate_trust_score(results)

        assert score_result.final_score < 60
        assert score_result.grade in ["D", "F"]

    def test_misinformation_severe_penalty(self):
        """False claims should severely reduce score."""
        results = {
            "ai_detection": {"overall_assessment": "real", "images": []},
            "deepfake": {"is_manipulated": False},
            "fact_checking": {
                "overall_verdict": "LIKELY_FALSE",
                "claims": [{"verdict": "LIKELY_FALSE"}]
            },
            "source_credibility": {"overall_credibility": "unknown"}
        }

        score_result = calculate_trust_score(results)

        assert score_result.final_score < 50
        assert score_result.grade == "F"

    def test_score_bounds(self):
        """Score should always be between 0 and 100."""
        # Test extreme negative case
        bad_results = {
            "ai_detection": {"overall_assessment": "ai_generated", "images": []},
            "deepfake": {"is_manipulated": True},
            "fact_checking": {"overall_verdict": "LIKELY_FALSE"},
            "source_credibility": {"overall_credibility": "very_unreliable"}
        }

        score_result = calculate_trust_score(bad_results)

        assert 0 <= score_result.final_score <= 100
