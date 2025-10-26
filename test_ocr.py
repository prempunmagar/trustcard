"""
Test OCR service
"""
from app.services.ocr_service import ocr_service

def test_ocr():
    """Test OCR with sample images"""

    print("=" * 70)
    print("📝 OCR Text Extraction Test")
    print("=" * 70)

    # Test images with text
    test_images = {
        "Sample Text Image": "https://via.placeholder.com/800x400/000000/FFFFFF/?text=BREAKING+NEWS+HEADLINE",
        "Quote Image": "https://via.placeholder.com/600x600/4A90E2/FFFFFF/?text=Famous+Quote+Here",
        # Add real images with text for testing
    }

    print("\n📸 Testing OCR on sample images...")
    print("Note: For best results, test with real Instagram screenshots or images with text")

    for label, url in test_images.items():
        print(f"\n{'='*70}")
        print(f"Image: {label}")
        print(f"URL: {url[:60]}...")
        print("="*70)

        result = ocr_service.extract_from_url(url)

        if "error" in result:
            print(f"❌ Error: {result['error']}")
            continue

        text = result.get("text", "")
        word_count = result.get("word_count", 0)
        confidence = result.get("confidence", 0)
        has_text = result.get("has_text", False)

        print(f"\n📊 Results:")
        print(f"   Has Text: {'YES' if has_text else 'NO'}")
        print(f"   Word Count: {word_count}")
        print(f"   Confidence: {confidence}%")

        if text:
            print(f"\n📄 Extracted Text:")
            print(f"   {text[:200]}{'...' if len(text) > 200 else ''}")
        else:
            print(f"\n   No text detected in image")

    print("\n" + "=" * 70)
    print("✅ OCR Test Complete")
    print("=" * 70)
    print("\nTip: For better testing, use Instagram posts with:")
    print("  - News screenshots")
    print("  - Memes with text")
    print("  - Quote graphics")
    print("  - Infographics with data")

if __name__ == "__main__":
    test_ocr()
