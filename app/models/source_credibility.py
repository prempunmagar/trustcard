"""
Source Credibility model - stores publisher reliability ratings
"""
from sqlalchemy import Column, String, Text, DateTime
from datetime import datetime

from app.models.base import Base

class SourceCredibility(Base):
    """Stores credibility ratings for news sources and publishers"""
    __tablename__ = "source_credibility"

    domain = Column(String(255), primary_key=True)
    bias_rating = Column(String(50), nullable=True)  # left, center, right, etc.
    reliability_rating = Column(String(50), nullable=True)  # high, medium, low
    description = Column(Text, nullable=True)
    last_updated = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<SourceCredibility(domain={self.domain}, reliability={self.reliability_rating})>"
