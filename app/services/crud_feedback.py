"""
CRUD Operations for Community Feedback

Handles database operations for community voting and feedback.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from uuid import UUID
from typing import Optional, Dict, List
import hashlib

from app.models.community_feedback import CommunityFeedback, VoteType
from app.models.analysis import Analysis


class CRUDFeedback:
    """CRUD operations for community feedback"""

    @staticmethod
    def add_feedback(
        db: Session,
        analysis_id: UUID,
        vote_type: VoteType,
        comment: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> CommunityFeedback:
        """
        Add community feedback.

        Args:
            db: Database session
            analysis_id: Analysis ID
            vote_type: Vote type (accurate/misleading/false)
            comment: Optional comment
            ip_address: IP address (hashed for spam prevention)

        Returns:
            CommunityFeedback: Created feedback record
        """
        # Hash IP address if provided
        ip_hash = None
        if ip_address:
            ip_hash = hashlib.sha256(ip_address.encode()).hexdigest()

        feedback = CommunityFeedback(
            analysis_id=analysis_id,
            vote_type=vote_type,
            comment=comment,
            ip_hash=ip_hash
        )

        db.add(feedback)
        db.commit()
        db.refresh(feedback)

        return feedback

    @staticmethod
    def get_feedback_summary(db: Session, analysis_id: UUID) -> Dict:
        """
        Get aggregated feedback summary for an analysis.

        Args:
            db: Database session
            analysis_id: Analysis ID

        Returns:
            dict: Feedback summary with vote counts
        """
        # Count votes by type
        vote_counts = db.query(
            CommunityFeedback.vote_type,
            func.count(CommunityFeedback.id).label('count')
        ).filter(
            CommunityFeedback.analysis_id == analysis_id
        ).group_by(
            CommunityFeedback.vote_type
        ).all()

        # Build summary
        summary = {
            "total_votes": 0,
            "accurate": 0,
            "misleading": 0,
            "false": 0
        }

        for vote_type, count in vote_counts:
            summary["total_votes"] += count
            summary[vote_type.value] = count

        return summary

    @staticmethod
    def get_recent_comments(
        db: Session,
        analysis_id: UUID,
        limit: int = 10
    ) -> List[CommunityFeedback]:
        """
        Get recent comments for an analysis.

        Args:
            db: Database session
            analysis_id: Analysis ID
            limit: Maximum number of comments

        Returns:
            List[CommunityFeedback]: Recent comments
        """
        return db.query(CommunityFeedback).filter(
            CommunityFeedback.analysis_id == analysis_id,
            CommunityFeedback.comment.isnot(None),
            CommunityFeedback.comment != ''
        ).order_by(
            CommunityFeedback.created_at.desc()
        ).limit(limit).all()

    @staticmethod
    def check_duplicate_vote(
        db: Session,
        analysis_id: UUID,
        ip_address: str
    ) -> bool:
        """
        Check if IP has already voted on this analysis.

        Args:
            db: Database session
            analysis_id: Analysis ID
            ip_address: IP address

        Returns:
            bool: True if duplicate vote
        """
        ip_hash = hashlib.sha256(ip_address.encode()).hexdigest()

        existing = db.query(CommunityFeedback).filter(
            CommunityFeedback.analysis_id == analysis_id,
            CommunityFeedback.ip_hash == ip_hash
        ).first()

        return existing is not None


# Singleton instance
crud_feedback = CRUDFeedback()
