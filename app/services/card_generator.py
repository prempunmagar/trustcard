"""
Claude-Powered TrustCard Generator

Generates human-quality, context-aware report cards from normalized findings.
"""

import logging
import json
import hashlib
from typing import Dict, List
from anthropic import Anthropic
from app.config import settings
from app.schemas.card_schema import (
    TrustCard,
    VerdictSection,
    Evidence,
    OverallAssessment,
    ImpactExplanation
)

logger = logging.getLogger(__name__)


class CardGenerator:
    """Generate TrustCard report cards using Claude AI"""

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
            logger.info("✅ Card Generator initialized")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to initialize Card Generator: {e}")
            return False

    def generate_card(
        self,
        normalized_findings: Dict,
        trust_score: float,
        grade: str,
        analysis_id: str
    ) -> TrustCard:
        """
        Generate a TrustCard from normalized findings using Claude.

        Args:
            normalized_findings: Normalized output from findings_normalizer
            trust_score: Calculated trust score (0-100)
            grade: Letter grade (A-F)
            analysis_id: Analysis ID for traceability

        Returns:
            TrustCard with human-quality narrative
        """
        if not self.initialize():
            # Fallback to template-based generation
            return self._generate_fallback_card(
                normalized_findings, trust_score, grade, analysis_id
            )

        try:
            logger.info(f"🎯 Generating TrustCard for analysis {analysis_id[:8]}...")

            # Prepare prompt with decision matrix
            prompt = self._build_prompt(normalized_findings, trust_score, grade)

            # Call Claude
            message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=3000,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            # Parse Claude's response
            response_text = message.content[0].text.strip()

            # Extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                card_data = json.loads(json_match.group())
            else:
                card_data = json.loads(response_text)

            # Add metadata
            card_data["card_version"] = "1.0.0"
            card_data["analysis_id"] = analysis_id
            card_data["post_id"] = normalized_findings["post_metadata"]["post_id"]
            card_data["raw_findings_hash"] = self._hash_findings(normalized_findings)

            # Validate and create TrustCard
            trust_card = TrustCard(**card_data)

            logger.info(f"✅ Generated TrustCard: {trust_card.overall.verdict}")
            return trust_card

        except Exception as e:
            logger.error(f"❌ Failed to generate card with Claude: {e}")
            # Fallback to template-based generation
            return self._generate_fallback_card(
                normalized_findings, trust_score, grade, analysis_id
            )

    def _build_prompt(self, findings: Dict, trust_score: float, grade: str) -> str:
        """Build Claude prompt with decision matrix and findings"""

        # Determine primary concerns based on findings
        concerns = []
        strengths = []

        # AI Detection analysis
        ai_det = findings.get("ai_detection", {})
        if ai_det.get("performed"):
            if ai_det["verdict"] == "AI_GENERATED":
                concerns.append(f"AI-generated imagery detected (confidence: {ai_det['confidence']:.0%})")
            else:
                strengths.append(f"Authentic imagery verified (confidence: {ai_det['confidence']:.0%})")

        # Claim analysis
        claims = findings.get("claim_analysis", {})
        verification = findings.get("claim_verification", {})

        if claims.get("performed") and claims.get("has_claims"):
            if claims["risk_level"] == "high":
                concerns.append(f"High-risk claims detected ({claims['total_claims']} claims)")
            elif claims["credibility_score"] < 60:
                concerns.append(f"Low credibility score: {claims['credibility_score']:.0f}/100")
            else:
                strengths.append(f"Claims appear credible ({claims['total_claims']} analyzed)")

        # Add verification results
        if verification.get("performed"):
            verified_claims = verification.get("claims", [])
            false_claims = [c for c in verified_claims if c.get("verdict") == "FALSE"]
            unverified_claims = [c for c in verified_claims if c.get("verdict") == "UNVERIFIED"]

            if false_claims:
                concerns.append(f"{len(false_claims)} claim(s) found FALSE by official sources")
            elif unverified_claims:
                concerns.append(f"{len(unverified_claims)} claim(s) could not be verified")

        # Source credibility
        source = findings.get("source_credibility", {})
        if not source.get("is_verified"):
            concerns.append("Unverified account")
        else:
            strengths.append("Verified account")

        prompt = f"""Generate a TrustCard report card from these analysis findings.

## TASK
You are generating a human-readable report card that explains trust and credibility findings to non-technical users. Be conversational but precise. Ground EVERY statement in the provided data.

## INPUT DATA

### Trust Score: {trust_score:.1f}/100 (Grade: {grade})

### Normalized Findings:
```json
{json.dumps(findings, indent=2)}
```

## DECISION MATRIX

Based on the data, follow this logic:

**If AI-generated imagery detected:**
- Primary verdict: "AI-Generated Content Detected"
- Verdict type: "warning" or "fail" depending on confidence
- Evidence: Cite specific indicators from ai_detection module

**If claims present:**
- Analyze credibility_score and risk_level
- Create "Claim Analysis" section
- List specific concerning claims with red_flags
- If risk_level="high": verdict_type="fail"
- **IMPORTANT**: If claim_verification data exists, use it to enhance your analysis
  - Check each verified claim's verdict (TRUE, FALSE, UNVERIFIED, MISLEADING)
  - Reference official_sources_found and supporting/contradicting sources
  - If FALSE claims found: increase severity, cite official sources
  - Include verification reasoning and recommendations in your verdict

**If no claims or images:**
- Focus on source credibility
- Simpler card with "info" verdict type

**Source credibility:**
- Always include as a section
- If unverified account: note as limitation
- If verified: mention as strength

## OUTPUT FORMAT

Generate a JSON object matching this exact structure:

```json
{{
  "overall": {{
    "trust_score": {trust_score},
    "grade": "{grade}",
    "verdict": "One-sentence overall assessment",
    "verdict_type": "pass|fail|warning|info",
    "confidence": 0.0-1.0,
    "key_concerns": ["Top concern 1", "Top concern 2", "Top concern 3"],
    "key_strengths": ["Top strength 1", "Top strength 2"]
  }},
  "sections": [
    {{
      "title": "Section Title (e.g., Image Authenticity)",
      "verdict": "Clear, human-readable verdict statement",
      "verdict_type": "pass|fail|warning|info|pending",
      "confidence": 0.0-1.0,
      "evidence": [
        {{
          "source_module": "module_name (e.g., claude_ai_detection)",
          "finding": "Specific finding from the data",
          "confidence": 0.0-1.0,
          "impact": "positive|negative|neutral"
        }}
      ],
      "reasoning": "Detailed explanation grounded in evidence. Reference specific data points. Use conversational language.",
      "limitations": "Optional: Known limitations or caveats"
    }}
  ],
  "impact": {{
    "why_it_matters": "Plain-language explanation of what these findings mean to regular users",
    "recommended_action": "Optional: What users should do with this information",
    "context": "Optional: Additional context for interpretation"
  }}
}}
```

## CRITICAL RULES

1. **Ground everything in data**: Never invent findings. Only cite what's in the input.
2. **Explicit uncertainty**: Use confidence scores. Say "may" or "appears" when uncertain.
3. **Cite sources**: Every evidence item must reference source_module from input.
4. **Be conversational**: Write like you're explaining to a friend, not a researcher.
5. **Focus on impact**: Users care about "what does this mean?" not technical details.
6. **Adaptive detail**: More claims = more detailed claim section. No images = skip image section.

## EXAMPLES OF GOOD REASONING

Good: "Claude Vision analysis found natural lighting patterns and realistic textures consistent with genuine photography (confidence: 95%). No AI generation artifacts were detected."

Bad: "The image is real." (too vague, no grounding)

Good: "This post makes 4 factual claims about historical events. Our analysis found sensationalist language patterns in 3 of the 4 claims, reducing the credibility score to 50/100."

Bad: "Claims are questionable." (no specifics, no data reference)

## YOUR TASK

Generate the JSON now. Be thorough, conversational, and data-driven.
"""

        return prompt

    def _hash_findings(self, findings: Dict) -> str:
        """Generate hash of findings for traceability"""
        findings_json = json.dumps(findings, sort_keys=True)
        return hashlib.sha256(findings_json.encode()).hexdigest()[:16]

    def _generate_fallback_card(
        self,
        findings: Dict,
        trust_score: float,
        grade: str,
        analysis_id: str
    ) -> TrustCard:
        """Generate a basic card without Claude (fallback)"""
        logger.info("⚠️ Using fallback card generation")

        # Build sections from findings
        sections = []

        # AI Detection section
        ai_det = findings.get("ai_detection", {})
        if ai_det.get("performed"):
            sections.append(VerdictSection(
                title="Image Authenticity",
                verdict=ai_det["summary"],
                verdict_type="pass" if ai_det["verdict"] == "REAL" else "warning",
                confidence=ai_det["confidence"],
                evidence=[
                    Evidence(
                        source_module="ai_detection",
                        finding=ai_det["summary"],
                        confidence=ai_det["confidence"],
                        impact="positive" if ai_det["verdict"] == "REAL" else "negative"
                    )
                ],
                reasoning=f"Analysis detected {ai_det['details']['total_images']} image(s). {ai_det['summary']}",
                limitations="Analysis based on visual inspection"
            ))

        # Claim Analysis section
        claims = findings.get("claim_analysis", {})
        if claims.get("performed") and claims.get("has_claims"):
            sections.append(VerdictSection(
                title="Claim Analysis",
                verdict=claims["interpretation"],
                verdict_type="warning" if claims["credibility_score"] < 60 else "pass",
                confidence=0.7,
                evidence=[
                    Evidence(
                        source_module="fact_check",
                        finding=f"{claims['total_claims']} claims analyzed",
                        confidence=0.7,
                        impact="neutral"
                    )
                ],
                reasoning=claims["summary"],
                limitations="Automated analysis - manual verification recommended for important decisions"
            ))

        # Overall assessment
        overall = OverallAssessment(
            trust_score=trust_score,
            grade=grade,
            verdict=f"Trust score: {trust_score:.0f}/100",
            verdict_type="pass" if trust_score >= 70 else "warning",
            confidence=0.7,
            key_concerns=[],
            key_strengths=[]
        )

        # Impact explanation
        impact = ImpactExplanation(
            why_it_matters="This analysis provides an automated assessment of content credibility.",
            recommended_action="Review detailed findings before sharing"
        )

        return TrustCard(
            card_version="1.0.0",
            analysis_id=analysis_id,
            post_id=findings["post_metadata"]["post_id"],
            overall=overall,
            sections=sections,
            impact=impact,
            raw_findings_hash=self._hash_findings(findings)
        )


# Singleton instance
card_generator = CardGenerator()
