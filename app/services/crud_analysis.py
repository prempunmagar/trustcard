"""
CRUD operations for Analysis model
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from uuid import UUID

from app.models.analysis import Analysis

class CRUDAnalysis:
    """CRUD operations for analyses"""

    model = Analysis  # Add this for query building

    @staticmethod
    def get_by_id(db: Session, analysis_id: UUID) -> Optional[Analysis]:
        """Get analysis by ID"""
        return db.query(Analysis).filter(Analysis.id == analysis_id).first()

    @staticmethod
    def get_by_post_id(db: Session, post_id: str) -> Optional[Analysis]:
        """Get analysis by Instagram post ID"""
        return db.query(Analysis).filter(Analysis.post_id == post_id).first()

    @staticmethod
    def get_by_url(db: Session, instagram_url: str) -> Optional[Analysis]:
        """Get analysis by Instagram URL"""
        return db.query(Analysis).filter(Analysis.instagram_url == instagram_url).first()

    @staticmethod
    def get_by_url_cached(db: Session, instagram_url: str) -> Optional[Analysis]:
        """
        Get most recent analysis by URL with query optimization.
        Uses indexed column and orders by created_at for efficient lookup.
        """
        return db.query(Analysis).filter(
            Analysis.instagram_url == instagram_url
        ).order_by(
            Analysis.created_at.desc()
        ).first()

    @staticmethod
    def get_recent(db: Session, limit: int = 10) -> List[Analysis]:
        """
        Get recent completed analyses.
        Optimized query with indexed columns.
        """
        return db.query(Analysis).filter(
            Analysis.status == "completed"
        ).order_by(
            Analysis.created_at.desc()
        ).limit(limit).all()

    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[Analysis]:
        """Get all analyses with pagination"""
        return db.query(Analysis).offset(skip).limit(limit).all()

    @staticmethod
    def create(db: Session, instagram_url: str, post_id: str) -> Analysis:
        """Create new analysis record"""
        analysis = Analysis(
            instagram_url=instagram_url,
            post_id=post_id,
            status="pending"
        )
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        return analysis

    @staticmethod
    def update_results(
        db: Session,
        analysis_id: UUID,
        results: dict,
        trust_score: float,
        processing_time: int,
        content: dict = None
    ) -> Optional[Analysis]:
        """Update analysis with results"""
        analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
        if analysis:
            analysis.results = results
            analysis.trust_score = trust_score
            analysis.processing_time = processing_time
            analysis.status = "completed"
            if content:
                analysis.content = content
            db.commit()
            db.refresh(analysis)
        return analysis

    @staticmethod
    def update_status(
        db: Session,
        analysis_id: UUID,
        status: str,
        error_message: Optional[str] = None
    ) -> Optional[Analysis]:
        """Update analysis status"""
        analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
        if analysis:
            analysis.status = status
            if error_message:
                analysis.error_message = error_message
            db.commit()
            db.refresh(analysis)
        return analysis

    @staticmethod
    def delete(db: Session, analysis_id: UUID) -> bool:
        """Delete analysis"""
        analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
        if analysis:
            db.delete(analysis)
            db.commit()
            return True
        return False

# Create instance
crud_analysis = CRUDAnalysis()
