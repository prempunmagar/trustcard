"""
Community Feedback model - stores anonymous user feedback
"""
from sqlalchemy import Column, String, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import enum

from app.models.base import Base, TimestampMixin

class VoteType(enum.Enum):
    """Enum for feedback vote types"""
    ACCURATE = "accurate"
    MISLEADING = "misleading"
    FALSE = "false"

class CommunityFeedback(Base, TimestampMixin):
    """Stores anonymous community feedback on analyses"""
    __tablename__ = "community_feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_id = Column(UUID(as_uuid=True), ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False, index=True)

    # Vote type
    vote_type = Column(SQLEnum(VoteType), nullable=False)

    # Optional anonymous comment
    comment = Column(Text, nullable=True)

    # IP hash for spam prevention (optional, not user-identifiable)
    ip_hash = Column(String(64), nullable=True, index=True)

    # Relationships
    analysis = relationship("Analysis", back_populates="feedback")

    def __repr__(self):
        return f"<CommunityFeedback(id={self.id}, vote_type={self.vote_type.value})>"
