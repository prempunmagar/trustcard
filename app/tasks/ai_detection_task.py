"""
AI Image Detection Celery Task

Separate task module for parallel processing.
"""

from celery import shared_task
import logging

from app.services.claude_ai_detection import claude_ai_detection

logger = logging.getLogger(__name__)


@shared_task(name="analysis.ai_detection", bind=True)
def run_ai_detection(self, image_urls: list) -> dict:
    """
    Run AI image detection on images using Claude Vision.

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

        logger.info(f"🤖 [AI-{task_id}] Starting Claude Vision AI detection on {len(image_urls)} images")

        # Use Claude Vision for AI detection
        results = claude_ai_detection.detect_multiple_images(image_urls)

        result = {
            "status": "completed",
            "overall": {
                "overall_ai_detected": results["overall_ai_detected"],
                "confidence": results["confidence"],
                "ai_images": results["ai_images"],
                "real_images": results["real_images"],
                "uncertain_images": results["uncertain_images"],
                "total_images": results["total_images"],
                "assessment": results["assessment"]
            },
            "individual_results": results["individual_results"],
            "model": "claude-3-5-sonnet-20241022"
        }

        logger.info(f"✅ [AI-{task_id}] Complete: {results['assessment']}")
        return result

    except Exception as e:
        logger.error(f"❌ [AI-{task_id}] Failed: {e}")
        return {
            "status": "failed",
            "error": str(e)
        }
