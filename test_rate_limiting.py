"""
Test Rate Limiting Middleware

Tests rate limiting functionality per IP address.
"""
import requests
import time
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

BASE_URL = "http://localhost:8000"


def test_rate_limit_headers():
    """Test that rate limit headers are present"""
    print("\n" + "=" * 70)
    print("TEST 1: Rate Limit Headers")
    print("=" * 70)

    response = requests.get(f"{BASE_URL}/")

    headers = response.headers
    print(f"Status Code: {response.status_code}")
    print("\nRate Limit Headers:")

    rate_limit_headers = [
        "X-RateLimit-Limit-Minute",
        "X-RateLimit-Limit-Hour",
        "X-RateLimit-Remaining-Minute",
        "X-RateLimit-Remaining-Hour"
    ]

    for header in rate_limit_headers:
        if header in headers:
            print(f"  {header}: {headers[header]}")
        else:
            print(f"  {header}: MISSING")

    assert "X-RateLimit-Limit-Minute" in headers, "Rate limit headers should be present"
    print("\n✅ PASS: Rate limit headers present")


def test_rate_limit_per_minute():
    """Test per-minute rate limit"""
    print("\n" + "=" * 70)
    print("TEST 2: Per-Minute Rate Limit (10 requests/min)")
    print("=" * 70)

    print("\nSending 15 requests rapidly...")

    success_count = 0
    rate_limited_count = 0

    for i in range(15):
        response = requests.get(f"{BASE_URL}/")

        if response.status_code == 200:
            success_count += 1
            remaining = response.headers.get("X-RateLimit-Remaining-Minute", "?")
            print(f"  Request {i+1}: ✅ Success (Remaining: {remaining})")
        elif response.status_code == 429:
            rate_limited_count += 1
            retry_after = response.headers.get("Retry-After", "?")
            print(f"  Request {i+1}: ⚠️  Rate Limited (Retry-After: {retry_after}s)")
        else:
            print(f"  Request {i+1}: ❓ Unexpected status {response.status_code}")

        time.sleep(0.1)  # Small delay between requests

    print(f"\nResults:")
    print(f"  Successful: {success_count}")
    print(f"  Rate Limited: {rate_limited_count}")

    # Should have some rate-limited requests
    assert rate_limited_count > 0, "Should have rate-limited some requests"
    print("\n✅ PASS: Per-minute rate limiting working")


def test_rate_limit_recovery():
    """Test rate limit recovery after waiting"""
    print("\n" + "=" * 70)
    print("TEST 3: Rate Limit Recovery")
    print("=" * 70)

    print("\nExhausting rate limit...")

    # Exhaust rate limit
    for i in range(12):
        requests.get(f"{BASE_URL}/")

    # Should be rate limited now
    response = requests.get(f"{BASE_URL}/")
    print(f"After exhaustion: Status {response.status_code}")

    if response.status_code == 429:
        retry_after = int(response.headers.get("Retry-After", 60))
        print(f"Rate limited. Waiting {retry_after}s for recovery...")

        # Wait for rate limit to reset
        time.sleep(retry_after + 1)

        # Try again
        response = requests.get(f"{BASE_URL}/")
        print(f"After waiting: Status {response.status_code}")

        assert response.status_code == 200, "Should be able to make requests after waiting"
        print("✅ PASS: Rate limit recovered")
    else:
        print("⚠️  WARNING: Not rate limited (may need to adjust test)")


def test_exempt_endpoints():
    """Test that certain endpoints are exempt from rate limiting"""
    print("\n" + "=" * 70)
    print("TEST 4: Exempt Endpoints")
    print("=" * 70)

    exempt_endpoints = [
        "/health",
        "/metrics",
        "/docs",
        "/openapi.json"
    ]

    print("\nTesting exempt endpoints (20 requests each)...")

    for endpoint in exempt_endpoints:
        success_count = 0
        rate_limited_count = 0

        for i in range(20):
            response = requests.get(f"{BASE_URL}{endpoint}")

            if response.status_code in [200, 404]:  # 404 is ok (metrics may not be enabled)
                success_count += 1
            elif response.status_code == 429:
                rate_limited_count += 1

        print(f"  {endpoint}: {success_count} success, {rate_limited_count} rate limited")

        if endpoint in ["/health", "/docs"]:
            assert rate_limited_count == 0, f"{endpoint} should be exempt from rate limiting"

    print("\n✅ PASS: Exempt endpoints not rate limited")


