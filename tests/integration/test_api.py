"""
Integration tests for TrustCard API endpoints.

Tests API routes with database interactions.
"""
import pytest


@pytest.mark.integration
class TestHealthEndpoints:
    """Test health check endpoints."""

    def test_root_endpoint(self, client):
        """GET / should return welcome message."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "TrustCard" in data["message"]

    def test_health_endpoint(self, client):
        """GET /health should return health status."""
        response = client.get("/health")

        # Health endpoint may return 200 (healthy) or 503 (unhealthy)
        assert response.status_code in [200, 503]
        data = response.json()
        assert "status" in data
        assert "checks" in data

    def test_status_endpoint(self, client):
        """GET /status should return system status."""
        response = client.get("/status")

        assert response.status_code == 200
        data = response.json()
        assert "application" in data
        assert "configuration" in data


@pytest.mark.integration
class TestAnalysisEndpoints:
    """Test analysis API endpoints."""

    def test_analyze_requires_url(self, client):
        """POST /api/analyze should require instagram_url."""
        response = client.post("/api/analyze", json={})

        assert response.status_code == 422  # Validation error

    def test_analyze_rejects_invalid_url(self, client):
        """POST /api/analyze should reject invalid URLs."""
        response = client.post(
            "/api/analyze",
            json={"url": "https://facebook.com/post/123"}
        )

        assert response.status_code in [400, 422]

    def test_list_analyses(self, client):
        """GET /api/results should return list of analyses."""
        response = client.get("/api/results")

        assert response.status_code == 200
        data = response.json()
        assert "analyses" in data
        assert "total" in data
        assert isinstance(data["analyses"], list)

    def test_list_analyses_pagination(self, client):
        """GET /api/results should support pagination."""
        response = client.get("/api/results?skip=0&limit=5")

        assert response.status_code == 200
        data = response.json()
        assert len(data["analyses"]) <= 5

    def test_get_nonexistent_analysis(self, client):
        """GET /api/results/{id} should return 404 for nonexistent analysis."""
        # Using a valid UUID format but nonexistent
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/api/results/{fake_uuid}")

        assert response.status_code == 404


@pytest.mark.integration
class TestCacheEndpoints:
    """Test cache management endpoints."""

    def test_cache_stats(self, client):
        """GET /api/cache/stats should return cache statistics."""
        response = client.get("/api/cache/stats")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data


@pytest.mark.integration
class TestReportEndpoints:
    """Test report and feedback endpoints."""

    def test_get_nonexistent_report(self, client):
        """GET /api/reports/{id} should return 404."""
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/api/reports/{fake_uuid}")

        assert response.status_code == 404

    def test_submit_feedback_requires_vote_type(self, client):
        """POST /api/reports/{id}/feedback should require vote_type."""
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        response = client.post(f"/api/reports/{fake_uuid}/feedback", json={})

        assert response.status_code == 422  # Validation error

    def test_submit_feedback_rejects_invalid_vote_type(self, client):
        """POST /api/reports/{id}/feedback should reject invalid vote types."""
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        response = client.post(
            f"/api/reports/{fake_uuid}/feedback",
            json={"vote_type": "invalid_vote"}
        )

        assert response.status_code == 422  # Validation error
