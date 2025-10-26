"""
OCR Text Extraction Celery Task

Separate task module for parallel processing.
"""

from celery import shared_task
import logging

from app.services.ocr_service import ocr_service

logger = logging.getLogger(__name__)


@shared_task(name="analysis.ocr_extraction", bind=True)
def run_ocr_extraction(self, image_urls: list, caption: str) -> dict:
    """
    Run OCR text extraction on images.

    This task can run in parallel with other independent tasks.

    Args:
        image_urls: List of image URLs
        caption: Instagram caption

    Returns:
        dict: OCR results with combined text
    """
    task_id = self.request.id[:8]  # Short ID for logging

    try:
        logger.info(f"📝 [OCR-{task_id}] Starting OCR on {len(image_urls)} images")

        if image_urls:
            ocr_results = ocr_service.extract_from_multiple_images(image_urls)
            combined = ocr_service.combine_texts(ocr_results, caption)

            result = {
                "status": "completed",
                "individual_results": ocr_results,
                "combined": combined,
                "summary": {
                    "images_with_text": combined["images_with_text"],
                    "total_images": combined["total_images"],
                    "total_words_extracted": combined["total_words_ocr"],
                    "avg_confidence": combined["avg_confidence"],
                    "has_text": combined["has_extractable_text"]
                }
            }

            logger.info(f"✅ [OCR-{task_id}] Complete: {combined['total_words_ocr']} words from {combined['images_with_text']} images")
        else:
            # No images, just use caption
            result = {
                "status": "completed",
                "individual_results": [],
                "combined": {
                    "combined_text": caption,
                    "caption": caption,
                    "ocr_text": "",
                    "has_extractable_text": False,
                    "total_words_ocr": 0,
                    "images_with_text": 0,
                    "total_images": 0,
                    "avg_confidence": 0
                },
                "summary": {
                    "images_with_text": 0,
                    "total_images": 0,
                    "total_words_extracted": 0,
                    "avg_confidence": 0,
                    "has_text": bool(caption)
                }
            }

            logger.info(f"✅ [OCR-{task_id}] Complete: No images, using caption only")

        return result

    except Exception as e:
        logger.error(f"❌ [OCR-{task_id}] Failed: {e}")
        return {
            "status": "failed",
            "error": str(e)
        }
