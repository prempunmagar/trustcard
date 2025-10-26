"""
Source Credibility Evaluation Celery Task

Separate task module that depends on text extraction.
"""

from celery import shared_task
import logging

from app.services.source_evaluation_service import source_evaluation_service
from app.utils.url_extractor import extract_urls

logger = logging.getLogger(__name__)


@shared_task(name="analysis.source_evaluation", bind=True)
def run_source_evaluation(self, combined_text: str, instagram_user: dict) -> dict:
    """
    Run source credibility evaluation.

    This task depends on text extraction and runs sequentially.

    Args:
        combined_text: Combined text from caption and OCR
        instagram_user: Instagram user info

    Returns:
        dict: Source credibility results
    """
    task_id = self.request.id[:8]  # Short ID for logging

    try:
        logger.info(f"📰 [Source-{task_id}] Starting source evaluation")

        # Extract URLs
        external_urls = extract_urls(combined_text) if combined_text else []

        # Evaluate sources
        source_assessment = source_evaluation_service.get_overall_source_assessment(
            external_urls,
            instagram_user
        )

        result = {
            "status": "completed",
            "assessment": source_assessment
        }

        logger.info(f"✅ [Source-{task_id}] Complete: {len(external_urls)} URLs analyzed")
        logger.info(f"   {source_assessment['overall_assessment']}")

        return result

    except Exception as e:
        logger.error(f"❌ [Source-{task_id}] Failed: {e}")
        return {
            "status": "failed",
            "error": str(e)
        }
