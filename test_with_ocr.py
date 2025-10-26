"""
Test full analysis pipeline with OCR
"""
import requests
import time
import json

BASE_URL = "http://localhost:8000"

def test_analysis_with_ocr():
    """Test complete analysis with OCR"""

    print("=" * 70)
    print("🧪 TrustCard Analysis Test - With OCR")
    print("=" * 70)

    # Get Instagram URL
    print("\n📝 Enter an Instagram post URL (preferably with text in image):")
    print("   Good examples: news screenshots, memes, quote graphics")
    instagram_url = input("\nURL: ").strip()

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

    # OCR Results
    if data.get("analysis_results", {}).get("ocr"):
        ocr_results = data["analysis_results"]["ocr"]

        print("\n📝 OCR TEXT EXTRACTION:")

        if ocr_results.get("status") == "completed":
            summary = ocr_results.get("summary", {})

            print(f"   Images with Text: {summary.get('images_with_text', 0)}/{summary.get('total_images', 0)}")
            print(f"   Words Extracted: {summary.get('total_words_extracted', 0)}")
            print(f"   Confidence: {summary.get('avg_confidence', 0)}%")
            print(f"   Has Text: {summary.get('has_text', False)}")

            # Show combined text
            combined = ocr_results.get("combined", {})
            if combined.get("ocr_text"):
                print(f"\n   Extracted Text Preview:")
                text_preview = combined["ocr_text"][:200]
                print(f"   {text_preview}{'...' if len(combined['ocr_text']) > 200 else ''}")

            # Individual results
            if ocr_results.get("individual_results"):
                print(f"\n   Individual Image Results:")
                for idx, result in enumerate(ocr_results["individual_results"], 1):
                    has_text = result.get("has_text", False)
                    word_count = result.get("word_count", 0)
                    confidence = result.get("confidence", 0)
                    print(f"   {idx}. {'✅ Text found' if has_text else '❌ No text'} - {word_count} words (conf: {confidence}%)")

        elif ocr_results.get("status") == "failed":
            print(f"   ❌ Error: {ocr_results.get('error')}")

    # AI Detection Results
    if data.get("analysis_results", {}).get("ai_detection"):
        ai_results = data["analysis_results"]["ai_detection"]

        print("\n🤖 AI IMAGE DETECTION:")

        if ai_results.get("status") == "completed":
            overall = ai_results["overall"]
            print(f"   {overall['assessment']}")
            print(f"   Confidence: {overall['confidence']*100:.1f}%")

    print("\n" + "=" * 70)
    print("✅ Test Complete!")
    print("=" * 70)

if __name__ == "__main__":
    test_analysis_with_ocr()
