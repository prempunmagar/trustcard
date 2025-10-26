"""
Test Trust Score Calculator

Tests the trust score calculator with various mock scenarios.
"""

import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.trust_score_calculator import calculate_trust_score
from app.config.scoring_config import DEFAULT_CONFIG


def print_score_result(scenario: str, result):
    """Pretty print a trust score result"""
    print()
    print("=" * 70)
    print(f"SCENARIO: {scenario}")
    print("=" * 70)
    print()
    print(f"Final Score: {result.final_score}/100")
    print(f"Grade: {result.grade} - {result.grade_info['description']}")
    print(f"Emoji: {result.grade_info['emoji']}")
    print()
    print(f"Total Penalties: {result.total_penalties}")
    print(f"Total Bonuses: {result.total_bonuses}")
    print()

    if result.adjustments:
        print("Score Adjustments:")
        for adj in result.adjustments:
            sign = "+" if adj.impact >= 0 else ""
            print(f"  [{adj.component}] {adj.category}: {sign}{adj.impact:.1f}")
            print(f"    → {adj.reason}")
        print()

    if result.flags:
        print("⚠️  Flags:")
        for flag in result.flags:
            print(f"  • {flag}")
        print()

    if result.requires_review:
        print("🔴 REQUIRES MANUAL REVIEW")
        print()

    print("Component Scores:")
    for component, score in result.component_scores.items():
        sign = "+" if score >= 0 else ""
        print(f"  {component}: {sign}{score:.1f}")
    print()


def test_perfect_post():
    """Test scenario: Perfect, trustworthy post"""
    results = {
        "ai_detection": {
            "status": "completed",
            "overall": {
                "overall_ai_detected": False,
                "confidence": 0.0
            }
        },
        "ocr": {
            "status": "completed",
            "summary": {"has_text": True, "total_words_extracted": 50}
        },
        "deepfake": {
            "status": "completed",
            "is_deepfake": False
        },
        "fact_check": {
            "status": "completed",
            "credibility_analysis": {
                "score": 85.0
            },
            "flags": [],
            "requires_manual_review": False
        },
        "source_credibility": {
            "status": "completed",
            "assessment": {
                "has_conspiracy": False,
                "has_unreliable_sources": False,
                "has_satire": False,
                "avg_reliability_score": 0.8
            }
        }
    }

    result = calculate_trust_score(results)
    print_score_result("Perfect Trustworthy Post", result)


def test_ai_generated():
    """Test scenario: AI-generated content detected"""
    results = {
        "ai_detection": {
            "status": "completed",
            "overall": {
                "overall_ai_detected": True,
                "confidence": 0.85,
                "ai_images": 3,
                "total_images": 3
            }
        },
        "ocr": {"status": "completed"},
        "deepfake": {"status": "completed", "is_deepfake": False},
        "fact_check": {
            "status": "completed",
            "credibility_analysis": {"score": 70.0},
            "flags": [],
            "requires_manual_review": False
        },
        "source_credibility": {
            "status": "completed",
            "assessment": {
                "has_conspiracy": False,
                "has_unreliable_sources": False,
                "has_satire": False,
                "avg_reliability_score": 0.5
            }
        }
    }

    result = calculate_trust_score(results)
    print_score_result("AI-Generated Content", result)


def test_conspiracy_content():
    """Test scenario: Conspiracy theory content"""
    results = {
        "ai_detection": {
            "status": "completed",
            "overall": {"overall_ai_detected": False}
        },
        "ocr": {"status": "completed"},
        "deepfake": {"status": "completed", "is_deepfake": False},
        "fact_check": {
            "status": "completed",
            "credibility_analysis": {"score": 35.0},
            "flags": ["CONSPIRACY_LANGUAGE", "MEDICAL_CLAIMS", "UNVERIFIED_SOURCES"],
            "requires_manual_review": True
        },
        "source_credibility": {
            "status": "completed",
            "assessment": {
                "has_conspiracy": True,
                "has_unreliable_sources": False,
                "has_satire": False,
                "avg_reliability_score": 0.2
            }
        }
    }

    result = calculate_trust_score(results)
    print_score_result("Conspiracy Theory Content", result)


def test_deepfake():
    """Test scenario: Deepfake detected"""
    results = {
        "ai_detection": {
            "status": "completed",
            "overall": {"overall_ai_detected": False}
        },
        "ocr": {"status": "completed"},
        "deepfake": {
            "status": "completed",
            "is_deepfake": True,
            "analysis": {"manipulation_detected": True}
        },
        "fact_check": {
            "status": "completed",
            "credibility_analysis": {"score": 60.0},
            "flags": [],
            "requires_manual_review": False
        },
        "source_credibility": {
            "status": "completed",
            "assessment": {
                "has_conspiracy": False,
                "has_unreliable_sources": False,
                "has_satire": False,
                "avg_reliability_score": 0.5
            }
        }
    }

    result = calculate_trust_score(results)
    print_score_result("Deepfake Detected", result)


