"""
Fact-Checking Service

Analyzes claims for credibility using heuristic pattern matching.
"""

import re
import logging
from typing import List, Dict
from langdetect import detect, LangDetectException

logger = logging.getLogger(__name__)


class FactCheckingService:
    """Heuristic-based fact-checking and credibility analysis."""

    def __init__(self):
        # Red flag patterns indicating potential misinformation
        self.red_flag_patterns = {
            'urgent_language': [
                r'\b(urgent|emergency|immediately|right now|act now|hurry|quick|asap)\b',
                r'\b(before it\'s (too late|deleted|removed|banned))\b',
                r'\b(they (don\'t want|are hiding|won\'t tell))\b',
            ],
            'absolutist_language': [
                r'\b(always|never|every|all|none|100%|completely|totally|absolutely)\b',
                r'\b(everyone knows|everybody says|no one)\b',
                r'\b(proven fact|undeniable|irrefutable|guaranteed)\b',
            ],
            'unverified_sources': [
                r'\b(a (doctor|scientist|expert|friend) (said|told me))\b',
                r'\b(studies show|research shows)\b(?! from)',  # Without specific source
                r'\b(I (heard|read) (that|somewhere))\b',
                r'\b((they|people) say)\b',
            ],
            'conspiracy_indicators': [
                r'\b(cover([ -]?up)?|conspiracy|secret|hidden (truth|agenda))\b',
                r'\b(big (pharma|tech|government|media))\b',
                r'\b(wake up|sheeple|open your eyes)\b',
                r'\b(deep state|new world order)\b',
            ],
            'emotional_manipulation': [
                r'\b(shocking|terrifying|devastating|horrifying|outrageous)\b',
                r'\b(you (won\'t believe|need to see|must know))\b',
                r'\b(this will (change|blow your mind|shock you))\b',
            ],
            'sensationalism': [
                r'[!]{3,}',  # Multiple exclamation marks
                r'[?]{3,}',  # Multiple question marks
                r'\b[A-Z]{5,}\b',  # All caps words (5+ letters)
                r'!!!|\?\?\?|!!!',  # Excessive punctuation
            ]
        }

        # Medical misinformation patterns
        self.medical_red_flags = [
            r'\b(cure[sd]?|curing|100% (effective|cure))\b(?! cancer)',  # Miracle cures
            r'\b(natural (cure|remedy|treatment) for)\b',
            r'\b(big pharma (hiding|covering up|doesn\'t want))\b',
            r'\b(vaccine[sd]? (cause[sd]?|contain[sd]?))\b',
            r'\b(detox|cleanse|toxins)\b',
        ]

        # Clickbait patterns
        self.clickbait_patterns = [
            r'^(you (won\'t believe|need to (see|know)))',
            r'^(what happens next will)',
            r'^(doctors hate (him|her|this))',
            r'^(this one (trick|secret|tip))',
            r'^(number \d+ will)',
        ]

    def analyze_claims(self, claim_data: Dict, text: str) -> Dict:
        """
        Analyze extracted claims and text for fact-checking signals.

        Args:
            claim_data: Result from ClaimExtractor
            text: Original full text

        Returns:
            Dict containing fact-check analysis
        """
        claims = claim_data.get('claims', [])

        # Analyze each claim
        analyzed_claims = []
        for claim in claims:
            analysis = self._analyze_single_claim(claim)
            analyzed_claims.append(analysis)

        # Analyze overall text for red flags
        text_analysis = self._analyze_text_patterns(text)

        # Calculate credibility score
        credibility_score = self._calculate_credibility_score(
            analyzed_claims,
            text_analysis,
            claim_data
        )

        # Detect language
        language = self._detect_language(text)

        # Generate flags and warnings
        flags = self._generate_flags(analyzed_claims, text_analysis)

        return {
            'analyzed_claims': analyzed_claims,
            'total_analyzed': len(analyzed_claims),
            'text_analysis': text_analysis,
            'credibility_score': credibility_score,
            'language': language,
            'flags': flags,
            'requires_manual_review': self._requires_manual_review(flags, credibility_score),
            'risk_level': self._assess_risk_level(credibility_score, flags),
            'summary': self._generate_summary(analyzed_claims, text_analysis, credibility_score)
        }

    def _analyze_single_claim(self, claim: Dict) -> Dict:
        """Analyze a single claim for credibility."""
        text = claim['text']
        claim_type = claim['type']

        # Check for red flags in claim
        red_flags = self._check_red_flags(text)

        # Check if claim is verifiable
        verifiable = claim.get('verifiable', False)
        requires_source = claim.get('requires_source', False)

        # Special handling for health claims
        if claim_type == 'health_medical':
            medical_flags = self._check_medical_red_flags(text)
            red_flags['medical_red_flags'] = medical_flags

        # Check for vague sources
        vague_source = claim.get('vague_source', False)

        # Calculate claim credibility
        claim_credibility = self._calculate_claim_credibility(
            claim_type,
            red_flags,
            verifiable,
            vague_source
        )

        return {
            **claim,
            'red_flags': red_flags,
            'claim_credibility': claim_credibility,
            'needs_verification': requires_source or not verifiable,
            'warnings': self._generate_claim_warnings(claim_type, red_flags, vague_source)
        }

    def _check_red_flags(self, text: str) -> Dict:
        """Check text for red flag patterns."""
        flags = {}

        for category, patterns in self.red_flag_patterns.items():
            matches = []
            for pattern in patterns:
                found = re.findall(pattern, text, re.IGNORECASE)
                if found:
                    matches.extend(found)

            if matches:
                flags[category] = {
                    'found': True,
                    'matches': matches,
                    'count': len(matches)
                }

        return flags

    def _check_medical_red_flags(self, text: str) -> List[str]:
        """Check for medical misinformation patterns."""
        flags = []

        for pattern in self.medical_red_flags:
            if re.search(pattern, text, re.IGNORECASE):
                flags.append(pattern)

        return flags

    def _analyze_text_patterns(self, text: str) -> Dict:
        """Analyze overall text for suspicious patterns."""
        # Check for clickbait
        is_clickbait = any(re.search(pattern, text, re.IGNORECASE)
                          for pattern in self.clickbait_patterns)

        # Count all caps words (excluding short ones)
        all_caps_words = re.findall(r'\b[A-Z]{5,}\b', text)
        excessive_caps = len(all_caps_words) > 3

        # Count excessive punctuation
        excessive_exclamation = len(re.findall(r'!{2,}', text))
        excessive_question = len(re.findall(r'\?{2,}', text))

        # Check for "share this" type requests
        share_requests = bool(re.search(
            r'\b(share (this|now)|repost|spread the word|tell everyone|pass (it|this) on)\b',
            text,
            re.IGNORECASE
        ))

        # Count URLs (potential source links)
        url_count = len(re.findall(
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
            text
        ))

        return {
            'is_clickbait': is_clickbait,
            'excessive_caps': excessive_caps,
            'all_caps_count': len(all_caps_words),
            'excessive_punctuation': {
                'exclamation': excessive_exclamation,
                'question': excessive_question
            },
            'share_requests': share_requests,
            'url_count': url_count,
            'has_sources': url_count > 0
        }

    def _calculate_credibility_score(
        self,
        analyzed_claims: List[Dict],
        text_analysis: Dict,
        claim_data: Dict
    ) -> Dict:
        """
        Calculate overall credibility score (0-100).

        Higher score = more credible
        Lower score = less credible
        """
        base_score = 70.0  # Start neutral

        # Penalties
        penalties = []

        # 1. Red flags in claims
        total_red_flags = 0
        for claim in analyzed_claims:
            red_flag_count = len(claim.get('red_flags', {}))
            total_red_flags += red_flag_count

        if total_red_flags > 0:
            penalty = min(total_red_flags * 5, 30)  # Up to -30
            penalties.append({
                'reason': f'{total_red_flags} red flag pattern(s) detected',
                'penalty': penalty
            })

        # 2. Unverifiable claims
        unverifiable_count = sum(1 for c in analyzed_claims if not c.get('verifiable', False))
        if unverifiable_count > 0:
            penalty = min(unverifiable_count * 5, 20)  # Up to -20
            penalties.append({
                'reason': f'{unverifiable_count} unverifiable claim(s)',
                'penalty': penalty
            })

        # 3. Vague sources
        vague_source_count = sum(1 for c in analyzed_claims if c.get('vague_source', False))
        if vague_source_count > 0:
            penalty = min(vague_source_count * 7, 25)  # Up to -25
            penalties.append({
                'reason': f'{vague_source_count} claim(s) with vague sources',
                'penalty': penalty
            })

        # 4. High-risk medical claims
        medical_claims = sum(1 for c in analyzed_claims if c.get('high_risk', False))
        if medical_claims > 0:
            penalty = min(medical_claims * 15, 40)  # Up to -40
            penalties.append({
                'reason': f'{medical_claims} unverified medical claim(s)',
                'penalty': penalty
            })

        # 5. Text pattern penalties
        if text_analysis.get('is_clickbait'):
            penalties.append({'reason': 'Clickbait patterns detected', 'penalty': 15})

        if text_analysis.get('excessive_caps'):
            penalties.append({'reason': 'Excessive capitalization', 'penalty': 10})

        if text_analysis.get('share_requests'):
            penalties.append({'reason': 'Urgency to share/spread', 'penalty': 10})

        if text_analysis['excessive_punctuation']['exclamation'] > 2:
            penalties.append({'reason': 'Excessive exclamation marks', 'penalty': 8})

        # 6. Very high subjectivity
        sentiment = claim_data.get('sentiment', {})
        subjectivity = sentiment.get('subjectivity', 0)
        if subjectivity > 0.7:  # Very subjective text
            penalties.append({
                'reason': f'Highly subjective text ({subjectivity:.2f})',
                'penalty': 12
            })

        # Bonuses
        bonuses = []

        # 1. Includes source URLs
        if text_analysis.get('has_sources'):
            bonuses.append({
                'reason': f'{text_analysis["url_count"]} URL(s) provided',
                'bonus': min(text_analysis["url_count"] * 5, 15)
            })

        # 2. Low subjectivity (more objective)
        if subjectivity < 0.3:
            bonuses.append({
                'reason': 'Objective tone',
                'bonus': 8
            })

        # 3. No red flags at all
        if total_red_flags == 0 and len(analyzed_claims) > 0:
            bonuses.append({
                'reason': 'No red flags detected',
                'bonus': 10
            })

        # Calculate final score
        total_penalty = sum(p['penalty'] for p in penalties)
        total_bonus = sum(b['bonus'] for b in bonuses)

        final_score = base_score - total_penalty + total_bonus
        final_score = max(0, min(100, final_score))  # Clamp 0-100

        return {
            'score': round(final_score, 1),
            'base_score': base_score,
            'penalties': penalties,
            'bonuses': bonuses,
            'total_penalty': total_penalty,
            'total_bonus': total_bonus,
            'interpretation': self._interpret_score(final_score)
        }

    def _calculate_claim_credibility(
        self,
        claim_type: str,
        red_flags: Dict,
        verifiable: bool,
        vague_source: bool
    ) -> float:
        """Calculate credibility score for a single claim (0-1)."""
        base = 0.7

        # Penalties
        if len(red_flags) > 0:
            base -= len(red_flags) * 0.1

        if not verifiable:
            base -= 0.2

        if vague_source:
            base -= 0.15

        if claim_type == 'health_medical':
            # Medical claims need higher standards
            base -= 0.1

        return max(0.0, min(1.0, base))

    def _detect_language(self, text: str) -> str:
        """Detect language of text."""
        try:
            return detect(text)
        except LangDetectException:
            return 'unknown'

    def _generate_flags(self, analyzed_claims: List[Dict], text_analysis: Dict) -> List[str]:
        """Generate list of warning flags."""
        flags = []

        # Claim-based flags
        high_risk_claims = sum(1 for c in analyzed_claims if c.get('high_risk', False))
        if high_risk_claims > 0:
            flags.append(f'MEDICAL_CLAIMS:{high_risk_claims}')

        unverifiable = sum(1 for c in analyzed_claims if not c.get('verifiable', False))
        if unverifiable > 2:
            flags.append(f'MULTIPLE_UNVERIFIABLE:{unverifiable}')

        # Text-based flags
        if text_analysis.get('is_clickbait'):
            flags.append('CLICKBAIT_DETECTED')

        if text_analysis.get('excessive_caps'):
            flags.append('EXCESSIVE_CAPS')

        if text_analysis.get('share_requests'):
            flags.append('VIRAL_PRESSURE')

        # Check for conspiracy indicators in any claim
        conspiracy_detected = any(
            'conspiracy_indicators' in c.get('red_flags', {})
            for c in analyzed_claims
        )
        if conspiracy_detected:
            flags.append('CONSPIRACY_LANGUAGE')

        return flags

    def _requires_manual_review(self, flags: List[str], credibility_score: Dict) -> bool:
        """Determine if post requires human fact-checker review."""
        score = credibility_score['score']

        # Low credibility always needs review
        if score < 40:
            return True

        # Medical claims always need review
        if any('MEDICAL_CLAIMS' in f for f in flags):
            return True

        # Multiple red flags
        if len(flags) >= 3:
            return True

        return False

    def _assess_risk_level(self, credibility_score: Dict, flags: List[str]) -> str:
        """Assess risk level of content."""
        score = credibility_score['score']

        if score < 30 or any('MEDICAL_CLAIMS' in f for f in flags):
            return 'high'
        elif score < 50:
            return 'medium'
        elif score < 70:
            return 'low'
        else:
            return 'very_low'

    def _interpret_score(self, score: float) -> str:
        """Interpret credibility score."""
        if score >= 80:
            return 'Highly credible - Few or no red flags'
        elif score >= 65:
            return 'Generally credible - Minor concerns'
        elif score >= 50:
            return 'Questionable - Multiple red flags detected'
        elif score >= 30:
            return 'Low credibility - Many warning signs'
        else:
            return 'Very low credibility - High risk of misinformation'

    def _generate_summary(
        self,
        analyzed_claims: List[Dict],
        text_analysis: Dict,
        credibility_score: Dict
    ) -> str:
        """Generate human-readable summary."""
        score = credibility_score['score']
        total_claims = len(analyzed_claims)

        summary_parts = []

        # Overall assessment
        summary_parts.append(f"Credibility Score: {score}/100 ({credibility_score['interpretation']})")

        # Claims
        if total_claims > 0:
            summary_parts.append(f"Analyzed {total_claims} claim(s)")

            # High risk claims
            high_risk = sum(1 for c in analyzed_claims if c.get('high_risk', False))
            if high_risk > 0:
                summary_parts.append(f"⚠️ {high_risk} high-risk medical/health claim(s)")

        # Key warnings
        penalties = credibility_score.get('penalties', [])
        if penalties:
            top_penalty = max(penalties, key=lambda p: p['penalty'])
            summary_parts.append(f"Main concern: {top_penalty['reason']}")

        # Positive signals
        if text_analysis.get('has_sources'):
            summary_parts.append(f"✓ Includes {text_analysis['url_count']} source link(s)")

        return ' | '.join(summary_parts)

    def _generate_claim_warnings(
        self,
        claim_type: str,
        red_flags: Dict,
        vague_source: bool
    ) -> List[str]:
        """Generate warnings for a specific claim."""
        warnings = []

        if claim_type == 'health_medical':
            warnings.append('Health/medical claim requires verification')

        if vague_source:
            warnings.append('Source is vague or unspecified')

        for flag_type, flag_data in red_flags.items():
            warnings.append(f'{flag_type.replace("_", " ").title()} detected')

        return warnings


# Singleton instance
fact_checking_service = FactCheckingService()
