"""
Test TrustCard API with Fact-Checking

This script tests the full API including fact-checking by analyzing
Instagram posts with various types of content.
"""

import requests
import time
import json


BASE_URL = "http://localhost:8000"


def analyze_post(instagram_url: str, description: str) -> dict:
    """Submit post for analysis and wait for results."""
    print(f"\n{'='*80}")
    print(f"TEST: {description}")
    print(f"{'='*80}")
    print(f"Instagram URL: {instagram_url}")

    # Submit analysis request
    print("\n1. Submitting analysis request...")
    response = requests.post(
        f"{BASE_URL}/api/v1/analysis",
        json={"instagram_url": instagram_url}
    )

    if response.status_code != 202:
        print(f"❌ Failed to submit request: {response.status_code}")
        print(response.text)
        return None

    data = response.json()
    analysis_id = data["analysis_id"]
    print(f"✅ Analysis submitted: {analysis_id}")

    # Poll for results
    print("\n2. Polling for results...")
    max_attempts = 60  # 60 seconds max
    for attempt in range(max_attempts):
        time.sleep(1)

        status_response = requests.get(f"{BASE_URL}/api/v1/analysis/{analysis_id}")

        if status_response.status_code != 200:
            print(f"❌ Failed to get status: {status_response.status_code}")
            return None

        status_data = status_response.json()
        status = status_data.get("status")

        if status == "completed":
            print(f"✅ Analysis complete (took {attempt+1}s)")
            return status_data
        elif status == "failed":
            print(f"❌ Analysis failed: {status_data.get('error_message')}")
            return status_data
        else:
            print(f"   [{attempt+1}s] Status: {status}...")

    print("❌ Timeout waiting for results")
    return None


