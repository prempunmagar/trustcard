"""
Source Evaluation Service

Evaluates the credibility and bias of content sources.
"""

from sqlalchemy.orm import Session
from urllib.parse import urlparse
import re
import logging
from typing import Dict, Optional, List

from app.database import get_db_context
from app.models.source_credibility import SourceCredibility

logger = logging.getLogger(__name__)


class SourceEvaluationService:
    """Service for evaluating source credibility."""

    # Reliability scores (for numerical calculations)
    RELIABILITY_SCORES = {
        "very-high": 1.0,
        "high": 0.8,
        "mixed": 0.5,
        "low": 0.3,
        "very-low": 0.1,
        "satire": 0.0,  # Special case
        "unknown": 0.5
    }

    # Bias spectrum (informational, not judgmental)
    BIAS_SPECTRUM = {
        "extreme-left": -2,
        "left": -1,
        "left-center": -0.5,
        "center": 0,
        "right-center": 0.5,
        "right": 1,
        "extreme-right": 2,
        "satire": 0,
        "varies": 0,
        "unknown": 0
    }

    def __init__(self):
        self._cache = {}  # Simple in-memory cache

    def extract_domain(self, url: str) -> Optional[str]:
        """
        Extract domain from URL.

        Args:
            url: Full URL

        Returns:
            str: Domain name or None
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc or parsed.path

            # Remove www prefix
            domain = re.sub(r'^www\.', '', domain)

            # Remove subdomains for major platforms
            # e.g., mobile.twitter.com -> twitter.com
            major_platforms = [
                'instagram.com', 'facebook.com', 'twitter.com', 'x.com',
                'youtube.com', 'reddit.com', 'tiktok.com'
            ]

            for platform in major_platforms:
                if platform in domain:
                    domain = platform
                    break

            # Remove port if present
            domain = domain.split(':')[0]

            return domain.lower()
        except Exception as e:
            logger.error(f"Failed to extract domain from {url}: {e}")
            return None

    def get_source_credibility(self, url: str) -> Dict:
        """
        Get credibility rating for a source URL.

        Args:
            url: Source URL

        Returns:
            dict: Credibility information
        """
        domain = self.extract_domain(url)

        if not domain:
            return self._unknown_source()

        # Check cache
        if domain in self._cache:
            return self._cache[domain]

        # Query database
        with get_db_context() as db:
            source = db.query(SourceCredibility).filter(
                SourceCredibility.domain == domain
            ).first()

            if source:
                result = {
                    "domain": source.domain,
                    "bias_rating": source.bias_rating,
                    "reliability_rating": source.reliability_rating,
                    "description": source.description,
                    "reliability_score": self.RELIABILITY_SCORES.get(
                        source.reliability_rating, 0.5
                    ),
                    "bias_score": self.BIAS_SPECTRUM.get(
                        source.bias_rating, 0
                    ),
                    "in_database": True,
                    "assessment": self._generate_assessment(
                        source.bias_rating,
                        source.reliability_rating
                    )
                }

                # Cache result
                self._cache[domain] = result
                return result

        # Unknown source
        result = self._unknown_source(domain)
        self._cache[domain] = result
        return result

    def _unknown_source(self, domain: Optional[str] = None) -> Dict:
        """Return data for unknown sources."""
        return {
            "domain": domain or "unknown",
            "bias_rating": "unknown",
            "reliability_rating": "unknown",
            "description": "Source not in credibility database. Verify independently.",
            "reliability_score": 0.5,  # Neutral score
            "bias_score": 0,
            "in_database": False,
            "assessment": "Unknown source. Exercise caution and verify claims independently."
        }

    def _generate_assessment(self, bias: str, reliability: str) -> str:
        """Generate human-readable assessment."""

        # Special cases
        if reliability == "satire":
            return "⚠️ This is a SATIRE site. Content is not intended to be factual."

        if reliability == "very-low":
            return "❌ This source has a very poor factual record. Claims should be verified with reliable sources."

        if reliability == "low":
            return "⚠️ This source has a poor factual record. Verify claims with reliable sources."

        # Build assessment
        reliability_text = {
            "very-high": "excellent",
            "high": "good",
            "mixed": "mixed",
            "unknown": "unknown"
        }.get(reliability, "unknown")

        bias_text = {
            "extreme-left": "extreme left",
            "left": "left",
            "left-center": "left-center",
            "center": "minimal",
            "right-center": "right-center",
            "right": "right",
            "extreme-right": "extreme right",
            "varies": "varies",
            "unknown": "unknown"
        }.get(bias, "unknown")

        if reliability in ["very-high", "high"]:
            return f"✅ This source has {reliability_text} factual reporting with {bias_text} bias."
        elif reliability == "mixed":
            return f"⚡ This source has {reliability_text} factual reporting with {bias_text} bias. Verify important claims."
        else:
            return f"This source has {reliability_text} factual reporting with {bias_text} bias."

    def evaluate_instagram_user(self, user_info: Dict) -> Dict:
        """
        Evaluate Instagram user credibility.

        Args:
            user_info: User information from Instagram

        Returns:
            dict: Credibility assessment
        """
        username = user_info.get("username", "unknown")
        is_verified = user_info.get("is_verified", False)
        follower_count = user_info.get("follower_count", 0)

        # Base assessment
        assessment = {
            "username": username,
            "is_verified": is_verified,
            "follower_count": follower_count,
            "account_type": "verified" if is_verified else "unverified",
            "reliability_score": 0.6 if is_verified else 0.4,
            "note": ""
        }

        if is_verified:
            assessment["note"] = "✓ Verified account. However, verify claims independently."
        else:
            assessment["note"] = "Unverified account. Verify claims with reliable sources."

        return assessment

    def get_overall_source_assessment(
        self,
        external_urls: List[str],
        instagram_user: Dict
    ) -> Dict:
        """
        Get overall source assessment combining external links and user.

        Args:
            external_urls: List of external URLs shared in post
            instagram_user: Instagram user info

        Returns:
            dict: Overall assessment
        """
        # Evaluate Instagram user
        user_assessment = self.evaluate_instagram_user(instagram_user)

        # Evaluate external sources
        external_sources = []
        if external_urls:
            for url in external_urls[:5]:  # Limit to first 5
                source = self.get_source_credibility(url)
                external_sources.append(source)

        # Calculate average reliability if external sources exist
        if external_sources:
            avg_reliability = sum(
                s.get("reliability_score", 0.5) for s in external_sources
            ) / len(external_sources)

            lowest_reliability = min(
                s.get("reliability_score", 0.5) for s in external_sources
            )

            # Check for problematic sources
            has_unreliable = any(
                s.get("reliability_rating") in ["low", "very-low"]
                for s in external_sources
            )

            has_satire = any(
                s.get("reliability_rating") == "satire"
                for s in external_sources
            )

            # Check for conspiracy sources
            has_conspiracy = any(
                s.get("reliability_rating") == "very-low"
                for s in external_sources
            )
        else:
            avg_reliability = user_assessment["reliability_score"]
            lowest_reliability = avg_reliability
            has_unreliable = False
            has_satire = False
            has_conspiracy = False

        # Generate overall assessment
        if has_conspiracy:
            overall = "❌ Post links to conspiracy/unreliable sources. Claims are likely false."
        elif has_satire:
            overall = "⚠️ Post links to satire content. Not intended as factual."
        elif has_unreliable or lowest_reliability < 0.3:
            overall = "❌ Post links to unreliable sources. Verify claims independently."
        elif avg_reliability > 0.7:
            overall = "✅ Sources appear credible, but always verify important claims."
        elif avg_reliability > 0.5:
            overall = "⚡ Mixed source credibility. Verify important claims."
        else:
            overall = "⚠️ Source credibility unclear. Exercise caution."

        return {
            "instagram_user": user_assessment,
            "external_sources": external_sources,
            "external_source_count": len(external_sources),
            "avg_reliability_score": round(avg_reliability, 2),
            "lowest_reliability_score": round(lowest_reliability, 2),
            "has_unreliable_sources": has_unreliable,
            "has_satire": has_satire,
            "has_conspiracy": has_conspiracy,
            "overall_assessment": overall,
            "recommendation": self._generate_recommendation(
                avg_reliability,
                has_unreliable,
                has_satire,
                has_conspiracy
            )
        }

    def _generate_recommendation(
        self,
        avg_reliability: float,
        has_unreliable: bool,
        has_satire: bool,
        has_conspiracy: bool
    ) -> str:
        """Generate actionable recommendation for users."""
        if has_conspiracy:
            return "Do not trust claims without verification from reliable sources."
        elif has_satire:
            return "This content is satirical. Do not share as factual information."
        elif has_unreliable:
            return "Cross-check claims with established news organizations or fact-checkers."
        elif avg_reliability > 0.7:
            return "Sources are generally reliable, but verify before sharing important claims."
        elif avg_reliability > 0.5:
            return "Check additional sources before accepting claims as factual."
        else:
            return "Exercise caution. Verify all claims with trusted sources."


# Singleton instance
source_evaluation_service = SourceEvaluationService()
