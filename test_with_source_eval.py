"""
Test TrustCard API with Source Evaluation

This script tests the full API including source credibility evaluation.
"""

import requests
import time
import json


BASE_URL = "http://localhost:8000"


def test_analysis_with_source_eval(instagram_url: str):
    """Test complete analysis including source evaluation."""

    print("=" * 70)
    print("🧪 TRUSTCARD ANALYSIS TEST - WITH SOURCE EVALUATION")
    print("=" * 70)
    print()
    print(f"Instagram URL: {instagram_url}")
    print()

    # Submit analysis
    print("📤 Submitting analysis...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/analysis",
            json={"instagram_url": instagram_url}
        )

        if response.status_code != 202:
            print(f"❌ Failed: {response.status_code}")
            print(response.text)
            return

        data = response.json()
        analysis_id = data["analysis_id"]

        print(f"✅ Analysis submitted: {analysis_id}")
        print()

    except Exception as e:
        print(f"❌ Error: {e}")
        return

    # Poll for results
    print("⏳ Waiting for analysis to complete...")
    print()

    for i in range(60):
        time.sleep(2)

        try:
            response = requests.get(f"{BASE_URL}/api/v1/analysis/{analysis_id}")
            data = response.json()

            status = data.get("status")

            if status == "completed":
                print(f"✅ Analysis complete!")
                print()
                break
            elif status == "failed":
                print(f"❌ Analysis failed: {data.get('error_message')}")
                return
            else:
                print(f"   [{i*2}s] Status: {status}...")

        except Exception as e:
            print(f"   Error checking status: {e}")

    if status != "completed":
        print("❌ Timeout waiting for results")
        return

    # Display results
    print("=" * 70)
    print("📊 TRUSTCARD ANALYSIS RESULTS")
    print("=" * 70)
    print()

    print(f"🎯 TRUST SCORE: {data.get('trust_score')}/100")
    print()

    # Instagram content
    content = data.get("content", {})
    user = content.get("user", {})
    caption = content.get("caption", "")

    print(f"📱 Instagram Post:")
    print(f"   User: @{user.get('username')}")
    print(f"   Verified: {user.get('is_verified')}")
    print(f"   Post Type: {content.get('type')}")
    if caption:
        print(f"   Caption: {caption[:150]}{'...' if len(caption) > 150 else ''}")
    print()

    # Analysis results
    results = data.get("results", {})

    # AI Detection
    ai_detection = results.get("ai_detection", {})
    if ai_detection.get("status") == "completed":
        overall = ai_detection.get("overall", {})
        print(f"🤖 AI Detection:")
        print(f"   Status: {overall.get('assessment')}")
        print(f"   Confidence: {overall.get('confidence', 0)*100:.1f}%")
        print()

    # OCR
    ocr = results.get("ocr", {})
    if ocr.get("status") == "completed":
        summary = ocr.get("summary", {})
        print(f"📝 OCR Text Extraction:")
        print(f"   Words extracted: {summary.get('total_words_extracted')}")
        print(f"   Images with text: {summary.get('images_with_text')}/{summary.get('total_images')}")
        print()

    # Fact-Checking
    fact_check = results.get("fact_check", {})
    if fact_check.get("status") == "completed":
        credibility = fact_check.get("credibility_analysis", {})
        print(f"🔍 Fact-Checking:")
        print(f"   Claims analyzed: {fact_check.get('claim_extraction', {}).get('total_claims')}")
        print(f"   Credibility score: {credibility.get('score')}/100")
        print(f"   Risk level: {fact_check.get('risk_level')}")
        print()

    # Source Credibility (main focus)
    source_cred = results.get("source_credibility", {})
    if source_cred.get("status") == "completed":
        print("=" * 70)
        print("📰 SOURCE CREDIBILITY ANALYSIS")
        print("=" * 70)
        print()

        assessment = source_cred.get("assessment", {})

        # Instagram user
        ig_user = assessment.get("instagram_user", {})
        print(f"📱 Instagram Account:")
        print(f"   Username: @{ig_user.get('username')}")
        print(f"   Verified: {'✓' if ig_user.get('is_verified') else '✗'}")
        print(f"   Reliability Score: {ig_user.get('reliability_score')}")
        print(f"   {ig_user.get('note')}")
        print()

        # External sources
        external = assessment.get("external_sources", [])
        if external:
            print(f"🔗 External Sources Linked: {len(external)}")
            print()

            for idx, source in enumerate(external, 1):
                print(f"   {idx}. {source['domain']}")
                print(f"      Reliability: {source['reliability_rating']}")
                print(f"      Bias: {source['bias_rating']}")
                print(f"      Score: {source['reliability_score']}")
                print(f"      {source['assessment']}")
                print()

            # Overall scores
            print(f"   📊 Overall Statistics:")
            print(f"      Average Reliability: {assessment.get('avg_reliability_score')}")
            print(f"      Lowest Reliability: {assessment.get('lowest_reliability_score')}")
            print(f"      Has Unreliable Sources: {assessment.get('has_unreliable_sources')}")
            print(f"      Has Satire: {assessment.get('has_satire')}")
            print(f"      Has Conspiracy Sources: {assessment.get('has_conspiracy')}")
            print()

        else:
            print(f"🔗 No external sources found in post")
            print()

        # Overall assessment
        print(f"   ✅ Overall Assessment:")
        print(f"   {assessment.get('overall_assessment')}")
        print()

        print(f"   💡 Recommendation:")
        print(f"   {assessment.get('recommendation')}")
        print()

    elif source_cred.get("status") == "failed":
        print(f"📰 Source Credibility: ❌ Failed ({source_cred.get('error')})")
        print()

    # Summary
    print("=" * 70)
    print("📋 ANALYSIS SUMMARY")
    print("=" * 70)
    print()

    components = [
        ("🤖 AI Detection", "ai_detection"),
        ("📝 OCR", "ocr"),
        ("🔍 Fact-Check", "fact_check"),
        ("📰 Source Credibility", "source_credibility"),
        ("🎭 Deepfake", "deepfake")
    ]

    for label, key in components:
        component = results.get(key, {})
        status = component.get("status", "unknown")
        print(f"   {label}: {status}")

    print()
    print("=" * 70)
    print(f"🎯 FINAL TRUST SCORE: {data.get('trust_score')}/100")
    print("=" * 70)
    print()


def main():
    """Run API test."""
    print("=" * 70)
    print("TRUSTCARD API TEST - SOURCE CREDIBILITY")
    print("=" * 70)
    print()
    print("Make sure the API is running: docker-compose up")
    print()
    print("⚠️ NOTE: This test requires real Instagram post URLs")
    print("For best results, use posts that:")
    print("  - Have external links in the caption")
    print("  - Link to news sources")
    print("  - Link to various types of sources (reliable, unreliable, satire)")
    print()

    # Test URLs (replace with real Instagram posts)
    print("Enter Instagram post URL to test:")
    print("(or press Enter to use example URL)")
    url = input("URL: ").strip()

    if not url:
        url = "https://www.instagram.com/p/EXAMPLE/"
        print(f"Using example URL: {url}")
        print("⚠️ This will likely fail at Instagram extraction.")
        print("Replace with a real Instagram URL for actual testing.")
        print()

    try:
        test_analysis_with_source_eval(url)

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

    print()
    print("=" * 70)
    print("TESTING COMPLETE")
    print("=" * 70)
    print()
    print("To test properly:")
    print("1. Use real Instagram post URLs")
    print("2. Ensure Instagram credentials are configured")
    print("3. Check posts with various source types")
    print("4. Review source credibility ratings")


if __name__ == "__main__":
    main()
