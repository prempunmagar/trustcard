"""
TrustCard Report Card Schema

Pydantic models for structured, reproducible report card generation.
"""

from typing import List, Optional, Dict, Literal
from pydantic import BaseModel, Field, field_validator
from datetime import datetime


class Evidence(BaseModel):
    """Individual piece of evidence supporting a conclusion"""
    source_module: str = Field(..., description="Which analysis module produced this")
    finding: str = Field(..., description="What was found")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in this finding")
    impact: Literal["positive", "negative", "neutral"] = Field(..., description="Impact on trust score")


class VerdictSection(BaseModel):
    """A section of the report card with verdict and evidence"""
    title: str = Field(..., description="Section title (e.g., 'AI Detection')")
    verdict: str = Field(..., description="Human-readable verdict")
    verdict_type: Literal["pass", "fail", "warning", "info", "pending"] = Field(
        ...,
        description="Visual type for rendering"
    )
    confidence: float = Field(..., ge=0.0, le=1.0, description="Overall confidence in verdict")
    evidence: List[Evidence] = Field(default_factory=list, description="Supporting evidence")
    reasoning: str = Field(..., description="Detailed explanation grounded in evidence")
    limitations: Optional[str] = Field(None, description="Known limitations or caveats")


class OverallAssessment(BaseModel):
    """Overall trust assessment"""
    trust_score: float = Field(..., ge=0.0, le=100.0, description="Final trust score")
    grade: str = Field(..., description="Letter grade (A-F)")
    verdict: str = Field(..., description="One-sentence overall verdict")
    verdict_type: Literal["pass", "fail", "warning", "info"] = Field(
        ...,
        description="Overall verdict type for visual rendering"
    )
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in assessment")
    key_concerns: List[str] = Field(default_factory=list, description="Top 3 concerns")
    key_strengths: List[str] = Field(default_factory=list, description="Top 3 strengths")


class ImpactExplanation(BaseModel):
    """Explains what the findings mean to non-technical users"""
    why_it_matters: str = Field(..., description="Plain-language explanation of impact")
    recommended_action: Optional[str] = Field(None, description="What users should do")
    context: Optional[str] = Field(None, description="Additional context for interpretation")


class TrustCard(BaseModel):
    """Complete TrustCard Report Card"""

    # Metadata
    card_version: str = Field(default="1.0.0", description="Schema version for evolution")
    generated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="Generation timestamp ISO format")
    analysis_id: str = Field(..., description="ID of underlying analysis")
    post_id: str = Field(..., description="Instagram post ID")

    # Overall Assessment
    overall: OverallAssessment = Field(..., description="Top-level verdict and score")

    # Detailed Sections
    sections: List[VerdictSection] = Field(..., description="Individual analysis sections")

    # Impact Explanation
    impact: ImpactExplanation = Field(..., description="What this means to users")

    # Footer Notes
    methodology_note: str = Field(
        default="This analysis was generated using AI-powered fact-checking, image analysis, and source verification. Results should be used as guidance, not absolute truth.",
        description="Standard disclaimer"
    )

    # Raw Data Reference
    raw_findings_hash: Optional[str] = Field(None, description="Hash of input findings for traceability")

    @field_validator('overall')
    def validate_overall_consistency(cls, v):
        """Ensure overall assessment is consistent"""
        if v.trust_score >= 80 and v.grade not in ['A', 'A+', 'A-', 'B+']:
            raise ValueError(f"Grade {v.grade} inconsistent with score {v.trust_score}")
        if v.trust_score < 60 and v.grade not in ['D', 'D+', 'D-', 'F']:
            raise ValueError(f"Grade {v.grade} inconsistent with score {v.trust_score}")
        return v

    @field_validator('sections')
    def validate_sections_not_empty(cls, v):
        """Ensure at least one section exists"""
        if not v:
            raise ValueError("Card must have at least one section")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "card_version": "1.0.0",
                "analysis_id": "abc123",
                "post_id": "DQAMs6PiJNa",
                "overall": {
                    "trust_score": 90.0,
                    "grade": "A",
                    "verdict": "Highly credible post with authentic imagery",
                    "verdict_type": "pass",
                    "confidence": 0.95,
                    "key_concerns": [],
                    "key_strengths": ["Real photograph verified", "No misleading claims"]
                },
                "sections": [
                    {
                        "title": "Image Authenticity",
                        "verdict": "Real photograph - not AI-generated",
                        "verdict_type": "pass",
                        "confidence": 0.95,
                        "evidence": [
                            {
                                "source_module": "claude_ai_detection",
                                "finding": "Natural lighting and realistic textures detected",
                                "confidence": 0.95,
                                "impact": "positive"
                            }
                        ],
                        "reasoning": "Claude Vision analysis found no AI generation artifacts...",
                        "limitations": "Analysis based on visual inspection only"
                    }
                ],
                "impact": {
                    "why_it_matters": "This appears to be authentic documentary content",
                    "recommended_action": "Safe to share with appropriate context"
                }
            }
        }


class CardGenerationRequest(BaseModel):
    """Request for card generation"""
    normalized_findings: Dict = Field(..., description="Normalized findings from pipeline")
    post_info: Dict = Field(..., description="Instagram post metadata")
    trust_score: float = Field(..., ge=0.0, le=100.0, description="Calculated trust score")
    grade: str = Field(..., description="Letter grade")
