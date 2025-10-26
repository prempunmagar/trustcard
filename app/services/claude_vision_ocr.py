"""
Claude Vision OCR Service

Uses Anthropic's Claude Vision API for accurate text extraction from images.
"""

import logging
import base64
import requests
from typing import Optional
from anthropic import Anthropic
from app.config import settings

logger = logging.getLogger(__name__)


class ClaudeVisionOCR:
    """Extract text from images using Claude Vision"""

    def __init__(self):
        self.client = None
        self._initialized = False

    def initialize(self):
        """Initialize Anthropic client"""
        if self._initialized:
            return True

        api_key = settings.ANTHROPIC_API_KEY
        if not api_key:
            logger.warning("⚠️ Anthropic API key not configured")
            return False

        try:
            self.client = Anthropic(api_key=api_key)
            self._initialized = True
            logger.info("✅ Claude Vision OCR initialized")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to initialize Claude Vision: {e}")
            return False

    def extract_text_from_url(self, image_url: str) -> Optional[str]:
        """
        Extract text from an image URL using Claude Vision.

        Args:
            image_url: URL to the image

        Returns:
            Extracted text or None if extraction failed
        """
        if not self.initialize():
            return None

        try:
            logger.info(f"🔍 Extracting text using Claude Vision from {image_url[:50]}...")

            # Create vision message
            message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "url",
                                    "url": image_url,
                                },
                            },
                            {
                                "type": "text",
                                "text": "Please extract ALL text you see in this image. Return only the text itself, exactly as it appears, preserving any line breaks. Do not add any commentary or explanation, just the extracted text."
                            }
                        ],
                    }
                ],
            )

            # Extract text from response
            if message.content and len(message.content) > 0:
                extracted_text = message.content[0].text.strip()
                logger.info(f"✅ Claude Vision extracted {len(extracted_text)} characters")
                return extracted_text
            else:
                logger.warning("⚠️ Claude Vision returned empty response")
                return None

        except Exception as e:
            logger.error(f"❌ Claude Vision extraction failed: {e}")
            return None

    def extract_text_from_image_bytes(self, image_bytes: bytes, media_type: str = "image/jpeg") -> Optional[str]:
        """
        Extract text from image bytes using Claude Vision.

        Args:
            image_bytes: Image data as bytes
            media_type: MIME type (image/jpeg, image/png, etc.)

        Returns:
            Extracted text or None if extraction failed
        """
        if not self.initialize():
            return None

        try:
            logger.info(f"🔍 Extracting text using Claude Vision from image bytes...")

            # Encode image to base64
            image_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")

            # Create vision message
            message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": image_b64,
                                },
                            },
                            {
                                "type": "text",
                                "text": "Please extract ALL text you see in this image. Return only the text itself, exactly as it appears, preserving any line breaks. Do not add any commentary or explanation, just the extracted text."
                            }
                        ],
                    }
                ],
            )

            # Extract text from response
            if message.content and len(message.content) > 0:
                extracted_text = message.content[0].text.strip()
                logger.info(f"✅ Claude Vision extracted {len(extracted_text)} characters")
                return extracted_text
            else:
                logger.warning("⚠️ Claude Vision returned empty response")
                return None

        except Exception as e:
            logger.error(f"❌ Claude Vision extraction failed: {e}")
            return None


# Singleton instance
claude_vision_ocr = ClaudeVisionOCR()
