"""
Test Cache Performance

Measures the performance improvement from caching by analyzing the same URL twice.
"""

import requests
import time
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

BASE_URL = "http://localhost:8000"


def test_cache_performance():
    """Test cache performance with same URL"""

    print("=" * 70)
    print("⚡ CACHE PERFORMANCE TEST")
    print("=" * 70)
    print()
    print("This test measures caching performance by submitting the same")
    print("Instagram URL twice and comparing response times.")
    print()

    # Get Instagram URL
    print("📝 Enter an Instagram post URL:")
    instagram_url = input("URL: ").strip()

    if not instagram_url:
        print("❌ No URL provided")
        return

    # Test 1: First request (cold - no cache)
    print()
    print("=" * 70)
    print("TEST 1: First Request (No Cache - Cold)")
    print("=" * 70)

    start_time = time.time()

    response = requests.post(
        f"{BASE_URL}/api/analyze",
        json={"url": instagram_url}
    )

    if response.status_code not in [200, 202]:
        print(f"❌ Failed: {response.json()}")
        return

    data = response.json()
    analysis_id_1 = data["analysis_id"]

    print(f"✅ Analysis submitted: {analysis_id_1}")
    print("\n⏳ Waiting for completion...")

    # Wait for completion
    for i in range(60):
        time.sleep(2)

        response = requests.get(f"{BASE_URL}/api/results/{analysis_id_1}")
        data = response.json()

        status = data.get("status")
        progress = data.get("progress", 0)

        if status == "completed":
            break
        elif status == "failed":
            print(f"❌ Failed: {data.get('error')}")
            return

        print(f"\r   Progress: {progress}%   ", end="", flush=True)

    first_request_time = time.time() - start_time
    first_processing_time = data.get("processing_time", 0)
    is_cached_1 = data.get("cached", False)

    print(f"\n\n✅ First request completed!")
    print(f"   Total time: {first_request_time:.2f}s")
    print(f"   Processing time: {first_processing_time}s")
    print(f"   Trust Score: {data.get('trust_score')}/100")
    print(f"   From cache: {is_cached_1}")

    # Test 2: Second request (should be cached)
    print()
    print("=" * 70)
    print("TEST 2: Second Request (Should Use Cache - Hot)")
    print("=" * 70)

    # Wait a moment
    time.sleep(2)

    start_time = time.time()

    response = requests.post(
        f"{BASE_URL}/api/analyze",
        json={"url": instagram_url}
    )

    data = response.json()
    analysis_id_2 = data["analysis_id"]

    print(f"✅ Analysis submitted: {analysis_id_2}")

    # Check results (should be instant from cache)
    time.sleep(1)

    response = requests.get(f"{BASE_URL}/api/results/{analysis_id_2}")
    data = response.json()

    second_request_time = time.time() - start_time
    second_processing_time = data.get("processing_time", 0)
    is_cached_2 = data.get("cached", False)

    print(f"\n✅ Second request completed!")
    print(f"   Total time: {second_request_time:.2f}s")
    print(f"   Processing time: {second_processing_time}s")
    print(f"   Trust Score: {data.get('trust_score')}/100")
    print(f"   From cache: {is_cached_2}")

    # Performance comparison
    print()
    print("=" * 70)
    print("📊 PERFORMANCE COMPARISON")
    print("=" * 70)

    if second_request_time > 0:
        speedup = first_request_time / second_request_time
    else:
        speedup = 0

    time_saved = first_request_time - second_request_time

    print(f"\n   First Request (Cold):  {first_request_time:.2f}s")
    print(f"   Second Request (Hot):  {second_request_time:.2f}s")
    print(f"   Time Saved:            {time_saved:.2f}s")
    print(f"   Speedup:               {speedup:.1f}x faster")

    if is_cached_2:
        print(f"\n   ✅ Cache is working! {speedup:.0f}x performance improvement!")
        print(f"   ⚡ Cached requests are nearly instant!")
    else:
        print(f"\n   ⚠️  Cache may not be working properly")
        print(f"   Check Redis connection and cache_manager logs")

    # Cache stats
    print()
    print("=" * 70)
    print("💾 CACHE STATISTICS")
    print("=" * 70)

    try:
        response = requests.get(f"{BASE_URL}/api/cache/stats")
        if response.status_code == 200:
            stats = response.json()
            print(f"\n   Status: {stats.get('status')}")
            print(f"   Cached Analyses: {stats.get('analysis_cached', 0)}")
            print(f"   Cached Instagram Data: {stats.get('instagram_cached', 0)}")
            print(f"   Memory Used: {stats.get('memory_used', 'N/A')}")
            print(f"   Hit Rate: {stats.get('hit_rate', 0)}%")
    except Exception as e:
        print(f"\n   ⚠️  Could not fetch cache stats: {e}")

    print()
    print("=" * 70)
    print("✅ CACHE PERFORMANCE TEST COMPLETE!")
    print("=" * 70)
    print()
    print("Key Findings:")
    print(f"  • First analysis took {first_request_time:.1f}s (full ML processing)")
    print(f"  • Second analysis took {second_request_time:.1f}s (cached)")
    print(f"  • Performance gain: {speedup:.0f}x faster")
    print(f"  • Cache is {'✅ working' if is_cached_2 else '❌ not working'}")
    print()


if __name__ == "__main__":
    test_cache_performance()
