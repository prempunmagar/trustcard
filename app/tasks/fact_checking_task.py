"""
Fact-Checking Celery Task

Separate task module that depends on OCR results.
"""

from celery import shared_task
import logging

from app.services.claim_extractor import claim_extractor
from app.services.fact_checking_service import fact_checking_service

logger = logging.getLogger(__name__)


@shared_task(name="analysis.fact_checking", bind=True)
def run_fact_checking(self, combined_text: str) -> dict:
    """
    Run fact-checking on extracted text.

    This task depends on OCR results and runs sequentially after OCR.

    Args:
        combined_text: Combined text from caption and OCR

    Returns:
        dict: Fact-checking results
    """
    task_id = self.request.id[:8]  # Short ID for logging

    try:
        logger.info(f"🔍 [FactCheck-{task_id}] Starting fact-checking analysis")

        if not combined_text or len(combined_text.strip()) < 10:
            logger.info(f"🔍 [FactCheck-{task_id}] Skipped - insufficient text")
            return {
                "status": "skipped",
                "reason": "Insufficient text for analysis"
            }

        # Extract claims
        claim_extractor.initialize()
        claim_data = claim_extractor.extract_claims(combined_text)

        # Analyze credibility
        fact_check_analysis = fact_checking_service.analyze_claims(claim_data, combined_text)

        result = {
            "status": "completed",
            "claim_extraction": {
                "total_claims": claim_data["total_claims"],
                "claim_types": claim_data["claim_types"],
                "has_claims": claim_data["has_claims"],
                "sentiment": claim_data["sentiment"]
            },
            "credibility_analysis": {
                "score": fact_check_analysis["credibility_score"]["score"],
                "interpretation": fact_check_analysis["credibility_score"]["interpretation"],
                "penalties": fact_check_analysis["credibility_score"]["penalties"],
                "bonuses": fact_check_analysis["credibility_score"]["bonuses"]
            },
            "flags": fact_check_analysis["flags"],
            "risk_level": fact_check_analysis["risk_level"],
            "requires_manual_review": fact_check_analysis["requires_manual_review"],
            "summary": fact_check_analysis["summary"],
            "analyzed_claims": fact_check_analysis["analyzed_claims"]
        }

        logger.info(f"✅ [FactCheck-{task_id}] Complete: {claim_data['total_claims']} claims, credibility {fact_check_analysis['credibility_score']['score']}/100")
        return result

    except Exception as e:
        logger.error(f"❌ [FactCheck-{task_id}] Failed: {e}")
        return {
            "status": "failed",
            "error": str(e)
        }
