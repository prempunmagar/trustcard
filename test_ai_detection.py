"""
Test AI image detection service
"""
from app.services.ai_detection_service import ai_detection_service

def test_ai_detection():
    """Test AI detection with sample images"""

    print("=" * 70)
    print("🤖 AI Image Detection Test")
    print("=" * 70)

    # Initialize model
    print("\n📦 Initializing AI detection model...")
    ai_detection_service.initialize()

    # Test images (you can replace with your own)
    test_images = {
        "Real Photo": "https://images.unsplash.com/photo-1506744038136-46273834b3fb",
        # Add AI-generated image URLs here for testing
        # "AI Generated": "url-to-ai-image"
    }

    print("\n" + "=" * 70)
    print("Testing Image Detection")
    print("=" * 70)

    for label, url in test_images.items():
        print(f"\n📸 Testing: {label}")
        print(f"   URL: {url[:60]}...")

        result = ai_detection_service.detect_from_url(url)

        if "error" in result:
            print(f"   ❌ Error: {result['error']}")
            continue

        is_ai = result["is_ai_generated"]
        confidence = result["confidence"]
        ai_score = result["ai_score"]
        real_score = result["real_score"]
        inference_time = result["inference_time"]
        device = result["device"]

        print(f"\n   Results:")
        print(f"   - AI Generated: {'YES' if is_ai else 'NO'}")
        print(f"   - Confidence: {confidence*100:.1f}%")
        print(f"   - AI Score: {ai_score*100:.1f}%")
        print(f"   - Real Score: {real_score*100:.1f}%")
        print(f"   - Inference Time: {inference_time}s")
        print(f"   - Device: {device}")

        if is_ai:
            print(f"   ⚠️  This image appears to be AI-generated")
        else:
            print(f"   ✅ This image appears to be a real photograph")

    print("\n" + "=" * 70)
    print("✅ AI Detection Test Complete")
    print("=" * 70)

if __name__ == "__main__":
    test_ai_detection()
