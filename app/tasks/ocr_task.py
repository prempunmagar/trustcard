"""
OCR Text Extraction Celery Task

Separate task module for parallel processing.
"""

from celery import shared_task
import logging

from app.services.ocr_service import ocr_service
from app.services.claude_vision_ocr import claude_vision_ocr

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
            # Try Claude Vision first (more accurate)
            ocr_results = []
            for idx, image_url in enumerate(image_urls, 1):
                logger.info(f"Running OCR on image {idx}/{len(image_urls)}")

                # Download image for Claude Vision (Instagram blocks direct URL access)
                import requests
                try:
                    response = requests.get(image_url, timeout=10)
                    response.raise_for_status()
                    image_bytes = response.content

                    # Determine media type from URL or headers
                    content_type = response.headers.get('content-type', 'image/jpeg')
                    media_type = content_type if content_type.startswith('image/') else 'image/jpeg'

                    # Try Claude Vision with image bytes
                    claude_text = claude_vision_ocr.extract_text_from_image_bytes(image_bytes, media_type)

                    if claude_text:
                        # Claude Vision succeeded
                        ocr_results.append({
                            "text": claude_text,
                            "raw_text": claude_text,
                            "word_count": len(claude_text.split()),
                            "confidence": 95.0,  # Claude Vision is highly accurate
                            "method": "claude_vision"
                        })
                        logger.info(f"✅ Claude Vision extracted {len(claude_text.split())} words from image {idx}")
                    else:
                        raise Exception("Claude Vision returned empty result")

                except Exception as e:
                    # Fallback to Tesseract
                    logger.warning(f"⚠️ Claude Vision failed for image {idx}: {e}, falling back to Tesseract")
                    tesseract_result = ocr_service.extract_from_url(image_url)
                    tesseract_result["method"] = "tesseract"
                    ocr_results.append(tesseract_result)

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
