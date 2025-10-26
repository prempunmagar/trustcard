"""
API endpoints for Instagram content extraction
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl
from typing import Optional, Dict

from app.services.instagram_service import instagram_service

router = APIRouter(prefix="/instagram", tags=["instagram"])

class InstagramURLRequest(BaseModel):
    url: HttpUrl

class InstagramPostResponse(BaseModel):
    post_id: str
    url: str
    type: str
    caption: str
    images: list
    videos: list
    user: dict
    timestamp: Optional[str]
    like_count: int
    comment_count: int
    location: Optional[str]

@router.post("/auth")
async def authenticate_instagram():
    """
    Authenticate with Instagram
    Uses credentials from environment variables
    """
    success = instagram_service.authenticate()

    if success:
        return {
            "status": "authenticated",
            "message": "Successfully authenticated with Instagram"
        }
    else:
        raise HTTPException(
            status_code=401,
            detail="Instagram authentication failed. Check credentials in .env file"
        )

@router.post("/extract")
async def extract_instagram_post(request: InstagramURLRequest):
    """
    Extract information from Instagram post URL

    This endpoint extracts:
    - Post metadata (caption, timestamp, counts)
    - Media URLs (images, videos)
    - User information

    Note: Requires Instagram authentication first (call /instagram/auth)
    """
    # Ensure authenticated
    if not instagram_service._authenticated:
        # Try to authenticate automatically
        success = instagram_service.authenticate()
        if not success:
            raise HTTPException(
                status_code=401,
                detail="Not authenticated with Instagram. Please call /instagram/auth first."
            )

    # Extract post info
    post_info = instagram_service.get_post_info(str(request.url))

    if post_info is None:
        raise HTTPException(
            status_code=500,
            detail="Failed to extract post information"
        )

    if "error" in post_info:
        raise HTTPException(
            status_code=400,
            detail=post_info["error"]
        )

    return post_info

@router.get("/test")
async def test_instagram_connection():
    """Test if Instagram service is authenticated and working"""
    if instagram_service._authenticated:
        return {
            "status": "authenticated",
            "message": "Instagram service is ready"
        }
    else:
        return {
            "status": "not_authenticated",
            "message": "Instagram service not authenticated. Call /instagram/auth to authenticate."
        }
