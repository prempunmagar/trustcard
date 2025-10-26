"""
Test Error Handling and Exception System

Tests custom exceptions, global exception handlers, and error responses.
"""
import requests
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

BASE_URL = "http://localhost:8000"


def test_invalid_url():
    """Test invalid Instagram URL"""
    print("\n" + "=" * 70)
    print("TEST 1: Invalid Instagram URL")
    print("=" * 70)

    response = requests.post(
        f"{BASE_URL}/api/analyze",
        json={"url": "https://www.youtube.com/watch?v=abc123"}
    )

    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")

    assert response.status_code == 422, "Should return 422 for invalid URL"
    print("✅ PASS: Invalid URL rejected")


def test_missing_url():
    """Test missing URL field"""
    print("\n" + "=" * 70)
    print("TEST 2: Missing URL Field")
    print("=" * 70)

    response = requests.post(
        f"{BASE_URL}/api/analyze",
        json={}
    )

    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")

    assert response.status_code == 422, "Should return 422 for missing field"
    print("✅ PASS: Missing field rejected")


def test_invalid_analysis_id():
    """Test invalid analysis ID format"""
    print("\n" + "=" * 70)
    print("TEST 3: Invalid Analysis ID")
    print("=" * 70)

    response = requests.get(f"{BASE_URL}/api/results/invalid-uuid")

    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")

    assert response.status_code == 422, "Should return 422 for invalid UUID"
    print("✅ PASS: Invalid UUID rejected")


def test_nonexistent_analysis():
    """Test nonexistent analysis ID"""
    print("\n" + "=" * 70)
    print("TEST 4: Nonexistent Analysis ID")
    print("=" * 70)

    # Valid UUID but doesn't exist
    fake_uuid = "00000000-0000-0000-0000-000000000000"
    response = requests.get(f"{BASE_URL}/api/results/{fake_uuid}")

    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")

    assert response.status_code == 404, "Should return 404 for nonexistent analysis"
    print("✅ PASS: Nonexistent analysis returns 404")


def test_invalid_vote_type():
    """Test invalid feedback vote type"""
    print("\n" + "=" * 70)
    print("TEST 5: Invalid Vote Type")
    print("=" * 70)

    # Need a valid analysis ID for this test
    # Using fake UUID for demonstration
    fake_uuid = "00000000-0000-0000-0000-000000000000"

    response = requests.post(
        f"{BASE_URL}/api/reports/{fake_uuid}/feedback",
        json={
            "vote_type": "invalid_vote",
            "comment": "Test comment"
        }
    )

    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")

    assert response.status_code == 422, "Should return 422 for invalid vote type"
    print("✅ PASS: Invalid vote type rejected")


def test_comment_too_long():
    """Test comment length validation"""
    print("\n" + "=" * 70)
    print("TEST 6: Comment Too Long")
    print("=" * 70)

    fake_uuid = "00000000-0000-0000-0000-000000000000"

    # Create a comment that's too long (> 1000 characters)
    long_comment = "A" * 1001

    response = requests.post(
        f"{BASE_URL}/api/reports/{fake_uuid}/feedback",
        json={
            "vote_type": "accurate",
            "comment": long_comment
        }
    )

    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")

    assert response.status_code == 422, "Should return 422 for comment too long"
    print("✅ PASS: Long comment rejected")


def test_url_too_long():
    """Test URL length validation"""
    print("\n" + "=" * 70)
    print("TEST 7: URL Too Long")
    print("=" * 70)

    # Create a URL that's too long (> 2000 characters)
    long_url = "https://www.instagram.com/p/" + "A" * 2000 + "/"

    response = requests.post(
        f"{BASE_URL}/api/analyze",
        json={"url": long_url}
    )

    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")

    assert response.status_code == 422, "Should return 422 for URL too long"
    print("✅ PASS: Long URL rejected")


def test_health_endpoint():
    """Test health check endpoint"""
    print("\n" + "=" * 70)
    print("TEST 8: Health Check")
    print("=" * 70)

    response = requests.get(f"{BASE_URL}/health")

    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")

    assert response.status_code in [200, 503], "Health check should return 200 or 503"
    print("✅ PASS: Health check working")


def test_status_endpoint():
    """Test status endpoint"""
    print("\n" + "=" * 70)
    print("TEST 9: System Status")
    print("=" * 70)

    response = requests.get(f"{BASE_URL}/status")

    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")

    assert response.status_code == 200, "Status should return 200"

    data = response.json()
    assert "application" in data
    assert "configuration" in data
    assert "database" in data
    assert "cache" in data

    print("✅ PASS: Status endpoint working")


def test_security_headers():
    """Test security headers are present"""
    print("\n" + "=" * 70)
    print("TEST 10: Security Headers")
    print("=" * 70)

    response = requests.get(f"{BASE_URL}/")

    headers = response.headers
    print(f"Status Code: {response.status_code}")
    print("\nSecurity Headers:")

    security_headers = [
        "X-Content-Type-Options",
        "X-Frame-Options",
        "X-XSS-Protection",
        "Content-Security-Policy",
        "Referrer-Policy",
        "Permissions-Policy"
    ]

    for header in security_headers:
        if header in headers:
            print(f"  ✅ {header}: {headers[header]}")
        else:
            print(f"  ❌ {header}: MISSING")

    assert "X-Content-Type-Options" in headers, "Security headers should be present"
    print("\n✅ PASS: Security headers present")


def run_all_tests():
    """Run all error handling tests"""
    print("\n" + "=" * 70)
    print("🧪 ERROR HANDLING & VALIDATION TEST SUITE")
    print("=" * 70)

    tests = [
        test_invalid_url,
        test_missing_url,
        test_invalid_analysis_id,
        test_nonexistent_analysis,
        test_invalid_vote_type,
        test_comment_too_long,
        test_url_too_long,
        test_health_endpoint,
        test_status_endpoint,
        test_security_headers
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

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
