"""
Test full analysis pipeline with AI detection
"""
import requests
import time
import json

BASE_URL = "http://localhost:8000"

def test_analysis_with_ai():
    """Test complete analysis with AI detection"""

    print("=" * 70)
    print("🧪 TrustCard Analysis Test - With AI Detection")
    print("=" * 70)

    # Get Instagram URL
    print("\n📝 Enter an Instagram post URL to analyze:")
    instagram_url = input("URL: ").strip()

    if not instagram_url:
        print("❌ No URL provided")
        return

    # Submit analysis
    print("\n📤 Submitting analysis...")
    response = requests.post(
        f"{BASE_URL}/api/analyze",
        json={"url": instagram_url}
    )

    if response.status_code not in [200, 202]:
        print(f"❌ Failed: {response.json()}")
        return

    data = response.json()
    analysis_id = data["analysis_id"]

    print(f"✅ Analysis submitted: {analysis_id}")

    # Poll for results
    print("\n⏳ Waiting for analysis to complete...")
    print("   (This may take 30-60 seconds for first run - model loading)")

    for i in range(40):
        time.sleep(3)

        response = requests.get(f"{BASE_URL}/api/results/{analysis_id}")
        data = response.json()

        status = data["status"]
        progress = data.get("progress", 0)
        message = data["message"]

        print(f"\r   [{progress:3d}%] {message}", end="", flush=True)

        if status == "completed":
            print("\n")
            break
        elif status == "failed":
            print(f"\n❌ Failed: {data.get('error')}")
            return

    # Display results
    print("\n" + "=" * 70)
    print("📊 ANALYSIS RESULTS")
    print("=" * 70)

    print(f"\n🎯 Trust Score: {data['trust_score']}/100")
    print(f"📊 Grade: {data['grade']}")
    print(f"⏱️  Processing Time: {data['processing_time']}s")

    # AI Detection Results
    if data.get("analysis_results", {}).get("ai_detection"):
        ai_results = data["analysis_results"]["ai_detection"]

        print("\n🤖 AI IMAGE DETECTION:")

        if ai_results.get("status") == "completed":
            overall = ai_results["overall"]

            print(f"   Overall: {overall['assessment']}")
            print(f"   Confidence: {overall['confidence']*100:.1f}%")
            print(f"   Total Images: {overall['total_images']}")
            print(f"   AI Images: {overall['ai_images']}")
            print(f"   Real Images: {overall['real_images']}")

            # Individual results
            if ai_results.get("individual_results"):
                print("\n   Individual Image Results:")
                for idx, result in enumerate(ai_results["individual_results"], 1):
                    is_ai = result.get("is_ai_generated")
                    conf = result.get("confidence", 0)
                    print(f"   {idx}. {'⚠️  AI' if is_ai else '✅ Real'} - Confidence: {conf*100:.1f}%")

        elif ai_results.get("status") == "skipped":
            print(f"   {ai_results.get('reason')}")

        elif ai_results.get("status") == "failed":
            print(f"   ❌ Error: {ai_results.get('error')}")

    print("\n" + "=" * 70)

if __name__ == "__main__":
    test_analysis_with_ai()