def test_unreliable_sources():
    """Test scenario: Unreliable news sources"""
    results = {
        "ai_detection": {
            "status": "completed",
            "overall": {"overall_ai_detected": False}
        },
        "ocr": {"status": "completed"},
        "deepfake": {"status": "completed", "is_deepfake": False},
        "fact_check": {
            "status": "completed",
            "credibility_analysis": {"score": 65.0},
            "flags": ["SENSATIONALISM"],
            "requires_manual_review": False
        },
        "source_credibility": {
            "status": "completed",
            "assessment": {
                "has_conspiracy": False,
                "has_unreliable_sources": True,
                "has_satire": False,
                "avg_reliability_score": 0.3
            }
        }
    }

    result = calculate_trust_score(results)
    print_score_result("Unreliable News Sources", result)


def test_satire():
    """Test scenario: Satire content"""
    results = {
        "ai_detection": {
            "status": "completed",
            "overall": {"overall_ai_detected": False}
        },
        "ocr": {"status": "completed"},
        "deepfake": {"status": "completed", "is_deepfake": False},
        "fact_check": {
            "status": "completed",
            "credibility_analysis": {"score": 70.0},
            "flags": [],
            "requires_manual_review": False
        },
        "source_credibility": {
            "status": "completed",
            "assessment": {
                "has_conspiracy": False,
                "has_unreliable_sources": False,
                "has_satire": True,
                "avg_reliability_score": 0.5
            }
        }
    }

    result = calculate_trust_score(results)
    print_score_result("Satire Content", result)


def test_mixed_issues():
    """Test scenario: Multiple issues combined"""
    results = {
        "ai_detection": {
            "status": "completed",
            "overall": {
                "overall_ai_detected": True,
                "confidence": 0.6,
                "ai_images": 2,
                "total_images": 4
            }
        },
        "ocr": {"status": "completed"},
        "deepfake": {"status": "completed", "is_deepfake": False},
        "fact_check": {
            "status": "completed",
            "credibility_analysis": {"score": 55.0},
            "flags": ["URGENT_LANGUAGE", "EMOTIONAL_MANIPULATION"],
            "requires_manual_review": False
        },
        "source_credibility": {
            "status": "completed",
            "assessment": {
                "has_conspiracy": False,
                "has_unreliable_sources": False,
                "has_satire": False,
                "avg_reliability_score": 0.4
            }
        }
    }

    result = calculate_trust_score(results)
    print_score_result("Multiple Issues", result)


def test_high_credibility_bonus():
    """Test scenario: High credibility content with bonus"""
    results = {
        "ai_detection": {
            "status": "completed",
            "overall": {"overall_ai_detected": False}
        },
        "ocr": {"status": "completed"},
        "deepfake": {"status": "completed", "is_deepfake": False},
        "fact_check": {
            "status": "completed",
            "credibility_analysis": {"score": 95.0},
            "flags": [],
            "requires_manual_review": False
        },
        "source_credibility": {
            "status": "completed",
            "assessment": {
                "has_conspiracy": False,
                "has_unreliable_sources": False,
                "has_satire": False,
                "avg_reliability_score": 0.9
            }
        }
    }

    result = calculate_trust_score(results)
    print_score_result("High Credibility with Bonus", result)


def main():
    """Run all test scenarios"""
    print()
    print("=" * 70)
    print("TRUST SCORE CALCULATOR TEST SUITE")
    print("=" * 70)
    print()
    print("Testing various scenarios with the trust score calculator...")
    print()

    # Run all tests
    test_perfect_post()
    test_ai_generated()
    test_conspiracy_content()
    test_deepfake()
    test_unreliable_sources()
    test_satire()
    test_mixed_issues()
    test_high_credibility_bonus()

    # Summary
    print()
    print("=" * 70)
    print("TEST SUITE COMPLETE")
    print("=" * 70)
    print()
    print("✅ All scenarios tested successfully!")
    print()
    print("Configuration used:")
    print(f"  Base Score: {DEFAULT_CONFIG.base_score}")
    print(f"  AI Detection Max Penalty: {DEFAULT_CONFIG.ai_detection.max_penalty}")
    print(f"  Deepfake Penalty: {DEFAULT_CONFIG.deepfake.deepfake_penalty}")
    print(f"  Conspiracy Sources Penalty: {DEFAULT_CONFIG.source_credibility.conspiracy_sources_penalty}")
    print()


if __name__ == "__main__":
    main()
