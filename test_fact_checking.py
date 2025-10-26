"""
Test Fact-Checking Services Directly

This script tests the claim extraction and fact-checking services
without requiring the full API or database setup.
"""

import sys
import json
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.claim_extractor import claim_extractor
from app.services.fact_checking_service import fact_checking_service


def test_text(text: str, description: str):
    """Test fact-checking on a given text."""
    print(f"\n{'='*80}")
    print(f"TEST: {description}")
    print(f"{'='*80}")
    print(f"\nOriginal Text:\n{text}\n")

    # Extract claims
    print("📝 Extracting claims...")
    claim_extractor.initialize()
    claim_data = claim_extractor.extract_claims(text)

    print(f"\n✅ Found {claim_data['total_claims']} claim(s)")
    print(f"   Claim types: {claim_data['claim_types']}")
    print(f"   Sentiment: polarity={claim_data['sentiment']['polarity']:.2f}, "
          f"subjectivity={claim_data['sentiment']['subjectivity']:.2f}")

    if claim_data['claims']:
        print(f"\n   Claims extracted:")
        for i, claim in enumerate(claim_data['claims'], 1):
            print(f"   {i}. [{claim['type']}] {claim['text'][:80]}...")

    # Analyze claims for credibility
    print(f"\n🔍 Analyzing credibility...")
    fact_check_analysis = fact_checking_service.analyze_claims(claim_data, text)

    print(f"\n✅ Credibility Analysis Complete")
    print(f"   Score: {fact_check_analysis['credibility_score']['score']}/100")
    print(f"   Interpretation: {fact_check_analysis['credibility_score']['interpretation']}")
    print(f"   Risk Level: {fact_check_analysis['risk_level']}")
    print(f"   Requires Manual Review: {fact_check_analysis['requires_manual_review']}")

    if fact_check_analysis['flags']:
        print(f"\n   ⚠️ Flags: {', '.join(fact_check_analysis['flags'])}")

    penalties = fact_check_analysis['credibility_score'].get('penalties', [])
    if penalties:
        print(f"\n   Penalties:")
        for penalty in penalties:
            print(f"   - {penalty['reason']}: -{penalty['penalty']} points")

    bonuses = fact_check_analysis['credibility_score'].get('bonuses', [])
    if bonuses:
        print(f"\n   Bonuses:")
        for bonus in bonuses:
            print(f"   + {bonus['reason']}: +{bonus['bonus']} points")

    print(f"\n   Summary: {fact_check_analysis['summary']}")

    # Show analyzed claims with red flags
    if fact_check_analysis['analyzed_claims']:
        print(f"\n   Analyzed Claims:")
        for i, claim in enumerate(fact_check_analysis['analyzed_claims'], 1):
            print(f"\n   {i}. {claim['text'][:80]}...")
            print(f"      Type: {claim['type']}")
            print(f"      Credibility: {claim['claim_credibility']:.2f}")
            if claim['red_flags']:
                print(f"      Red Flags: {list(claim['red_flags'].keys())}")
            if claim['warnings']:
                print(f"      Warnings: {', '.join(claim['warnings'])}")


def main():
    """Run test cases."""
    print("="*80)
    print("FACT-CHECKING SERVICE TEST")
    print("="*80)
    print("\nTesting claim extraction and credibility analysis...")

    # Test Case 1: High credibility text
    test_text(
        "A new study published in the Journal of Medicine found that regular exercise "
        "reduces the risk of heart disease. The research was conducted by Stanford University "
        "over 10 years with 5,000 participants. https://stanford.edu/study",
        "High Credibility - Proper source citation"
    )

    # Test Case 2: Low credibility - conspiracy language
    test_text(
        "URGENT!!! Big Pharma doesn't want you to know this SHOCKING truth!!! "
        "Doctors say this natural cure COMPLETELY eliminates cancer 100%! "
        "They're trying to cover it up!!! SHARE NOW before it's deleted!!!",
        "Low Credibility - Conspiracy + medical misinformation"
    )

    # Test Case 3: Medium credibility - vague sources
    test_text(
        "Studies show that 90% of people prefer this product. "
        "A doctor told me it's the best treatment available. "
        "Research proves this method works every time.",
        "Medium Credibility - Vague sources + absolutist language"
    )

    # Test Case 4: Statistical claims
    test_text(
        "Sales increased by 150% in Q4 2024. The company now has 5 million users. "
        "Customer satisfaction improved from 75% to 92%. "
        "Revenue reached $100 million this year.",
        "Statistical Claims - Verifiable numbers"
    )

    # Test Case 5: Clickbait + emotional manipulation
    test_text(
        "You won't believe what happens next! This ONE TRICK will SHOCK you! "
        "Number 5 will blow your mind!!! Doctors hate this simple method!!! "
        "EVERYONE is talking about it!!!",
        "Low Credibility - Clickbait + sensationalism"
    )

    # Test Case 6: Neutral informational text
    test_text(
        "The weather today is sunny with a high of 75 degrees. "
        "The local park will be open from 9am to 5pm. "
        "Parking is available on Main Street.",
        "Neutral - Informational, no claims"
    )

    # Test Case 7: Health claims without sources
    test_text(
        "This natural detox cleanse removes toxins from your body. "
        "It boosts your immune system and prevents diseases. "
        "Drink this every morning to stay healthy. "
        "Big pharma is hiding this secret remedy.",
        "Low Credibility - Health claims + conspiracy"
    )

    # Test Case 8: Political claims with sources
    test_text(
        "According to the Congressional Budget Office report published yesterday, "
        "the unemployment rate has decreased to 3.5%. The Federal Reserve confirmed "
        "these findings in their quarterly statement. "
        "https://cbo.gov/report https://federalreserve.gov",
        "High Credibility - Official sources cited"
    )

    print("\n" + "="*80)
    print("TESTING COMPLETE")
    print("="*80)


if __name__ == "__main__":
    main()
