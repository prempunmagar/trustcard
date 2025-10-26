"""
Helper functions for building API responses
"""
from typing import Optional, Dict, Any
from uuid import UUID

from app.models.analysis import Analysis

def calculate_grade(trust_score: float) -> str:
    """
    Convert trust score (0-100) to letter grade

    Args:
        trust_score: Score from 0-100

    Returns:
        str: Letter grade (A+ to F)
    """
    if trust_score >= 97:
        return "A+"
    elif trust_score >= 93:
        return "A"
    elif trust_score >= 90:
        return "A-"
    elif trust_score >= 87:
        return "B+"
    elif trust_score >= 83:
        return "B"
    elif trust_score >= 80:
        return "B-"
    elif trust_score >= 77:
        return "C+"
    elif trust_score >= 73:
        return "C"
    elif trust_score >= 70:
        return "C-"
    elif trust_score >= 67:
        return "D+"
    elif trust_score >= 63:
        return "D"
    elif trust_score >= 60:
        return "D-"
    else:
        return "F"

def get_status_message(status: str, progress: Optional[int] = None) -> str:
    """
    Get user-friendly status message

    Args:
        status: Analysis status
        progress: Optional progress percentage

    Returns:
        str: Human-readable message
    """
    messages = {
        "pending": "Analysis queued and waiting to start",
        "processing": "Analysis in progress",
        "completed": "Analysis completed successfully",
        "failed": "Analysis failed - see error details"
    }

    if status == "processing" and progress:
        if progress < 20:
            return "Extracting Instagram content..."
        elif progress < 40:
            return "Running AI detection..."
        elif progress < 60:
            return "Checking for deepfakes..."
        elif progress < 80:
            return "Fact-checking claims..."
        else:
            return "Calculating trust score..."

    return messages.get(status, "Unknown status")

def build_post_info_response(content: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build InstagramPostInfo from stored content

    Args:
        content: Stored Instagram content from database

    Returns:
        dict: Formatted post info
    """
    if not content:
        return None

    user = content.get("user", {})

    return {
        "post_id": content.get("post_id"),
        "url": content.get("url"),
        "type": content.get("type"),
        "caption": content.get("caption", ""),
        "username": user.get("username", "unknown"),
        "full_name": user.get("full_name", ""),
        "is_verified": user.get("is_verified", False),
        "timestamp": content.get("timestamp"),
        "like_count": content.get("like_count", 0),
        "comment_count": content.get("comment_count", 0),
        "location": content.get("location"),
        "image_count": len(content.get("images", [])),
        "video_count": len(content.get("videos", []))
    }

def calculate_progress(status: str, results: Optional[Dict[str, Any]] = None) -> int:
    """
    Calculate progress percentage based on status and results

    Args:
        status: Analysis status
        results: Analysis results

    Returns:
        int: Progress percentage (0-100)
    """
    if status == "completed":
        return 100
    elif status == "failed":
        return 0
    elif status == "pending":
        return 0
    elif status == "processing":
        # Estimate based on what's completed
        if not results:
            return 10

        progress = 10  # Started

        if results.get("instagram_extraction", {}).get("status") == "success":
            progress = 20

        if results.get("ai_detection", {}).get("status") not in [None, "pending_ml_integration"]:
            progress = 40

        if results.get("deepfake", {}).get("status") not in [None, "pending_ml_integration"]:
            progress = 60

        if results.get("fact_check", {}).get("status") not in [None, "pending_ml_integration"]:
            progress = 80

        return progress

    return 0
