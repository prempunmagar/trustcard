"""
Trust Score Calculator Service

Centralized service for calculating trust scores from analysis results.
Provides detailed breakdowns and explanations for transparency.
"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass, field

from app.config.scoring_config import (
    TrustScoreConfig,
    DEFAULT_CONFIG,
    get_grade_from_score,
    get_grade_description
)

logger = logging.getLogger(__name__)


@dataclass
class ScoreAdjustment:
    """Represents a single score adjustment (penalty or bonus)"""
    component: str  # e.g., "AI Detection", "Fact-Checking"
    category: str   # e.g., "AI Detected", "Low Credibility"
    impact: float   # Positive = bonus, Negative = penalty
    reason: str     # Human-readable explanation
    metadata: Dict = field(default_factory=dict)  # Additional context


@dataclass
class TrustScoreResult:
    """Complete trust score calculation result"""
    final_score: float  # Final trust score (0-100)
    grade: str          # Letter grade (A+ to F)
    grade_info: Dict    # Grade description and color
    adjustments: List[ScoreAdjustment]  # All score adjustments
    component_scores: Dict  # Score contribution per component
    total_penalties: float  # Sum of all penalties
    total_bonuses: float    # Sum of all bonuses
    flags: List[str]        # Warning flags
    requires_review: bool   # Flagged for manual review


class TrustScoreCalculator:
    """
    Calculates trust scores from analysis results with detailed breakdowns.
    """

    def __init__(self, config: TrustScoreConfig = None):
        """
        Initialize calculator with configuration.

        Args:
            config: Scoring configuration (uses DEFAULT_CONFIG if not provided)
        """
        self.config = config if config else DEFAULT_CONFIG

    def calculate_trust_score(self, results: Dict) -> TrustScoreResult:
        """
        Calculate trust score from analysis results.

        Args:
            results: Analysis results dictionary containing:
                - ai_detection: AI detection results
                - ocr: OCR extraction results
                - deepfake: Deepfake detection results
                - fact_check: Fact-checking results
                - source_credibility: Source credibility results

        Returns:
            TrustScoreResult: Complete scoring result with breakdown
        """
        score = self.config.base_score
        adjustments: List[ScoreAdjustment] = []
        flags: List[str] = []
        requires_review = False

        logger.info(f"📊 [Trust Score] Calculating from all analyses")
        logger.info(f"   Base Score: {score}")

        # Process each component
        ai_adjustments = self._process_ai_detection(results.get("ai_detection", {}))
        adjustments.extend(ai_adjustments)

        ocr_adjustments = self._process_ocr(results.get("ocr", {}))
        adjustments.extend(ocr_adjustments)

        deepfake_adjustments = self._process_deepfake(results.get("deepfake", {}))
        adjustments.extend(deepfake_adjustments)

        fact_check_adjustments, fact_flags, fact_review = self._process_fact_checking(
            results.get("fact_check", {})
        )
        adjustments.extend(fact_check_adjustments)
        flags.extend(fact_flags)
        requires_review = requires_review or fact_review

        source_adjustments, source_flags = self._process_source_credibility(
            results.get("source_credibility", {})
        )
        adjustments.extend(source_adjustments)
        flags.extend(source_flags)

        # Calculate final score
        for adjustment in adjustments:
            score += adjustment.impact
            logger.info(f"   {adjustment.category}: {adjustment.impact:+.1f} points")

        # Ensure score is in valid range
        score = max(0.0, min(100.0, score))

        # Calculate totals
        total_penalties = sum(adj.impact for adj in adjustments if adj.impact < 0)
        total_bonuses = sum(adj.impact for adj in adjustments if adj.impact > 0)

        # Get grade
        grade = get_grade_from_score(score, self.config)
        grade_info = get_grade_description(grade)

        # Calculate component scores
        component_scores = self._calculate_component_scores(adjustments)

        logger.info(f"📊 [Trust Score] Final Score: {score:.2f}/100 ({grade})")
        logger.info(f"   Total Penalties: {total_penalties:.1f}")
        logger.info(f"   Total Bonuses: {total_bonuses:.1f}")

        return TrustScoreResult(
            final_score=round(score, 2),
            grade=grade,
            grade_info=grade_info,
            adjustments=adjustments,
            component_scores=component_scores,
            total_penalties=round(total_penalties, 2),
            total_bonuses=round(total_bonuses, 2),
            flags=flags,
            requires_review=requires_review
        )

    def _process_ai_detection(self, ai_detection: Dict) -> List[ScoreAdjustment]:
        """Process AI detection results"""
        adjustments = []

        if ai_detection.get("status") != "completed":
            return adjustments

        overall = ai_detection.get("overall", {})

        if overall.get("overall_ai_detected"):
            confidence = overall.get("confidence", 0.0)
            penalty = -confidence * self.config.ai_detection.max_penalty

            adjustments.append(ScoreAdjustment(
                component="AI Detection",
                category="AI-Generated Content",
                impact=penalty,
                reason=f"AI-generated content detected with {confidence:.0%} confidence",
                metadata={
                    "confidence": confidence,
                    "ai_images": overall.get("ai_images", 0),
                    "total_images": overall.get("total_images", 0)
                }
            ))

        return adjustments

    def _process_ocr(self, ocr: Dict) -> List[ScoreAdjustment]:
        """Process OCR results (informational only, no score impact)"""
        adjustments = []

        if ocr.get("status") == "completed":
            summary = ocr.get("summary", {})
            if summary.get("has_text"):
                logger.info(f"   OCR: Extracted {summary.get('total_words_extracted', 0)} words")

        return adjustments

    def _process_deepfake(self, deepfake: Dict) -> List[ScoreAdjustment]:
        """Process deepfake detection results"""
        adjustments = []

        if deepfake.get("status") != "completed":
            return adjustments

        if deepfake.get("is_deepfake"):
            penalty = -self.config.deepfake.deepfake_penalty

            adjustments.append(ScoreAdjustment(
                component="Deepfake Detection",
                category="Deepfake/Manipulation",
                impact=penalty,
                reason="Video or image manipulation detected",
                metadata={
                    "analysis": deepfake.get("analysis", {})
                }
            ))

        return adjustments

    def _process_fact_checking(self, fact_check: Dict) -> tuple:
        """Process fact-checking results"""
        adjustments = []
        flags = []
        requires_review = False

        if fact_check.get("status") != "completed":
            return adjustments, flags, requires_review

        credibility = fact_check.get("credibility_analysis", {})
        credibility_score = credibility.get("score", 70.0)

        weights = self.config.fact_check

        # Credibility score impact
        if credibility_score < weights.low_credibility_threshold:
            # Low credibility: significant penalty
            penalty = -(50 - credibility_score) * weights.low_credibility_multiplier
            adjustments.append(ScoreAdjustment(
                component="Fact-Checking",
                category="Low Credibility",
                impact=penalty,
                reason=f"Claims show low credibility (score: {credibility_score:.0f}/100)",
                metadata={"credibility_score": credibility_score}
            ))

        elif credibility_score < weights.questionable_threshold:
            # Questionable credibility: moderate penalty
            penalty = -(70 - credibility_score) * weights.questionable_multiplier
            adjustments.append(ScoreAdjustment(
                component="Fact-Checking",
                category="Questionable Credibility",
                impact=penalty,
                reason=f"Claims show questionable credibility (score: {credibility_score:.0f}/100)",
                metadata={"credibility_score": credibility_score}
            ))

        elif credibility_score >= weights.high_credibility_threshold:
            # High credibility: small bonus
            bonus = (credibility_score - 80) * weights.high_credibility_multiplier
            adjustments.append(ScoreAdjustment(
                component="Fact-Checking",
                category="High Credibility",
                impact=bonus,
                reason=f"Claims show high credibility (score: {credibility_score:.0f}/100)",
                metadata={"credibility_score": credibility_score}
            ))

        # Red flag penalties
        fact_flags = fact_check.get("flags", [])

        if "MEDICAL_CLAIMS" in str(fact_flags):
            penalty = -weights.medical_claims_penalty
            adjustments.append(ScoreAdjustment(
                component="Fact-Checking",
                category="Medical Claims",
                impact=penalty,
                reason="Medical or health claims without verification",
                metadata={}
            ))
            flags.append("Medical claims require verification")

        if "CONSPIRACY_LANGUAGE" in fact_flags:
            penalty = -weights.conspiracy_language_penalty
            adjustments.append(ScoreAdjustment(
                component="Fact-Checking",
                category="Conspiracy Language",
                impact=penalty,
                reason="Conspiracy theory language detected",
                metadata={}
            ))
            flags.append("Conspiracy theory language detected")

        if "URGENT_LANGUAGE" in fact_flags:
            penalty = -weights.urgent_language_penalty
            adjustments.append(ScoreAdjustment(
                component="Fact-Checking",
                category="Urgent Language",
                impact=penalty,
                reason="Urgent/alarmist language detected",
                metadata={}
            ))

        if "ABSOLUTIST_CLAIMS" in fact_flags:
            penalty = -weights.absolutist_claims_penalty
            adjustments.append(ScoreAdjustment(
                component="Fact-Checking",
                category="Absolutist Claims",
                impact=penalty,
                reason="Absolutist language (always/never) detected",
                metadata={}
            ))

        if "UNVERIFIED_SOURCES" in fact_flags:
            penalty = -weights.unverified_sources_penalty
            adjustments.append(ScoreAdjustment(
                component="Fact-Checking",
                category="Unverified Sources",
                impact=penalty,
                reason="Unverified or anonymous sources cited",
                metadata={}
            ))

        if "EMOTIONAL_MANIPULATION" in fact_flags:
            penalty = -weights.emotional_manipulation_penalty
            adjustments.append(ScoreAdjustment(
                component="Fact-Checking",
                category="Emotional Manipulation",
                impact=penalty,
                reason="Emotionally manipulative language detected",
                metadata={}
            ))

        if "SENSATIONALISM" in fact_flags:
            penalty = -weights.sensationalism_penalty
            adjustments.append(ScoreAdjustment(
                component="Fact-Checking",
                category="Sensationalism",
                impact=penalty,
                reason="Sensationalist language detected",
                metadata={}
            ))

        # Manual review flag
        if fact_check.get("requires_manual_review"):
            requires_review = True
            flags.append("Flagged for manual review")
            logger.info(f"   ⚠️  Flagged for manual review")

        return adjustments, flags, requires_review

    def _process_source_credibility(self, source_cred: Dict) -> tuple:
        """Process source credibility results"""
        adjustments = []
        flags = []

        if source_cred.get("status") != "completed":
            return adjustments, flags

        assessment = source_cred.get("assessment", {})
        weights = self.config.source_credibility

        # Check for conspiracy sources (very serious)
        if assessment.get("has_conspiracy"):
            penalty = -weights.conspiracy_sources_penalty
            adjustments.append(ScoreAdjustment(
                component="Source Credibility",
                category="Conspiracy Sources",
                impact=penalty,
                reason="Links to known conspiracy theory websites",
                metadata={}
            ))
            flags.append("Conspiracy theory sources detected")

        # Check for unreliable sources
        elif assessment.get("has_unreliable_sources"):
            penalty = -weights.unreliable_sources_penalty
            adjustments.append(ScoreAdjustment(
                component="Source Credibility",
                category="Unreliable Sources",
                impact=penalty,
                reason="Links to unreliable or low-credibility sources",
                metadata={}
            ))
            flags.append("Unreliable sources detected")

        # Check for satire
        elif assessment.get("has_satire"):
            penalty = -weights.satire_penalty
            adjustments.append(ScoreAdjustment(
                component="Source Credibility",
                category="Satire Content",
                impact=penalty,
                reason="Links to satire/parody content (may be mistaken as factual)",
                metadata={}
            ))
            flags.append("Satire content detected")

        # Adjust based on average reliability
        else:
            avg_reliability = assessment.get("avg_reliability_score", 0.5)

            if avg_reliability < weights.low_reliability_threshold:
                penalty = -(0.5 - avg_reliability) * weights.low_reliability_multiplier
                adjustments.append(ScoreAdjustment(
                    component="Source Credibility",
                    category="Low Source Reliability",
                    impact=penalty,
                    reason=f"Sources have low average reliability ({avg_reliability:.0%})",
                    metadata={"avg_reliability": avg_reliability}
                ))

            elif avg_reliability > weights.high_reliability_threshold:
                bonus = (avg_reliability - 0.7) * weights.high_reliability_multiplier
                adjustments.append(ScoreAdjustment(
                    component="Source Credibility",
                    category="High Source Reliability",
                    impact=bonus,
                    reason=f"Sources have high reliability ({avg_reliability:.0%})",
                    metadata={"avg_reliability": avg_reliability}
                ))

        return adjustments, flags

    def _calculate_component_scores(self, adjustments: List[ScoreAdjustment]) -> Dict:
        """Calculate total impact per component"""
        component_scores = {}

        for adjustment in adjustments:
            component = adjustment.component
            if component not in component_scores:
                component_scores[component] = 0.0
            component_scores[component] += adjustment.impact

        # Round all scores
        return {k: round(v, 2) for k, v in component_scores.items()}


# Global calculator instance
trust_score_calculator = TrustScoreCalculator()


def calculate_trust_score(results: Dict, config: TrustScoreConfig = None) -> TrustScoreResult:
    """
    Convenience function to calculate trust score.

    Args:
        results: Analysis results
        config: Optional custom configuration

    Returns:
        TrustScoreResult: Complete scoring result
    """
    calculator = TrustScoreCalculator(config) if config else trust_score_calculator
    return calculator.calculate_trust_score(results)
