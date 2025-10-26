"""
Fact-Checking Celery Task

Separate task module that depends on OCR results.
"""

from celery import shared_task
import logging

from app.services.claude_claim_extractor import claude_claim_extractor
from app.services.fact_checking_service import fact_checking_service

logger = logging.getLogger(__name__)


@shared_task(name="analysis.fact_checking", bind=True)
def run_fact_checking(self, combined_text: str) -> dict:
    """
    Run fact-checking on extracted text using Claude AI.

    This task depends on OCR results and runs sequentially after OCR.

    Args:
        combined_text: Combined text from caption and OCR

    Returns:
        dict: Fact-checking results
    """
    task_id = self.request.id[:8]  # Short ID for logging

    try:
        logger.info(f"🔍 [FactCheck-{task_id}] Starting Claude-powered fact-checking analysis")

        if not combined_text or len(combined_text.strip()) < 10:
            logger.info(f"🔍 [FactCheck-{task_id}] Skipped - insufficient text")
            return {
                "status": "skipped",
                "reason": "Insufficient text for analysis"
            }

        # Extract claims using Claude
        claim_data = claude_claim_extractor.extract_claims(combined_text)

        if claim_data.get("error"):
            logger.warning(f"⚠️ [FactCheck-{task_id}] Claude extraction had error, may have limited results")

        # Analyze credibility using Claude's assessment
        if claim_data.get("summary"):
            # Use Claude's summary for risk assessment
            claude_summary = claim_data["summary"]
            risk_level = claude_summary.get("risk_level", "low")
            credibility_score = {
                "score": (1 - (claude_summary.get("red_flag_count", 0) * 5)) * 100,
                "interpretation": claude_summary.get("overall_assessment", "No assessment available"),
                "penalties": [],
                "bonuses": []
            }
        else:
            # Fallback to analyzing claims directly
            credibility_score = claude_claim_extractor.analyze_credibility(claim_data.get("claims", []))
            risk_level = "medium" if credibility_score["score"] < 60 else "low"

        # Determine if manual review is needed
        requires_manual_review = (
            risk_level == "high" or
            credibility_score["score"] < 50 or
            claim_data.get("total_claims", 0) > 5
        )

        result = {
            "status": "completed",
            "claim_extraction": {
                "total_claims": claim_data.get("total_claims", 0),
                "claim_types": claim_data.get("claim_types", {}),
                "has_claims": claim_data.get("has_claims", False),
                "sentiment": {"polarity": 0.0, "subjectivity": 0.5}  # Placeholder
            },
            "credibility_analysis": credibility_score,
            "flags": [],
            "risk_level": risk_level,
            "requires_manual_review": requires_manual_review,
            "summary": claim_data.get("summary", {}).get("overall_assessment", f"Analyzed {claim_data.get('total_claims', 0)} claims"),
            "analyzed_claims": claim_data.get("claims", [])[:10],  # Limit to 10 claims
            "method": "claude"
        }

        logger.info(f"✅ [FactCheck-{task_id}] Complete: {claim_data.get('total_claims', 0)} claims, credibility {credibility_score['score']:.1f}/100")
        return result

    except Exception as e:
        logger.error(f"❌ [FactCheck-{task_id}] Failed: {e}")
        return {
            "status": "failed",
            "error": str(e)
        }
