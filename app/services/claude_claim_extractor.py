"""
Claude-based Claim Extraction Service

Uses Anthropic's Claude API for intelligent claim extraction and analysis.
Much more accurate than spaCy for understanding context, nuance, and implicit claims.
"""

import logging
import json
from typing import Dict, List
from anthropic import Anthropic
from app.config import settings

logger = logging.getLogger(__name__)


class ClaudeClaimExtractor:
    """Extract and analyze claims using Claude AI"""

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
            logger.info("✅ Claude Claim Extractor initialized")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to initialize Claude Claim Extractor: {e}")
            return False

    def extract_claims(self, text: str, caption: str = "") -> Dict:
        """
        Extract factual claims from text using Claude.

        Args:
            text: Combined text (caption + OCR)
            caption: Original caption

        Returns:
            Dict with extracted claims and analysis
        """
        if not self.initialize():
            return {
                "has_claims": False,
                "total_claims": 0,
                "claims": [],
                "error": "Claude API not configured"
            }

        try:
            logger.info(f"🔍 Extracting claims from {len(text)} characters of text")

            # Prepare the prompt for Claude
            prompt = f"""Analyze this Instagram post and extract all factual claims.

POST CONTENT:
{text}

Extract all factual claims (statements that can be verified as true or false). For each claim, identify:
1. The exact claim text
2. Claim type (factual, statistical, causal, predictive)
3. Whether it's verifiable
4. Credibility indicators (sensationalism, bias, logical fallacies)
5. Red flags (excessive caps, suspicious patterns, clickbait)

Respond in this exact JSON format:
{{
    "claims": [
        {{
            "text": "exact claim text",
            "type": "factual|statistical|causal|predictive",
            "verifiable": true/false,
            "confidence": 0.0-1.0,
            "credibility_score": 0.0-1.0,
            "indicators": {{
                "sensationalism": true/false,
                "bias": true/false,
                "logical_fallacy": true/false,
                "emotional_manipulation": true/false
            }},
            "red_flags": ["list", "of", "specific", "red", "flags"],
            "reasoning": "Brief explanation of credibility assessment"
        }}
    ],
    "summary": {{
        "total_claims": 0,
        "verifiable_claims": 0,
        "high_credibility_claims": 0,
        "red_flag_count": 0,
        "overall_assessment": "Brief overall assessment",
        "risk_level": "low|medium|high"
    }}
}}

Be thorough - extract both explicit and implicit claims. Consider context and tone."""

            # Call Claude API
            message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2000,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
            )

            # Parse Claude's response
            if message.content and len(message.content) > 0:
                response_text = message.content[0].text.strip()

                # Extract JSON from response
                import re
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                else:
                    result = json.loads(response_text)

                claims = result.get('claims', [])
                summary = result.get('summary', {})

                logger.info(f"✅ Extracted {len(claims)} claims using Claude")

                # Format claims to match expected structure
                formatted_claims = []
                for claim in claims:
                    formatted_claims.append({
                        "text": claim.get("text", ""),
                        "type": claim.get("type", "factual"),
                        "verifiable": claim.get("verifiable", True),
                        "confidence": claim.get("confidence", 0.7),
                        "claim_credibility": claim.get("credibility_score", 0.5),
                        "indicators": claim.get("indicators", {}),
                        "red_flags": claim.get("red_flags", []),
                        "reasoning": claim.get("reasoning", ""),
                        "requires_source": False,
                        "needs_verification": claim.get("credibility_score", 0.5) < 0.6
                    })

                return {
                    "has_claims": len(claims) > 0,
                    "total_claims": len(claims),
                    "claims": formatted_claims,
                    "summary": summary,
                    "claim_types": {
                        claim_type: sum(1 for c in claims if c.get('type') == claim_type)
                        for claim_type in ['factual', 'statistical', 'causal', 'predictive']
                    },
                    "method": "claude"
                }
            else:
                logger.warning("⚠️ Claude returned empty response for claim extraction")
                return {
                    "has_claims": False,
                    "total_claims": 0,
                    "claims": [],
                    "error": "empty_response"
                }

        except Exception as e:
            logger.error(f"❌ Claude claim extraction failed: {e}")
            return {
                "has_claims": False,
                "total_claims": 0,
                "claims": [],
                "error": str(e)
            }

    def analyze_credibility(self, claims: List[Dict]) -> Dict:
        """
        Analyze overall credibility of extracted claims.

        Args:
            claims: List of extracted claims

        Returns:
            Dict with credibility analysis
        """
        if not claims:
            return {
                "score": 70.0,
                "interpretation": "No claims to assess",
                "penalties": [],
                "bonuses": []
            }

        # Count indicators
        red_flag_count = sum(len(claim.get("red_flags", [])) for claim in claims)
        sensationalism_count = sum(1 for claim in claims if claim.get("indicators", {}).get("sensationalism"))
        bias_count = sum(1 for claim in claims if claim.get("indicators", {}).get("bias"))
        low_credibility_count = sum(1 for claim in claims if claim.get("claim_credibility", 0.5) < 0.5)

        # Calculate score
        base_score = 70.0
        penalties = []
        bonuses = []

        # Apply penalties
        if red_flag_count > 0:
            penalty = min(red_flag_count * 5, 30)
            penalties.append({
                "reason": f"{red_flag_count} red flag(s) detected",
                "penalty": penalty
            })
            base_score -= penalty

        if sensationalism_count > 0:
            penalty = min(sensationalism_count * 5, 15)
            penalties.append({
                "reason": f"{sensationalism_count} sensationalist claim(s)",
                "penalty": penalty
            })
            base_score -= penalty

        if bias_count > 0:
            penalty = min(bias_count * 3, 10)
            penalties.append({
                "reason": f"{bias_count} biased claim(s)",
                "penalty": penalty
            })
            base_score -= penalty

        if low_credibility_count > len(claims) / 2:
            penalties.append({
                "reason": "Majority of claims have low credibility",
                "penalty": 15
            })
            base_score -= 15

        # Interpretation
        if base_score >= 80:
            interpretation = "High credibility"
        elif base_score >= 60:
            interpretation = "Moderate credibility"
        elif base_score >= 40:
            interpretation = "Questionable - Multiple red flags"
        else:
            interpretation = "Low credibility - Many warning signs"

        return {
            "score": max(base_score, 0),
            "interpretation": interpretation,
            "penalties": penalties,
            "bonuses": bonuses
        }


# Singleton instance
claude_claim_extractor = ClaudeClaimExtractor()
