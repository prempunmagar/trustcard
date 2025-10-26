"""
Pydantic schemas for analysis endpoints
"""
from pydantic import BaseModel, HttpUrl, Field, field_validator, constr
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID
from app.config import settings

class AnalyzeRequest(BaseModel):
    """Request model for POST /analyze"""
    url: HttpUrl = Field(
        ...,
        description="Instagram post URL to analyze",
        max_length=settings.MAX_URL_LENGTH,
        examples=["https://www.instagram.com/p/ABC123xyz/"]
    )

    @field_validator('url')
    @classmethod
    def validate_instagram_url(cls, v):
        """Ensure URL is from Instagram and within length limit"""
        url_str = str(v)

        # Length check
        if len(url_str) > settings.MAX_URL_LENGTH:
            raise ValueError(f'URL too long (max {settings.MAX_URL_LENGTH} characters)')

        # Domain check
        if not any(domain in url_str for domain in ['instagram.com', 'instagr.am']):
            raise ValueError('URL must be from Instagram (instagram.com or instagr.am)')

        # Path check
        if not any(path in url_str for path in ['/p/', '/reel/', '/tv/']):
            raise ValueError('URL must be an Instagram post (/p/), reel (/reel/), or IGTV (/tv/) link')

        return v

    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://www.instagram.com/p/ABC123xyz/"
            }
        }

class AnalyzeResponse(BaseModel):
    """Response model for POST /analyze"""
    analysis_id: UUID
    post_id: str
    status: str
    message: str
    estimated_time: int = Field(..., description="Estimated completion time in seconds")

    class Config:
        json_schema_extra = {
            "example": {
                "analysis_id": "123e4567-e89b-12d3-a456-426614174000",
                "post_id": "ABC123xyz",
                "status": "pending",
                "message": "Analysis started successfully",
                "estimated_time": 30
            }
        }

class InstagramPostInfo(BaseModel):
    """Instagram post information"""
    post_id: str
    url: str
    type: str
    caption: str
    username: str
    full_name: str
    is_verified: bool
    timestamp: Optional[str]
    like_count: int
    comment_count: int
    location: Optional[str]
    image_count: int
    video_count: int

class AnalysisResults(BaseModel):
    """Detailed analysis results"""
    instagram_extraction: Dict[str, Any]
    ai_detection: Optional[Dict[str, Any]] = None
    deepfake: Optional[Dict[str, Any]] = None
    fact_check: Optional[Dict[str, Any]] = None
    source_credibility: Optional[Dict[str, Any]] = None
    ocr_text: Optional[str] = None

class ResultsResponse(BaseModel):
    """Response model for GET /results/{analysis_id}"""
    analysis_id: UUID
    post_id: str
    status: str
    progress: Optional[int] = Field(None, description="Progress percentage (0-100)")
    message: str
    trust_score: Optional[float] = Field(None, description="Overall trust score (0-100)")
    grade: Optional[str] = Field(None, description="Letter grade (A-F)")
    post_info: Optional[InstagramPostInfo] = None
    analysis_results: Optional[AnalysisResults] = None
    processing_time: Optional[int] = Field(None, description="Processing time in seconds")
    error: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {
                "analysis_id": "123e4567-e89b-12d3-a456-426614174000",
                "post_id": "ABC123xyz",
                "status": "completed",
                "progress": 100,
                "message": "Analysis completed successfully",
                "trust_score": 85.5,
                "grade": "B+",
                "post_info": {
                    "post_id": "ABC123xyz",
                    "url": "https://instagram.com/p/ABC123xyz/",
                    "type": "photo",
                    "caption": "Amazing sunset!",
                    "username": "example_user",
                    "full_name": "Example User",
                    "is_verified": False,
                    "timestamp": "2024-01-15T10:30:00",
                    "like_count": 1234,
                    "comment_count": 56,
                    "location": "New York, NY",
                    "image_count": 1,
                    "video_count": 0
                },
                "processing_time": 28,
                "created_at": "2024-01-15T10:30:00",
                "completed_at": "2024-01-15T10:30:28"
            }
        }

class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    detail: Optional[str] = None
    status_code: int

    class Config:
        json_schema_extra = {
            "example": {
                "error": "Invalid Instagram URL",
                "detail": "URL must contain /p/, /reel/, or /tv/",
                "status_code": 400
            }
        }

class AnalysisListResponse(BaseModel):
    """Response for listing analyses"""
    total: int
    analyses: List[ResultsResponse]
    page: int
    page_size: int
