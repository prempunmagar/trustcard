"""
API Endpoints for Reports and Community Feedback

Handles HTML report generation and community voting.
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, field_validator
from uuid import UUID
from typing import Optional

from app.config import settings
from app.database import get_db
from app.services.crud_analysis import crud_analysis
from app.services.crud_feedback import crud_feedback
from app.services.report_generator import report_generator
from app.models.community_feedback import VoteType

router = APIRouter(prefix="/api/reports", tags=["reports"])


class FeedbackSubmission(BaseModel):
    """Community feedback submission schema"""
    vote_type: str = Field(
        ...,
        description="Vote type: 'accurate', 'misleading', or 'false'",
        examples=["accurate"]
    )
    comment: Optional[str] = Field(
        None,
        max_length=settings.MAX_COMMENT_LENGTH,
        description=f"Optional comment (max {settings.MAX_COMMENT_LENGTH} characters)",
        examples=["Great analysis, very thorough!"]
    )

    @field_validator('vote_type')
    @classmethod
    def validate_vote_type(cls, v):
        """Validate vote type is one of the allowed values"""
        allowed_votes = ['accurate', 'misleading', 'false']
        v_lower = v.lower()
        if v_lower not in allowed_votes:
            raise ValueError(f"vote_type must be one of: {', '.join(allowed_votes)}")
        return v_lower

    @field_validator('comment')
    @classmethod
    def validate_comment(cls, v):
        """Validate comment length and sanitize"""
        if v is None:
            return v

        # Strip whitespace
        v = v.strip()

        # Check length
        if len(v) > settings.MAX_COMMENT_LENGTH:
            raise ValueError(f"Comment too long (max {settings.MAX_COMMENT_LENGTH} characters)")

        # Check if empty after stripping
        if len(v) == 0:
            return None

        return v


class FeedbackResponse(BaseModel):
    """Feedback submission response schema"""
    message: str
    feedback_id: UUID
    summary: dict


@router.get("/{analysis_id}", response_class=HTMLResponse)
async def get_report_html(
    analysis_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get HTML report card for an analysis.

    Returns a beautiful, shareable HTML report that can be:
    - Viewed in browser
    - Shared via link
    - Saved as PDF (print to PDF)

    Args:
        analysis_id: UUID of the analysis

    Returns:
        HTMLResponse: HTML report card
    """
    # Get analysis
    analysis = crud_analysis.get_by_id(db, analysis_id)

    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    if analysis.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Analysis not yet completed (status: {analysis.status})"
        )

    # Get community feedback summary
    feedback_summary = crud_feedback.get_feedback_summary(db, analysis_id)

    # Extract data
    post_info = analysis.content or {}
    results = analysis.results or {}

    # Get score data from breakdown if available
    score_data = results.get("trust_score_breakdown", {})
    if not score_data:
        # Fallback for older analyses
        score_data = {
            "final_score": float(analysis.trust_score or 0),
            "score": float(analysis.trust_score or 0),
            "grade": "N/A",
            "grade_info": {
                "description": "No detailed assessment available"
            }
        }

    # Generate HTML report
    html = report_generator.generate_html_report(
        analysis_id=str(analysis_id),
        post_info=post_info,
        score_data=score_data,
        results=results,
        community_feedback=feedback_summary
    )

    return HTMLResponse(content=html)


@router.post("/{analysis_id}/feedback", response_model=FeedbackResponse)
async def submit_feedback(
    analysis_id: UUID,
    feedback: FeedbackSubmission,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Submit community feedback on an analysis.

    Users can vote:
    - **accurate** - Content is accurate and truthful
    - **misleading** - Content is misleading or lacks context
    - **false** - Content contains false information

    Optional comment can be provided for explanation.

    **Anonymous voting**: No login required, but duplicate votes from the same IP are prevented.

    Args:
        analysis_id: UUID of the analysis
        feedback: Feedback submission with vote type and optional comment
        request: FastAPI request (for IP address)

    Returns:
        FeedbackResponse: Confirmation with updated vote summary
    """
    # Verify analysis exists
    analysis = crud_analysis.get_by_id(db, analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    # Get IP address
    ip_address = request.client.host

    # Check for duplicate vote
    if crud_feedback.check_duplicate_vote(db, analysis_id, ip_address):
        raise HTTPException(
            status_code=400,
            detail="You have already voted on this analysis"
        )

    # Validate vote type
    try:
        vote_type = VoteType(feedback.vote_type.lower())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid vote_type. Must be 'accurate', 'misleading', or 'false'"
        )

    # Add feedback
    feedback_record = crud_feedback.add_feedback(
        db=db,
        analysis_id=analysis_id,
        vote_type=vote_type,
        comment=feedback.comment,
        ip_address=ip_address
    )

    # Get updated summary
    summary = crud_feedback.get_feedback_summary(db, analysis_id)

    return {
        "message": "Thank you for your feedback!",
        "feedback_id": feedback_record.id,
        "summary": summary
    }


@router.get("/{analysis_id}/feedback")
async def get_feedback_summary(
    analysis_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get community feedback summary for an analysis.

    Returns aggregated vote counts and recent comments.

    Args:
        analysis_id: UUID of the analysis

    Returns:
        dict: Feedback summary with vote counts and recent comments
    """
    # Verify analysis exists
    analysis = crud_analysis.get_by_id(db, analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    # Get summary
    summary = crud_feedback.get_feedback_summary(db, analysis_id)

    # Get recent comments
    comments = crud_feedback.get_recent_comments(db, analysis_id, limit=10)

    comment_list = []
    for comment in comments:
        if comment.comment:
            comment_list.append({
                "vote_type": comment.vote_type.value,
                "comment": comment.comment,
                "created_at": comment.created_at.isoformat()
            })

    return {
        "analysis_id": str(analysis_id),
        "summary": summary,
        "recent_comments": comment_list
    }
