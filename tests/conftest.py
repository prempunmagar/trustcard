"""
Pytest configuration and fixtures.

Provides shared test fixtures for database, client, and sample data.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import get_db
from app.models.base import Base

# Test database (in-memory SQLite)
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def test_db():
    """
    Create a fresh test database for each test.

    Uses in-memory SQLite for fast, isolated testing.
    """
    engine = create_engine(
        SQLALCHEMY_TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Create all tables
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Drop all tables after test
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(test_db):
    """
    Create a test client with test database.

    Overrides the get_db dependency to use test database.
    """
    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    # Clear overrides after test
    app.dependency_overrides.clear()


@pytest.fixture
def sample_instagram_url():
    """Sample Instagram URL for testing."""
    return "https://www.instagram.com/p/CXyZ123abc/"


@pytest.fixture
def sample_post_id():
    """Sample Instagram post ID."""
    return "CXyZ123abc"


@pytest.fixture
def sample_analysis_data():
    """Sample analysis data for testing."""
    return {
        "instagram_url": "https://www.instagram.com/p/CXyZ123abc/",
        "post_id": "CXyZ123abc",
        "content": {
            "images": ["https://example.com/image.jpg"],
            "caption": "Test caption for analysis",
            "video": None,
            "user": {
                "username": "testuser",
                "full_name": "Test User",
                "is_verified": False
            }
        },
        "results": {
            "ai_detection": {
                "is_ai_generated": False,
                "confidence": 0.95,
                "overall_assessment": "real"
            },
            "ocr": {
                "has_text": False,
                "extracted_text": ""
            },
            "deepfake": {
                "is_manipulated": False,
                "confidence": 0.95
            },
            "fact_checking": {
                "overall_verdict": "INCONCLUSIVE",
                "claims": []
            },
            "source_credibility": {
                "overall_credibility": "unknown"
            }
        },
        "trust_score": 85.0,
        "status": "completed"
    }


@pytest.fixture
def sample_feedback_data():
    """Sample feedback data for testing."""
    return {
        "vote_type": "accurate",
        "comment": "This analysis looks accurate to me!"
    }


@pytest.fixture
def mock_instagram_response():
    """Mock Instagram API response."""
    return {
        "post_id": "CXyZ123abc",
        "url": "https://www.instagram.com/p/CXyZ123abc/",
        "type": "photo",
        "caption": "Amazing sunset view! 🌅",
        "username": "testuser",
        "full_name": "Test User",
        "is_verified": False,
        "timestamp": "2024-01-15T10:30:00Z",
        "like_count": 1234,
        "comment_count": 56,
        "location": "New York, NY",
        "images": ["https://example.com/image1.jpg"],
        "video": None,
        "has_audio": False
    }


@pytest.fixture
def mock_ai_detection_result():
    """Mock AI detection result."""
    return {
        "is_ai_generated": False,
        "confidence": 0.95,
        "overall_assessment": "real",
        "images": [
            {
                "is_ai_generated": False,
                "confidence": 0.95,
                "model_scores": {
                    "real_score": 0.95,
                    "ai_score": 0.05
                }
            }
        ]
    }


@pytest.fixture
def mock_deepfake_result():
    """Mock deepfake detection result."""
    return {
        "is_manipulated": False,
        "confidence": 0.90,
        "manipulation_type": None,
        "suspicious_frames": []
    }


@pytest.fixture
def mock_fact_check_result():
    """Mock fact-checking result."""
    return {
        "overall_verdict": "INCONCLUSIVE",
        "claims": [],
        "patterns_detected": [],
        "red_flags": []
    }


@pytest.fixture
def mock_source_credibility_result():
    """Mock source credibility result."""
    return {
        "overall_credibility": "unknown",
        "publisher": None,
        "instagram_verified": False
    }
