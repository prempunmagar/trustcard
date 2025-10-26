"""
End-to-end test of complete TrustCard API workflow
"""
import requests
import time
import json

BASE_URL = "http://localhost:8000"

def test_complete_workflow():
    """Test the complete user workflow"""

    print("=" * 70)
    print("🧪 TrustCard End-to-End API Test")
    print("=" * 70)

    # Get Instagram URL from user
    print("\n📝 Please provide an Instagram post URL to test with:")
    print("   Example: https://www.instagram.com/p/ABC123xyz/")
    instagram_url = input("\nInstagram URL: ").strip()

    if not instagram_url:
        print("❌ No URL provided, exiting")
        return

    # Step 1: Submit for analysis
    print("\n" + "=" * 70)
    print("STEP 1: Submit Instagram Post for Analysis")
    print("=" * 70)

    response = requests.post(
        f"{BASE_URL}/api/analyze",
        json={"url": instagram_url}
    )

    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    if response.status_code not in [200, 202]:
        print(f"❌ Failed to submit analysis: {response.json()}")
        return

    data = response.json()
    analysis_id = data["analysis_id"]
    post_id = data["post_id"]

    print(f"\n✅ Analysis submitted successfully!")
    print(f"   Analysis ID: {analysis_id}")
    print(f"   Post ID: {post_id}")
    print(f"   Status: {data['status']}")
    print(f"   Estimated time: {data['estimated_time']} seconds")

    # Step 2: Poll for results
    print("\n" + "=" * 70)
    print("STEP 2: Poll for Analysis Results")
    print("=" * 70)

    max_polls = 30
    poll_interval = 2

    for i in range(max_polls):
        print(f"\n📊 Poll #{i+1} (waiting {poll_interval}s between polls)...")

        response = requests.get(f"{BASE_URL}/api/results/{analysis_id}")

        if response.status_code != 200:
            print(f"❌ Failed to get results: {response.status_code}")
            print(response.json())
            return

        data = response.json()
        status = data["status"]
        progress = data.get("progress", 0)
        message = data["message"]

        print(f"   Status: {status}")
        print(f"   Progress: {progress}%")
        print(f"   Message: {message}")

        if status == "completed":
            print("\n" + "=" * 70)
            print("✅ ANALYSIS COMPLETED!")
            print("=" * 70)
            print(f"\n🎯 TRUST SCORE: {data['trust_score']}/100")
            print(f"📊 GRADE: {data['grade']}")
            print(f"⏱️  Processing Time: {data.get('processing_time')} seconds")

            if data.get("post_info"):
                post_info = data["post_info"]
                print(f"\n📸 POST INFORMATION:")
                print(f"   Type: {post_info['type']}")
                print(f"   User: @{post_info['username']}")
                caption = post_info['caption']
                print(f"   Caption: {caption[:100]}..." if len(caption) > 100 else f"   Caption: {caption}")
                print(f"   Images: {post_info['image_count']}")
                print(f"   Videos: {post_info['video_count']}")
                print(f"   Likes: {post_info['like_count']}")
                print(f"   Comments: {post_info['comment_count']}")

            if data.get("analysis_results"):
                print(f"\n🔬 ANALYSIS RESULTS:")
                print(json.dumps(data["analysis_results"], indent=2))

            break

        elif status == "failed":
            print(f"\n❌ Analysis failed: {data.get('error', 'Unknown error')}")
            break

        elif status in ["pending", "processing"]:
            time.sleep(poll_interval)
            continue

    else:
        print(f"\n⚠️  Timeout: Analysis did not complete in {max_polls * poll_interval} seconds")

    # Step 3: List recent analyses
    print("\n" + "=" * 70)
    print("STEP 3: List Recent Analyses")
    print("=" * 70)

    response = requests.get(f"{BASE_URL}/api/results?limit=5")

    if response.status_code == 200:
        data = response.json()
        print(f"\nTotal analyses: {data['total']}")
        print(f"Showing {len(data['analyses'])} most recent:\n")

        for idx, analysis in enumerate(data['analyses'], 1):
            print(f"{idx}. Analysis {analysis['analysis_id']}")
            print(f"   Post: {analysis['post_id']}")
            print(f"   Status: {analysis['status']}")
            if analysis.get('trust_score'):
                print(f"   Score: {analysis['trust_score']} ({analysis['grade']})")
            print()

    print("=" * 70)
    print("🎉 End-to-End Test Complete!")
    print("=" * 70)

if __name__ == "__main__":
    try:
        test_complete_workflow()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