def display_results(results: dict):
    """Display analysis results with focus on fact-checking."""
    if not results:
        return

    print(f"\n{'='*80}")
    print("ANALYSIS RESULTS")
    print(f"{'='*80}")

    # Basic info
    print(f"\nAnalysis ID: {results.get('id')}")
    print(f"Status: {results.get('status')}")
    print(f"Trust Score: {results.get('trust_score')}/100")
    print(f"Post Type: {results.get('results', {}).get('instagram_extraction', {}).get('post_type')}")

    # Instagram content
    content = results.get("content", {})
    caption = content.get("caption", "")
    print(f"\nCaption: {caption[:200]}{'...' if len(caption) > 200 else ''}")

    # AI Detection
    ai_detection = results.get("results", {}).get("ai_detection", {})
    if ai_detection.get("status") == "completed":
        overall = ai_detection.get("overall", {})
        print(f"\n🤖 AI Detection:")
        print(f"   Status: {overall.get('assessment')}")
        print(f"   Confidence: {overall.get('confidence', 0)*100:.1f}%")
        if overall.get("overall_ai_detected"):
            print(f"   ⚠️ AI-generated content detected")

    # OCR
    ocr = results.get("results", {}).get("ocr", {})
    if ocr.get("status") == "completed":
        summary = ocr.get("summary", {})
        print(f"\n📝 OCR Text Extraction:")
        print(f"   Images with text: {summary.get('images_with_text')}/{summary.get('total_images')}")
        print(f"   Words extracted: {summary.get('total_words_extracted')}")
        print(f"   Avg confidence: {summary.get('avg_confidence', 0):.1f}%")

        # Show extracted text
        combined = ocr.get("combined", {})
        ocr_text = combined.get("ocr_text", "")
        if ocr_text:
            print(f"   Extracted text: {ocr_text[:150]}{'...' if len(ocr_text) > 150 else ''}")

    # Fact-Checking (main focus)
    fact_check = results.get("results", {}).get("fact_check", {})
    if fact_check.get("status") == "completed":
        print(f"\n🔍 FACT-CHECKING ANALYSIS:")

        # Claim extraction
        claim_extraction = fact_check.get("claim_extraction", {})
        print(f"\n   Claims Extracted:")
        print(f"   - Total claims: {claim_extraction.get('total_claims')}")
        print(f"   - Claim types: {claim_extraction.get('claim_types')}")
        print(f"   - Sentiment: polarity={claim_extraction.get('sentiment', {}).get('polarity', 0):.2f}, "
              f"subjectivity={claim_extraction.get('sentiment', {}).get('subjectivity', 0):.2f}")

        # Credibility analysis
        credibility = fact_check.get("credibility_analysis", {})
        print(f"\n   Credibility Analysis:")
        print(f"   - Score: {credibility.get('score')}/100")
        print(f"   - Interpretation: {credibility.get('interpretation')}")

        penalties = credibility.get("penalties", [])
        if penalties:
            print(f"\n   Penalties:")
            for penalty in penalties:
                print(f"   - {penalty['reason']}: -{penalty['penalty']} points")

        bonuses = credibility.get("bonuses", [])
        if bonuses:
            print(f"\n   Bonuses:")
            for bonus in bonuses:
                print(f"   + {bonus['reason']}: +{bonus['bonus']} points")

        # Flags and warnings
        flags = fact_check.get("flags", [])
        if flags:
            print(f"\n   ⚠️ Flags: {', '.join(flags)}")

        print(f"\n   Risk Level: {fact_check.get('risk_level')}")
        print(f"   Requires Manual Review: {fact_check.get('requires_manual_review')}")

        # Summary
        print(f"\n   Summary: {fact_check.get('summary')}")

        # Individual claims
        analyzed_claims = fact_check.get("analyzed_claims", [])
        if analyzed_claims:
            print(f"\n   Analyzed Claims ({len(analyzed_claims)}):")
            for i, claim in enumerate(analyzed_claims[:5], 1):  # Show first 5
                print(f"\n   {i}. {claim['text'][:100]}{'...' if len(claim['text']) > 100 else ''}")
                print(f"      Type: {claim['type']}")
                print(f"      Credibility: {claim['claim_credibility']:.2f}")
                if claim.get('red_flags'):
                    print(f"      Red Flags: {list(claim['red_flags'].keys())}")
                if claim.get('warnings'):
                    print(f"      Warnings: {', '.join(claim['warnings'][:2])}")

            if len(analyzed_claims) > 5:
                print(f"\n   ... and {len(analyzed_claims) - 5} more claims")

    elif fact_check.get("status") == "skipped":
        print(f"\n🔍 Fact-Checking: Skipped ({fact_check.get('reason')})")
    elif fact_check.get("status") == "failed":
        print(f"\n🔍 Fact-Checking: Failed ({fact_check.get('error')})")

    # Final score breakdown
    print(f"\n{'='*80}")
    print(f"FINAL TRUST SCORE: {results.get('trust_score')}/100")
    print(f"{'='*80}")


def main():
    """Run API tests."""
    print("="*80)
    print("TRUSTCARD API TEST - WITH FACT-CHECKING")
    print("="*80)
    print("\nMake sure the API is running: docker-compose up")
    print("Testing with various Instagram posts...")

    # Test with different types of posts
    # You should replace these URLs with real Instagram posts for testing

    test_cases = [
        {
            "url": "https://www.instagram.com/p/EXAMPLE1/",
            "description": "Test Post 1 - News/Informational Content"
        },
        {
            "url": "https://www.instagram.com/p/EXAMPLE2/",
            "description": "Test Post 2 - Meme with Text"
        },
        {
            "url": "https://www.instagram.com/p/EXAMPLE3/",
            "description": "Test Post 3 - Health/Medical Claim"
        }
    ]

    print("\n⚠️ NOTE: Replace EXAMPLE URLs in test_with_fact_checking.py with real Instagram post URLs")
    print("For now, testing with example URLs (will likely fail at Instagram extraction)")

    for test_case in test_cases:
        try:
            results = analyze_post(test_case["url"], test_case["description"])
            if results:
                display_results(results)

            print("\n" + "-"*80)
            input("Press Enter to continue to next test...")

        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "="*80)
    print("TESTING COMPLETE")
    print("="*80)
    print("\nTo test properly:")
    print("1. Replace EXAMPLE URLs with real Instagram post URLs")
    print("2. Ensure Instagram credentials are configured")
    print("3. Run: python test_with_fact_checking.py")


if __name__ == "__main__":
    main()
