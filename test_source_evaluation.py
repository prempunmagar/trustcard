"""
Test Source Evaluation Service

This script tests the source credibility evaluation service.
"""

import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.source_evaluation_service import source_evaluation_service


def test_source_evaluation():
    """Test source credibility evaluation."""

    print("=" * 70)
    print("📰 SOURCE EVALUATION TEST")
    print("=" * 70)
    print()

    # Test URLs
    test_urls = {
        "High Reliability - Center": "https://www.reuters.com/article/xyz",
        "High Reliability - Left": "https://www.nytimes.com/article/xyz",
        "High Reliability - Right": "https://www.wsj.com/article/xyz",
        "Mixed Reliability - Right": "https://www.foxnews.com/article/xyz",
        "Mixed Reliability - Left": "https://www.huffpost.com/article/xyz",
        "Low Reliability": "https://www.infowars.com/article/xyz",
        "Satire": "https://www.theonion.com/article/xyz",
        "Fact-Checking": "https://www.snopes.com/fact-check/xyz",
        "Government": "https://www.cdc.gov/article",
        "Academic": "https://www.nature.com/articles/xyz",
        "Unknown Source": "https://www.randomwebsite123.com/article"
    }

    print("=" * 70)
    print("TESTING INDIVIDUAL SOURCES")
    print("=" * 70)
    print()

    for label, url in test_urls.items():
        print(f"📝 {label}")
        print(f"   URL: {url}")

        result = source_evaluation_service.get_source_credibility(url)

        print(f"\n   Domain: {result['domain']}")
        print(f"   Bias: {result['bias_rating']}")
        print(f"   Reliability: {result['reliability_rating']}")
        print(f"   Reliability Score: {result['reliability_score']}")
        print(f"   In Database: {result['in_database']}")
        print(f"\n   Assessment:")
        print(f"   {result['assessment']}")
        print()

    # Test Instagram user evaluation
    print("=" * 70)
    print("TESTING INSTAGRAM USER EVALUATION")
    print("=" * 70)
    print()

    test_users = [
        {"username": "verified_celebrity", "is_verified": True, "follower_count": 10000000},
        {"username": "regular_user", "is_verified": False, "follower_count": 500},
        {"username": "small_account", "is_verified": False, "follower_count": 50}
    ]

    for user in test_users:
        print(f"📱 @{user['username']}")
        result = source_evaluation_service.evaluate_instagram_user(user)

        print(f"   Verified: {result['is_verified']}")
        print(f"   Followers: {result['follower_count']:,}")
        print(f"   Reliability Score: {result['reliability_score']}")
        print(f"   Note: {result['note']}")
        print()

    # Test overall assessment
    print("=" * 70)
    print("TESTING OVERALL ASSESSMENT")
    print("=" * 70)
    print()

    test_cases = [
        {
            "name": "High Quality Sources",
            "urls": [
                "https://www.reuters.com/article/xyz",
                "https://www.nytimes.com/article/abc",
                "https://www.bbc.com/news/xyz"
            ],
            "user": {"username": "journalist", "is_verified": True, "follower_count": 50000}
        },
        {
            "name": "Mixed Quality Sources",
            "urls": [
                "https://www.reuters.com/article/xyz",
                "https://www.foxnews.com/article/abc"
            ],
            "user": {"username": "news_sharer", "is_verified": False, "follower_count": 1000}
        },
        {
            "name": "Unreliable Sources",
            "urls": [
                "https://www.infowars.com/article/xyz",
                "https://www.naturalnews.com/article/abc"
            ],
            "user": {"username": "conspiracy_poster", "is_verified": False, "follower_count": 5000}
        },
        {
            "name": "Satire Source",
            "urls": [
                "https://www.theonion.com/article/xyz"
            ],
            "user": {"username": "funny_account", "is_verified": False, "follower_count": 10000}
        },
        {
            "name": "No External Sources",
            "urls": [],
            "user": {"username": "regular_poster", "is_verified": False, "follower_count": 300}
        }
    ]

    for test_case in test_cases:
        print(f"📊 Test: {test_case['name']}")
        print(f"   External URLs: {len(test_case['urls'])}")

        overall = source_evaluation_service.get_overall_source_assessment(
            test_case['urls'],
            test_case['user']
        )

        print(f"\n   Instagram User: @{overall['instagram_user']['username']}")
        print(f"   Verified: {overall['instagram_user']['is_verified']}")

        if overall['external_source_count'] > 0:
            print(f"\n   External Sources Analyzed: {overall['external_source_count']}")
            print(f"   Average Reliability: {overall['avg_reliability_score']}")
            print(f"   Lowest Reliability: {overall['lowest_reliability_score']}")
            print(f"   Has Unreliable: {overall['has_unreliable_sources']}")
            print(f"   Has Satire: {overall['has_satire']}")
            print(f"   Has Conspiracy: {overall['has_conspiracy']}")

            print(f"\n   Individual Sources:")
            for idx, source in enumerate(overall['external_sources'], 1):
                print(f"      {idx}. {source['domain']} - {source['reliability_rating']}")

        print(f"\n   Overall Assessment:")
        print(f"   {overall['overall_assessment']}")

        print(f"\n   Recommendation:")
        print(f"   {overall['recommendation']}")
        print()

    print("=" * 70)
    print("✅ SOURCE EVALUATION TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    test_source_evaluation()
