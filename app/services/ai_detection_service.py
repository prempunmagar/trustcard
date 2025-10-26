"""
AI-generated image detection service
Uses Hugging Face transformers for AI image detection
"""
from transformers import pipeline
from PIL import Image
import torch
import requests
from io import BytesIO
import logging
from typing import Dict, Optional, List
import time

logger = logging.getLogger(__name__)

class AIDetectionService:
    """Service for detecting AI-generated images"""

    def __init__(self):
        self.model = None
        self.device = None
        self._initialized = False

    def initialize(self):
        """
        Initialize the AI detection model
        Lazy loading - only load when first needed
        """
        if self._initialized:
            return

        logger.info("🤖 Initializing AI Image Detection model...")
        start_time = time.time()

        try:
            # Detect if GPU is available
            if torch.cuda.is_available():
                self.device = 0  # GPU
                logger.info("✅ GPU detected - using CUDA acceleration")
            else:
                self.device = -1  # CPU
                logger.info("ℹ️  No GPU detected - using CPU (slower)")

            # Load model from Hugging Face
            # Model: umm-maybe/AI-image-detector
            self.model = pipeline(
                "image-classification",
                model="umm-maybe/AI-image-detector",
                device=self.device
            )

            load_time = time.time() - start_time
            logger.info(f"✅ AI Detection model loaded in {load_time:.2f}s")
            self._initialized = True

        except Exception as e:
            logger.error(f"❌ Failed to load AI detection model: {e}")
            raise

    def download_image(self, url: str, timeout: int = 30) -> Optional[Image.Image]:
        """
        Download image from URL

        Args:
            url: Image URL
            timeout: Request timeout in seconds

        Returns:
            PIL Image or None if failed
        """
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()

            # Open image with PIL
            image = Image.open(BytesIO(response.content))

            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')

            logger.info(f"✅ Downloaded image: {image.size}")
            return image

        except Exception as e:
            logger.error(f"❌ Failed to download image from {url}: {e}")
            return None

    def detect_ai_image(self, image: Image.Image) -> Dict:
        """
        Detect if image is AI-generated

        Args:
            image: PIL Image object

        Returns:
            dict: Detection results with confidence scores
        """
        if not self._initialized:
            self.initialize()

        try:
            start_time = time.time()

            # Run inference
            results = self.model(image)

            inference_time = time.time() - start_time
            logger.info(f"⚡ AI detection inference completed in {inference_time:.2f}s")

            # Parse results
            # Results format: [{'label': 'artificial', 'score': 0.95}, {'label': 'real', 'score': 0.05}]
            ai_score = 0.0
            real_score = 0.0

            for result in results:
                label = result['label'].lower()
                score = result['score']

                if 'artificial' in label or 'fake' in label or 'ai' in label:
                    ai_score = score
                elif 'real' in label or 'human' in label:
                    real_score = score

            # Determine if AI-generated (threshold: 0.5)
            is_ai_generated = ai_score > 0.5
            confidence = max(ai_score, real_score)

            return {
                "is_ai_generated": is_ai_generated,
                "confidence": float(confidence),
                "ai_score": float(ai_score),
                "real_score": float(real_score),
                "inference_time": round(inference_time, 2),
                "model": "umm-maybe/AI-image-detector",
                "device": "GPU" if self.device == 0 else "CPU"
            }

        except Exception as e:
            logger.error(f"❌ AI detection failed: {e}")
            return {
                "is_ai_generated": None,
                "confidence": 0.0,
                "error": str(e),
                "model": "umm-maybe/AI-image-detector"
            }

    def detect_from_url(self, image_url: str) -> Dict:
        """
        Detect AI-generated image from URL

        Args:
            image_url: URL of image to analyze

        Returns:
            dict: Detection results
        """
        # Download image
        image = self.download_image(image_url)

        if image is None:
            return {
                "is_ai_generated": None,
                "confidence": 0.0,
                "error": "Failed to download image",
                "image_url": image_url
            }

        # Detect AI
        result = self.detect_ai_image(image)
        result["image_url"] = image_url
        result["image_size"] = f"{image.size[0]}x{image.size[1]}"

        return result

    def detect_multiple_images(self, image_urls: List[str]) -> List[Dict]:
        """
        Detect AI-generated images from multiple URLs

        Args:
            image_urls: List of image URLs

        Returns:
            list: Detection results for each image
        """
        results = []

        for idx, url in enumerate(image_urls, 1):
            logger.info(f"Processing image {idx}/{len(image_urls)}: {url}")
            result = self.detect_from_url(url)
            results.append(result)

        return results

    def get_overall_assessment(self, results: List[Dict]) -> Dict:
        """
        Get overall AI detection assessment from multiple image results

        Args:
            results: List of detection results

        Returns:
            dict: Overall assessment
        """
        if not results:
            return {
                "overall_ai_detected": False,
                "confidence": 0.0,
                "total_images": 0,
                "ai_images": 0,
                "real_images": 0
            }

        ai_count = sum(1 for r in results if r.get("is_ai_generated") == True)
        real_count = sum(1 for r in results if r.get("is_ai_generated") == False)
        uncertain_count = len(results) - ai_count - real_count

        # Calculate average confidence
        confidences = [r.get("confidence", 0.0) for r in results if r.get("confidence")]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        # Overall assessment: if ANY image is AI-generated with high confidence
        overall_ai_detected = ai_count > 0

        return {
            "overall_ai_detected": overall_ai_detected,
            "confidence": round(avg_confidence, 2),
            "total_images": len(results),
            "ai_images": ai_count,
            "real_images": real_count,
            "uncertain_images": uncertain_count,
            "assessment": self._get_assessment_message(ai_count, real_count, len(results))
        }

    def _get_assessment_message(self, ai_count: int, real_count: int, total: int) -> str:
        """Generate human-readable assessment message"""
        if ai_count == 0:
            return "All images appear to be authentic photographs"
        elif ai_count == total:
            return "All images appear to be AI-generated"
        elif ai_count == 1:
            return f"1 out of {total} images appears to be AI-generated"
        else:
            return f"{ai_count} out of {total} images appear to be AI-generated"

# Singleton instance
ai_detection_service = AIDetectionService()