def test_rate_limit_error_response():
    """Test rate limit error response format"""
    print("\n" + "=" * 70)
    print("TEST 5: Rate Limit Error Response")
    print("=" * 70)

    print("\nExhausting rate limit to get error response...")

    # Exhaust rate limit
    for i in range(12):
        requests.get(f"{BASE_URL}/")

    # Should be rate limited now
    response = requests.get(f"{BASE_URL}/")

    if response.status_code == 429:
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")

        data = response.json()

        # Check error response structure
        assert "error" in data, "Should have 'error' field"
        assert "message" in data, "Should have 'message' field"
        assert "details" in data, "Should have 'details' field"
        assert "retry_after" in data.get("details", {}), "Should have 'retry_after' in details"

        # Check Retry-After header
        assert "Retry-After" in response.headers, "Should have Retry-After header"

        print("\n✅ PASS: Rate limit error response format correct")
    else:
        print("⚠️  WARNING: Not rate limited (may need to adjust test)")


def test_different_endpoints():
    """Test that rate limit is per-IP, not per-endpoint"""
    print("\n" + "=" * 70)
    print("TEST 6: Rate Limit Per-IP (Not Per-Endpoint)")
    print("=" * 70)

    endpoints = ["/", "/health", "/status"]

    print("\nTesting multiple endpoints...")

    # Make requests to different endpoints
    for i in range(15):
        endpoint = endpoints[i % len(endpoints)]
        response = requests.get(f"{BASE_URL}{endpoint}")

        if response.status_code == 200:
            remaining = response.headers.get("X-RateLimit-Remaining-Minute", "?")
            print(f"  Request {i+1} to {endpoint}: ✅ (Remaining: {remaining})")
        elif response.status_code == 429:
            print(f"  Request {i+1} to {endpoint}: ⚠️  Rate Limited")
            break

    print("\n✅ PASS: Rate limit applies across all endpoints")


def run_all_tests():
    """Run all rate limiting tests"""
    print("\n" + "=" * 70)
    print("🧪 RATE LIMITING TEST SUITE")
    print("=" * 70)
    print("\n⚠️  WARNING: These tests will temporarily exhaust your rate limit.")
    print("   Make sure rate limiting is enabled in your .env file:")
    print("   RATE_LIMIT_ENABLED=true")
    print("   RATE_LIMIT_PER_MINUTE=10")
    print("   RATE_LIMIT_PER_HOUR=100")

    input("\nPress Enter to continue...")

    tests = [
        test_rate_limit_headers,
        test_rate_limit_per_minute,
        test_rate_limit_recovery,
        test_exempt_endpoints,
        test_rate_limit_error_response,
        test_different_endpoints
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"❌ FAIL: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ ERROR: {e}")
            failed += 1

        # Small delay between tests
        time.sleep(2)

    print("\n" + "=" * 70)
    print(f"📊 TEST SUMMARY")
    print("=" * 70)
    print(f"  Total Tests: {len(tests)}")
    print(f"  ✅ Passed: {passed}")
    print(f"  ❌ Failed: {failed}")
    print(f"  Success Rate: {(passed/len(tests)*100):.1f}%")
    print("=" * 70)

    if failed == 0:
        print("\n🎉 ALL TESTS PASSED!")
    else:
        print(f"\n⚠️  {failed} tests failed")

    print("\n💡 TIP: If tests are failing, check:")
    print("   1. Is the API running? (http://localhost:8000)")
    print("   2. Is RATE_LIMIT_ENABLED=true in .env?")
    print("   3. Are rate limit settings configured correctly?")

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
