"""
Claude Vision AI Image Detection Service

Uses Anthropic's Claude Vision API to detect AI-generated images.
Much more accurate than traditional ML models and requires no local model downloads.
"""

import logging
import requests
from typing import Dict, Optional, List
from anthropic import Anthropic
from app.config import settings

logger = logging.getLogger(__name__)


class ClaudeAIDetection:
    """Detect AI-generated images using Claude Vision"""

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
            logger.info("✅ Claude AI Detection initialized")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to initialize Claude AI Detection: {e}")
            return False

    def detect_ai_image(self, image_url: str) -> Dict:
        """
        Detect if an image is AI-generated using Claude Vision.

        Args:
            image_url: URL to the image

        Returns:
            Dict with detection results
        """
        if not self.initialize():
            return {
                "is_ai_generated": False,
                "confidence": 0.0,
                "ai_score": 0.0,
                "real_score": 1.0,
                "reasoning": "Claude Vision not available",
                "method": "fallback",
                "error": "API not configured"
            }

        try:
            # Download image
            logger.info(f"🔍 Analyzing image for AI generation: {image_url[:50]}...")
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()
            image_bytes = response.content

            # Determine media type
            content_type = response.headers.get('content-type', 'image/jpeg')
            media_type = content_type if content_type.startswith('image/') else 'image/jpeg'

            # Analyze with Claude Vision
            import base64
            image_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")

            message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=500,
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
                                "text": """Analyze this image and determine if it is AI-generated or real.

Look for these AI generation indicators:
- Unnatural lighting or shadows
- Anatomical impossibilities (extra fingers, distorted faces)
- Unrealistic textures or patterns
- Inconsistent perspectives
- Overly smooth or perfect elements
- Artifacts or distortions typical of AI generation

Respond in this exact JSON format:
{
    "is_ai_generated": true/false,
    "confidence": 0.0-1.0,
    "reasoning": "Brief explanation of your determination",
    "indicators": ["list", "of", "specific", "indicators", "found"]
}"""
                            }
                        ],
                    }
                ],
            )

            # Parse Claude's response
            if message.content and len(message.content) > 0:
                response_text = message.content[0].text.strip()

                # Extract JSON from response (Claude sometimes adds markdown formatting)
                import json
                import re

                # Try to find JSON in the response
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                else:
                    # Fallback parsing
                    result = json.loads(response_text)

                is_ai = result.get('is_ai_generated', False)
                confidence = float(result.get('confidence', 0.5))
                reasoning = result.get('reasoning', 'No reasoning provided')
                indicators = result.get('indicators', [])

                logger.info(f"✅ Claude Vision analysis: AI={is_ai}, confidence={confidence:.2f}")

                return {
                    "is_ai_generated": is_ai,
                    "confidence": confidence,
                    "ai_score": confidence if is_ai else (1 - confidence),
                    "real_score": (1 - confidence) if is_ai else confidence,
                    "reasoning": reasoning,
                    "indicators": indicators,
                    "method": "claude_vision",
                    "model": "claude-3-5-sonnet-20241022"
                }
            else:
                logger.warning("⚠️ Claude Vision returned empty response")
                return {
                    "is_ai_generated": False,
                    "confidence": 0.0,
                    "ai_score": 0.0,
                    "real_score": 1.0,
                    "reasoning": "Empty response from Claude",
                    "method": "claude_vision",
                    "error": "empty_response"
                }

        except Exception as e:
            logger.error(f"❌ Claude AI detection failed: {e}")
            return {
                "is_ai_generated": False,
                "confidence": 0.0,
                "ai_score": 0.0,
                "real_score": 1.0,
                "reasoning": f"Detection failed: {str(e)}",
                "method": "claude_vision",
                "error": str(e)
            }

    def detect_multiple_images(self, image_urls: List[str]) -> Dict:
        """
        Analyze multiple images for AI generation.

        Args:
            image_urls: List of image URLs

        Returns:
            Dict with overall and individual results
        """
        if not image_urls:
            return {
                "overall_ai_detected": False,
                "confidence": 0.0,
                "ai_images": 0,
                "real_images": 0,
                "uncertain_images": 0,
                "total_images": 0,
                "assessment": "No images to analyze",
                "individual_results": []
            }

        individual_results = []
        ai_count = 0
        real_count = 0
        uncertain_count = 0

        for idx, image_url in enumerate(image_urls, 1):
            logger.info(f"Analyzing image {idx}/{len(image_urls)}")
            result = self.detect_ai_image(image_url)
            result["image_url"] = image_url
            individual_results.append(result)

            if result.get("confidence", 0) >= 0.7:
                if result.get("is_ai_generated"):
                    ai_count += 1
                else:
                    real_count += 1
            else:
                uncertain_count += 1

        # Overall assessment
        overall_ai = ai_count > (len(image_urls) / 2)
        avg_confidence = sum(r.get("confidence", 0) for r in individual_results) / len(individual_results)

        if ai_count == len(image_urls):
            assessment = "All images appear to be AI-generated"
        elif real_count == len(image_urls):
            assessment = "All images appear to be real photographs"
        elif ai_count > 0:
            assessment = f"{ai_count} of {len(image_urls)} images appear to be AI-generated"
        else:
            assessment = "Unable to determine with confidence"

        return {
            "overall_ai_detected": overall_ai,
            "confidence": avg_confidence,
            "ai_images": ai_count,
            "real_images": real_count,
            "uncertain_images": uncertain_count,
            "total_images": len(image_urls),
            "assessment": assessment,
            "individual_results": individual_results
        }


# Singleton instance
claude_ai_detection = ClaudeAIDetection()
