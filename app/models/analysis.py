"""
Analysis model - stores Instagram post analysis results
"""
from sqlalchemy import Column, String, Integer, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

from app.models.base import Base, TimestampMixin

class Analysis(Base, TimestampMixin):
    """Stores analysis results for Instagram posts"""
    __tablename__ = "analyses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    instagram_url = Column(String(500), nullable=False, index=True)
    post_id = Column(String(100), unique=True, nullable=False, index=True)

    # Raw Instagram data (flexible JSONB storage)
    content = Column(JSONB, nullable=True)

    # Analysis results from all detection models
    results = Column(JSONB, nullable=True)

    # Final trust score (0-100)
    trust_score = Column(Numeric(5, 2), nullable=True)

    # Processing time in seconds
    processing_time = Column(Integer, nullable=True)

    # Status tracking
    status = Column(String(50), default="pending", nullable=False)  # pending, processing, completed, failed
    error_message = Column(Text, nullable=True)

    # Relationships
    feedback = relationship("CommunityFeedback", back_populates="analysis", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Analysis(id={self.id}, post_id={self.post_id}, trust_score={self.trust_score})>"
