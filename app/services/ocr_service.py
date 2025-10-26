"""
OCR (Optical Character Recognition) service
Uses Tesseract to extract text from images
"""
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import cv2
import numpy as np
import requests
from io import BytesIO
import logging
from typing import Dict, List, Optional
import re

logger = logging.getLogger(__name__)

class OCRService:
    """Service for extracting text from images"""

    def __init__(self):
        # Verify Tesseract is installed
        try:
            version = pytesseract.get_tesseract_version()
            logger.info(f"✅ Tesseract OCR version: {version}")
        except Exception as e:
            logger.error(f"❌ Tesseract not found: {e}")
            logger.error("Please install Tesseract OCR")

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

            image = Image.open(BytesIO(response.content))

            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')

            logger.info(f"✅ Downloaded image for OCR: {image.size}")
            return image

        except Exception as e:
            logger.error(f"❌ Failed to download image: {e}")
            return None

    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Preprocess image for better OCR accuracy

        Args:
            image: PIL Image

        Returns:
            Preprocessed PIL Image
        """
        try:
            # Convert PIL to OpenCV format
            img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

            # Convert to grayscale
            gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)

            # Apply thresholding to get binary image
            # Adaptive thresholding works better for varying lighting
            binary = cv2.adaptiveThreshold(
                gray,
                255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY,
                11,
                2
            )

            # Denoise
            denoised = cv2.fastNlMeansDenoising(binary, h=10)

            # Convert back to PIL
            processed = Image.fromarray(denoised)

            # Increase contrast
            enhancer = ImageEnhance.Contrast(processed)
            processed = enhancer.enhance(2.0)

            # Sharpen
            processed = processed.filter(ImageFilter.SHARPEN)

            logger.info("✅ Image preprocessed for OCR")
            return processed

        except Exception as e:
            logger.error(f"❌ Preprocessing failed: {e}")
            return image  # Return original if preprocessing fails

    def extract_text(self, image: Image.Image, preprocess: bool = True, lang: str = 'eng') -> Dict:
        """
        Extract text from image using OCR

        Args:
            image: PIL Image object
            preprocess: Whether to preprocess image
            lang: Language(s) to use (e.g., 'eng', 'eng+spa')

        Returns:
            dict: Extracted text and metadata
        """
        try:
            # Preprocess if requested
            if preprocess:
                processed_image = self.preprocess_image(image)
            else:
                processed_image = image

            # Configure Tesseract
            custom_config = r'--oem 3 --psm 6'
            # OEM 3: Default OCR Engine Mode
            # PSM 6: Assume uniform block of text

            # Extract text with confidence data
            data = pytesseract.image_to_data(
                processed_image,
                lang=lang,
                config=custom_config,
                output_type=pytesseract.Output.DICT
            )

            # Extract text
            text = pytesseract.image_to_string(
                processed_image,
                lang=lang,
                config=custom_config
            )

            # Calculate average confidence
            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0

            # Count words
            words = [word for word in data['text'] if word.strip()]
            word_count = len(words)

            # Clean extracted text
            cleaned_text = self._clean_text(text)

            result = {
                "text": cleaned_text,
                "raw_text": text,
                "word_count": word_count,
                "confidence": round(avg_confidence, 2),
                "language": lang,
                "has_text": len(cleaned_text.strip()) > 0
            }

            logger.info(f"✅ OCR extracted {word_count} words (confidence: {avg_confidence:.1f}%)")
            return result

        except Exception as e:
            logger.error(f"❌ OCR extraction failed: {e}")
            return {
                "text": "",
                "raw_text": "",
                "word_count": 0,
                "confidence": 0.0,
                "error": str(e),
                "has_text": False
            }

    def extract_from_url(self, image_url: str, preprocess: bool = True, lang: str = 'eng') -> Dict:
        """
        Extract text from image URL

        Args:
            image_url: URL of image
            preprocess: Whether to preprocess
            lang: Language(s) to use

        Returns:
            dict: Extraction results
        """
        # Download image
        image = self.download_image(image_url)

        if image is None:
            return {
                "text": "",
                "word_count": 0,
                "confidence": 0.0,
                "error": "Failed to download image",
                "has_text": False
            }

        # Extract text
        result = self.extract_text(image, preprocess, lang)
        result["image_url"] = image_url
        result["image_size"] = f"{image.size[0]}x{image.size[1]}"

        return result

    def extract_from_multiple_images(self, image_urls: List[str], lang: str = 'eng') -> List[Dict]:
        """
        Extract text from multiple images

        Args:
            image_urls: List of image URLs
            lang: Language(s) to use

        Returns:
            list: Results for each image
        """
        results = []

        for idx, url in enumerate(image_urls, 1):
            logger.info(f"Running OCR on image {idx}/{len(image_urls)}")
            result = self.extract_from_url(url, lang=lang)
            results.append(result)

        return results

    def combine_texts(self, ocr_results: List[Dict], caption: str = "") -> Dict:
        """
        Combine OCR text from multiple images with caption

        Args:
            ocr_results: List of OCR results
            caption: Instagram caption text

        Returns:
            dict: Combined text analysis
        """
        # Collect all OCR text
        ocr_texts = [r.get("text", "") for r in ocr_results if r.get("has_text")]
        combined_ocr = "\n\n".join(ocr_texts)

        # Combine with caption
        all_text_parts = []
        if caption.strip():
            all_text_parts.append(f"Caption:\n{caption}")
        if combined_ocr.strip():
            all_text_parts.append(f"Text in Images:\n{combined_ocr}")

        combined_all = "\n\n---\n\n".join(all_text_parts)

        # Calculate statistics
        total_words_ocr = sum(r.get("word_count", 0) for r in ocr_results)
        avg_confidence = sum(r.get("confidence", 0) for r in ocr_results) / len(ocr_results) if ocr_results else 0
        images_with_text = sum(1 for r in ocr_results if r.get("has_text"))

        return {
            "combined_text": combined_all,
            "ocr_text": combined_ocr,
            "caption": caption,
            "total_words_ocr": total_words_ocr,
            "total_words_all": len(combined_all.split()),
            "avg_confidence": round(avg_confidence, 2),
            "images_with_text": images_with_text,
            "total_images": len(ocr_results),
            "has_extractable_text": len(combined_ocr.strip()) > 0
        }

    def _clean_text(self, text: str) -> str:
        """
        Clean OCR output text

        Args:
            text: Raw OCR text

        Returns:
            str: Cleaned text
        """
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)

        # Remove special characters that are likely OCR errors
        text = re.sub(r'[^\w\s\.,!?;:\-\'\"()\[\]/@#$%&*+=<>]', '', text)

        # Trim
        text = text.strip()

        return text

    def detect_language(self, text: str) -> str:
        """
        Simple language detection (can be enhanced)

        Args:
            text: Text to analyze

        Returns:
            str: Detected language code
        """
        # For now, assume English
        # In production, could use langdetect library
        return 'eng'

# Singleton instance
ocr_service = OCRService()
