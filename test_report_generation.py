"""
Test Report Generation

Tests HTML report card generation and opens in browser.
"""

import requests
import webbrowser
import time
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

BASE_URL = "http://localhost:8000"


def test_report_generation():
    """Test HTML report generation"""

    print("=" * 70)
    print("📄 REPORT GENERATION TEST")
    print("=" * 70)
    print()
    print("This test generates a beautiful HTML report card and opens it")
    print("in your browser.")
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

        if response.status_code not in [200, 202]:
            print(f"❌ Failed: {response.status_code}")
            print(response.json())
            return

        data = response.json()
        analysis_id = data["analysis_id"]

        print(f"✅ Analysis submitted: {analysis_id}")
        print()

    except Exception as e:
        print(f"❌ Error: {e}")
        return

    # Wait for completion
    print("⏳ Waiting for analysis to complete...")
    print("-" * 70)

    last_message = ""

    for i in range(60):
        time.sleep(3)

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
                print(f"\n✅ Analysis complete! ({total_time:.1f}s)")
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

    # Get HTML report
    print()
    print("=" * 70)
    print("📄 GENERATING HTML REPORT")
    print("=" * 70)
    print()

    report_url = f"{BASE_URL}/api/reports/{analysis_id}"

    print(f"✅ Report URL: {report_url}")
    print()

    # Display basic results
    trust_score = data.get("trust_score", 0)
    grade = data.get("grade", "N/A")
    print(f"Trust Score: {trust_score}/100 ({grade})")
    print()

    # Open in browser
    print("🌐 Opening report in browser...")
    try:
        webbrowser.open(report_url)
        print("✅ Report opened in your default browser!")
    except Exception as e:
        print(f"⚠️  Could not open browser: {e}")
        print(f"   Please open manually: {report_url}")

    print()
    print("=" * 70)
    print("✅ TEST COMPLETE!")
    print("=" * 70)
    print()
    print("The HTML report card includes:")
    print("  • Overall trust score and grade")
    print("  • Component-by-component breakdown")
    print("  • Community voting results")
    print("  • Key findings summary")
    print("  • Actionable recommendation")
    print()
    print("You can:")
    print("  • Share the report URL")
    print("  • Save as PDF (Ctrl+P → Save as PDF)")
    print("  • Submit community feedback")
    print()


if __name__ == "__main__":
    test_report_generation()
