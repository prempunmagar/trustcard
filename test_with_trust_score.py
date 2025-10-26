"""
Test Full Analysis with Trust Score Breakdown

End-to-end test of the complete analysis pipeline with detailed trust score breakdown.
"""

import requests
import time
import sys
from pathlib import Path
import json

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

BASE_URL = "http://localhost:8000"


def print_section(title: str):
    """Print a section header"""
    print()
    print("=" * 70)
    print(title)
    print("=" * 70)
    print()


def print_trust_score_breakdown(breakdown: dict):
    """Pretty print trust score breakdown"""
    print_section("📊 TRUST SCORE BREAKDOWN")

    print(f"Final Score: {breakdown.get('final_score', 'N/A')}/100")
    print(f"Grade: {breakdown.get('grade', 'N/A')}")

    grade_info = breakdown.get('grade_info', {})
    if grade_info:
        print(f"Description: {grade_info.get('description', 'N/A')}")
        print(f"Emoji: {grade_info.get('emoji', '')}")
    print()

    # Component scores
    component_scores = breakdown.get('component_scores', {})
    if component_scores:
        print("Component Impact:")
        for component, score in component_scores.items():
            sign = "+" if score >= 0 else ""
            print(f"  {component}: {sign}{score:.1f}")
        print()

    # Summary
    print(f"Total Penalties: {breakdown.get('total_penalties', 0)}")
    print(f"Total Bonuses: {breakdown.get('total_bonuses', 0)}")
    print()

    # Detailed adjustments
    adjustments = breakdown.get('adjustments', [])
    if adjustments:
        print("Detailed Adjustments:")
        for adj in adjustments:
            sign = "+" if adj['impact'] >= 0 else ""
            print(f"  [{adj['component']}] {adj['category']}")
            print(f"    Impact: {sign}{adj['impact']:.1f} points")
            print(f"    Reason: {adj['reason']}")
            print()

    # Flags
    flags = breakdown.get('flags', [])
    if flags:
        print("⚠️  Warning Flags:")
        for flag in flags:
            print(f"  • {flag}")
        print()

    # Review flag
    if breakdown.get('requires_review'):
        print("🔴 FLAGGED FOR MANUAL REVIEW")
        print()


def test_full_analysis():
    """Test complete analysis pipeline with trust score breakdown"""

    print_section("⚡ FULL ANALYSIS TEST WITH TRUST SCORE BREAKDOWN")

    print("This test runs a complete analysis and displays the detailed trust score")
    print("breakdown showing exactly how the final score was calculated.")
    print()

    print("📝 Enter an Instagram post URL to analyze:")
    print("   (For best results, use a post with text, images, and/or videos)")
    instagram_url = input("URL: ").strip()

    if not instagram_url:
        print("❌ No URL provided")
        return

    # Submit analysis
    print()
    print("📤 Submitting analysis...")
    start_time = time.time()

    try:
        response = requests.post(
            f"{BASE_URL}/api/analyze",
            json={"url": instagram_url}
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

    # Track progress
    print("⏱️  Tracking analysis progress...")
    print("-" * 70)

    last_message = ""

    for i in range(60):
        time.sleep(2)

        try:
            response = requests.get(f"{BASE_URL}/api/results/{analysis_id}")
            data = response.json()

            status = data.get("status")
            message = data.get("message", "Processing...")
            elapsed = time.time() - start_time

            # Only print when message changes
            if message != last_message:
                print(f"[{elapsed:5.1f}s] {message}")
                last_message = message

            if status == "completed":
                total_time = elapsed
                break
            elif status == "failed":
                print(f"\n❌ Failed: {data.get('error')}")
                return

        except Exception as e:
            print(f"Error: {e}")
            continue

    if status != "completed":
        print("\n❌ Timeout waiting for results")
        return

    # Display results
    print_section("📊 ANALYSIS COMPLETE")

    print(f"Total Analysis Time: {total_time:.1f}s")
    print()

    # Basic info
    post_info = data.get("post_info", {})
    if post_info:
        print("Instagram Post Info:")
        print(f"  Post ID: {post_info.get('post_id', 'N/A')}")
        print(f"  Type: {post_info.get('type', 'N/A')}")
        print(f"  Username: @{post_info.get('username', 'N/A')}")
        print(f"  Verified: {'✓' if post_info.get('is_verified') else '✗'}")
        print(f"  Images: {post_info.get('image_count', 0)}")
        print(f"  Videos: {post_info.get('video_count', 0)}")
        print()

    # Trust Score & Grade
    trust_score = data.get("trust_score")
    grade = data.get("grade")

    if trust_score is not None:
        print(f"Trust Score: {trust_score}/100")
        print(f"Grade: {grade}")
        print()

    # Detailed breakdown
    breakdown = data.get("trust_score_breakdown")
    if breakdown:
        print_trust_score_breakdown(breakdown)
    else:
        print("⚠️  No detailed breakdown available (using older analysis format)")
        print()

    # Component status
    results = data.get("analysis_results", {})
    if results:
        print_section("🔍 COMPONENT STATUS")

        components = [
            ("Instagram Extraction", "instagram_extraction"),
            ("AI Detection", "ai_detection"),
            ("OCR Extraction", "ocr"),
            ("Deepfake Detection", "deepfake"),
            ("Fact-Checking", "fact_check"),
            ("Source Evaluation", "source_credibility")
        ]

        for label, key in components:
            component = results.get(key, {})
            status = component.get("status", "unknown")
            print(f"  {label}: {status}")

        print()

    # Processing time
    processing_time = data.get("processing_time")
    if processing_time:
        print(f"⏱️  Processing Time: {processing_time}s")
        print()

    print_section("✅ TEST COMPLETE")

    # Export breakdown to JSON file
    if breakdown:
        print("📁 Exporting breakdown to JSON...")
        output_file = f"trust_score_breakdown_{analysis_id}.json"
        with open(output_file, 'w') as f:
            json.dump(breakdown, f, indent=2)
        print(f"   Saved to: {output_file}")
        print()


def test_retrieve_existing():
    """Test retrieving an existing analysis"""

    print_section("🔍 RETRIEVE EXISTING ANALYSIS")

    print("Enter analysis ID to retrieve:")
    analysis_id = input("Analysis ID: ").strip()

    if not analysis_id:
        print("❌ No ID provided")
        return

    try:
        response = requests.get(f"{BASE_URL}/api/results/{analysis_id}")

        if response.status_code != 200:
            print(f"❌ Failed: {response.status_code}")
            print(response.text)
            return

        data = response.json()

        # Display trust score breakdown
        breakdown = data.get("trust_score_breakdown")
        if breakdown:
            print_trust_score_breakdown(breakdown)
        else:
            print("⚠️  No breakdown available for this analysis")

        print_section("✅ RETRIEVAL COMPLETE")

    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    """Main test menu"""
    print()
    print("=" * 70)
    print("TRUST SCORE BREAKDOWN TEST")
    print("=" * 70)
    print()
    print("Choose test mode:")
    print("1. Run full analysis with new Instagram URL")
    print("2. Retrieve existing analysis by ID")
    print()

    choice = input("Choice (1 or 2): ").strip()

    if choice == "1":
        test_full_analysis()
    elif choice == "2":
        test_retrieve_existing()
    else:
        print("Invalid choice")


if __name__ == "__main__":
    main()
