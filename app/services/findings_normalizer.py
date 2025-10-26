"""
Findings Normalizer Service

Converts raw pipeline outputs into a unified structure for card generation.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class FindingsNormalizer:
    """Normalize raw analysis results into structured findings"""

    def normalize(self, raw_results: Dict, post_info: Dict) -> Dict:
        """
        Convert raw analysis results into normalized findings.

        Args:
            raw_results: Raw output from all pipeline modules
            post_info: Instagram post metadata

        Returns:
            Dict with normalized findings structure
        """
        try:
            logger.info("🔄 Normalizing pipeline findings...")

            normalized = {
                "post_metadata": self._normalize_post_metadata(post_info),
                "ai_detection": self._normalize_ai_detection(raw_results.get("ai_detection", {})),
                "ocr_extraction": self._normalize_ocr(raw_results.get("ocr_text", "")),
                "claim_analysis": self._normalize_claims(raw_results.get("fact_check", {})),
                "claim_verification": self._normalize_verification(raw_results.get("claim_verification", {})),
                "source_credibility": self._normalize_source(raw_results.get("source_credibility", {})),
                "deepfake_detection": self._normalize_deepfake(raw_results.get("deepfake", {})),
                "normalized_at": datetime.utcnow().isoformat()
            }

            logger.info("✅ Findings normalized successfully")
            return normalized

        except Exception as e:
            logger.error(f"❌ Failed to normalize findings: {e}")
            raise

    def _normalize_post_metadata(self, post_info: Dict) -> Dict:
        """Extract relevant post metadata"""
        return {
            "post_id": post_info.get("post_id"),
            "username": post_info.get("username"),
            "is_verified": post_info.get("is_verified", False),
            "post_type": post_info.get("type", "unknown"),
            "timestamp": post_info.get("timestamp"),
            "engagement": {
                "likes": post_info.get("like_count", 0),
                "comments": post_info.get("comment_count", 0)
            },
            "media_counts": {
                "images": post_info.get("image_count", 0),
                "videos": post_info.get("video_count", 0)
            }
        }

    def _normalize_ai_detection(self, ai_results: Dict) -> Dict:
        """Normalize AI detection results"""
        if ai_results.get("status") == "skipped":
            return {
                "performed": False,
                "reason": ai_results.get("reason", "No images to analyze")
            }

        overall = ai_results.get("overall", {})
        individual = ai_results.get("individual_results", [])

        return {
            "performed": True,
            "verdict": "AI_GENERATED" if overall.get("overall_ai_detected") else "REAL",
            "confidence": overall.get("confidence", 0.0),
            "model": ai_results.get("model", "unknown"),
            "summary": overall.get("assessment", ""),
            "details": {
                "ai_images": overall.get("ai_images", 0),
                "real_images": overall.get("real_images", 0),
                "uncertain_images": overall.get("uncertain_images", 0),
                "total_images": overall.get("total_images", 0)
            },
            "evidence": [
                {
                    "image_url": result.get("image_url", ""),
                    "is_ai": result.get("is_ai_generated", False),
                    "confidence": result.get("confidence", 0.0),
                    "reasoning": result.get("reasoning", ""),
                    "indicators": result.get("indicators", [])
                }
                for result in individual
            ]
        }

    def _normalize_ocr(self, ocr_text: str) -> Dict:
        """Normalize OCR extraction results"""
        has_text = bool(ocr_text and len(ocr_text.strip()) > 10)

        return {
            "performed": True,
            "has_text": has_text,
            "text_length": len(ocr_text) if ocr_text else 0,
            "extracted_text": ocr_text if has_text else None,
            "confidence": 0.95 if has_text else 0.0  # High confidence for Claude Vision
        }

    def _normalize_claims(self, fact_check: Dict) -> Dict:
        """Normalize claim analysis results"""
        if fact_check.get("status") == "skipped":
            return {
                "performed": False,
                "reason": fact_check.get("reason", "Insufficient text")
            }

        claim_extraction = fact_check.get("claim_extraction", {})
        credibility = fact_check.get("credibility_analysis", {})
        analyzed_claims = fact_check.get("analyzed_claims", [])

        return {
            "performed": True,
            "has_claims": claim_extraction.get("has_claims", False),
            "total_claims": claim_extraction.get("total_claims", 0),
            "claim_types": claim_extraction.get("claim_types", {}),
            "credibility_score": credibility.get("score", 70.0),
            "interpretation": credibility.get("interpretation", ""),
            "risk_level": fact_check.get("risk_level", "low"),
            "requires_review": fact_check.get("requires_manual_review", False),
            "summary": fact_check.get("summary", ""),
            "penalties": credibility.get("penalties", []),
            "bonuses": credibility.get("bonuses", []),
            "claims": [
                {
                    "text": claim.get("text", ""),
                    "type": claim.get("type", "factual"),
                    "verifiable": claim.get("verifiable", True),
                    "confidence": claim.get("confidence", 0.7),
                    "credibility": claim.get("claim_credibility", 0.5),
                    "red_flags": claim.get("red_flags", []),
                    "indicators": claim.get("indicators", {}),
                    "reasoning": claim.get("reasoning", ""),
                    "needs_verification": claim.get("needs_verification", False)
                }
                for claim in analyzed_claims
            ]
        }

    def _normalize_source(self, source_info: Dict) -> Dict:
        """Normalize source credibility information"""
        return {
            "username": source_info.get("username", ""),
            "is_verified": source_info.get("is_verified", False),
            "account_type": source_info.get("account_type", "unverified"),
            "follower_count": source_info.get("follower_count", 0),
            "reliability_score": source_info.get("reliability_score", 0.5),
            "note": source_info.get("note", "")
        }

    def _normalize_deepfake(self, deepfake_info: Dict) -> Dict:
        """Normalize deepfake detection results"""
        return {
            "performed": deepfake_info.get("status") == "completed",
            "status": deepfake_info.get("status", "pending_implementation"),
            "note": deepfake_info.get("note", "")
        }

    def _normalize_verification(self, verification_info: Dict) -> Dict:
        """Normalize claim verification results"""
        if verification_info.get("status") != "completed":
            return {
                "performed": False,
                "reason": verification_info.get("error", "Not verified")
            }

        verified_claims = verification_info.get("verified_claims", [])

        return {
            "performed": True,
            "total_verified": verification_info.get("total_verified", 0),
            "summary": verification_info.get("summary", ""),
            "claims": [
                {
                    "claim": vc.get("claim", ""),
                    "verdict": vc.get("verification", {}).get("verdict", "UNVERIFIED"),
                    "confidence": vc.get("verification", {}).get("confidence", 0.0),
                    "reasoning": vc.get("verification", {}).get("reasoning", ""),
                    "supporting_sources": vc.get("verification", {}).get("supporting_sources", []),
                    "contradicting_sources": vc.get("verification", {}).get("contradicting_sources", []),
                    "official_sources_found": vc.get("verification", {}).get("official_sources_found", False),
                    "recommendation": vc.get("verification", {}).get("recommendation", "")
                }
                for vc in verified_claims
            ]
        }


# Singleton instance
findings_normalizer = FindingsNormalizer()
