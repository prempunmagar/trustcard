"""
AI Image Detection Celery Task

Separate task module for parallel processing.
"""

from celery import shared_task
import logging

from app.services.ai_detection_service import ai_detection_service

logger = logging.getLogger(__name__)


@shared_task(name="analysis.ai_detection", bind=True)
def run_ai_detection(self, image_urls: list) -> dict:
    """
    Run AI image detection on images.

    This task can run in parallel with other independent tasks.

    Args:
        image_urls: List of image URLs to analyze

    Returns:
        dict: AI detection results
    """
    task_id = self.request.id[:8]  # Short ID for logging

    try:
        if not image_urls:
            logger.info(f"🤖 [AI-{task_id}] Skipped - no images")
            return {
                "status": "skipped",
                "reason": "No images in post"
            }

        logger.info(f"🤖 [AI-{task_id}] Starting AI detection on {len(image_urls)} images")

        # Initialize and run
        ai_detection_service.initialize()
        ai_results = ai_detection_service.detect_multiple_images(image_urls)
        overall = ai_detection_service.get_overall_assessment(ai_results)

        result = {
            "status": "completed",
            "overall": overall,
            "individual_results": ai_results,
            "model": "umm-maybe/AI-image-detector"
        }

        logger.info(f"✅ [AI-{task_id}] Complete: {overall['assessment']}")
        return result

    except Exception as e:
        logger.error(f"❌ [AI-{task_id}] Failed: {e}")
        return {
            "status": "failed",
            "error": str(e)
        }
