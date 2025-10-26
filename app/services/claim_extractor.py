"""
Claim Extraction Service

Identifies factual claims in text using NLP.
"""

import re
import logging
from typing import List, Dict
import spacy
from textblob import TextBlob

logger = logging.getLogger(__name__)


class ClaimExtractor:
    """Extract and classify factual claims from text."""

    def __init__(self):
        self.nlp = None
        self._initialized = False

    def initialize(self):
        """Lazy load spaCy model."""
        if self._initialized:
            return

        try:
            logger.info("Loading spaCy model for claim extraction...")
            self.nlp = spacy.load("en_core_web_sm")
            self._initialized = True
            logger.info("spaCy model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load spaCy model: {e}")
            raise

    def extract_claims(self, text: str) -> Dict:
        """
        Extract all claims from text.

        Args:
            text: Input text to analyze

        Returns:
            Dict containing claims, statistics, and metadata
        """
        if not self._initialized:
            self.initialize()

        if not text or not text.strip():
            return self._empty_result()

        # Process text with spaCy
        doc = self.nlp(text)

        # Extract different types of claims
        all_claims = []

        # 1. Statistical claims (numbers, percentages, etc.)
        statistical_claims = self._extract_statistical_claims(doc)
        all_claims.extend(statistical_claims)

        # 2. Health/medical claims
        health_claims = self._extract_health_claims(doc)
        all_claims.extend(health_claims)

        # 3. Factual statements (declarative sentences)
        factual_claims = self._extract_factual_statements(doc)
        all_claims.extend(factual_claims)

        # 4. Expert/authority claims
        authority_claims = self._extract_authority_claims(doc)
        all_claims.extend(authority_claims)

        # Remove duplicates while preserving order
        unique_claims = []
        seen = set()
        for claim in all_claims:
            claim_text = claim['text'].lower().strip()
            if claim_text not in seen:
                seen.add(claim_text)
                unique_claims.append(claim)

        # Get sentiment for overall text
        blob = TextBlob(text)
        sentiment = {
            'polarity': blob.sentiment.polarity,  # -1 to 1
            'subjectivity': blob.sentiment.subjectivity  # 0 to 1
        }

        return {
            'claims': unique_claims,
            'total_claims': len(unique_claims),
            'claim_types': self._count_claim_types(unique_claims),
            'sentiment': sentiment,
            'has_claims': len(unique_claims) > 0,
            'text_length': len(text),
            'sentence_count': len(list(doc.sents))
        }

    def _extract_statistical_claims(self, doc) -> List[Dict]:
        """Extract claims containing statistics or numbers."""
        claims = []

        # Patterns indicating statistical claims
        stat_patterns = [
            r'\d+%',  # Percentages
            r'\d+\s*(million|billion|thousand|hundred)',  # Large numbers
            r'\d+\s*in\s*\d+',  # Ratios (1 in 5)
            r'\d+x',  # Multipliers (10x more)
            r'\d+\s*(times|fold)',  # Times/fold
        ]

        for sent in doc.sents:
            sent_text = sent.text.strip()

            # Check if sentence contains statistical patterns
            has_stat = any(re.search(pattern, sent_text, re.IGNORECASE)
                          for pattern in stat_patterns)

            if has_stat:
                claims.append({
                    'text': sent_text,
                    'type': 'statistical',
                    'confidence': 0.8,
                    'verifiable': True,
                    'requires_source': True
                })

        return claims

    def _extract_health_claims(self, doc) -> List[Dict]:
        """Extract health and medical claims."""
        claims = []

        # Health-related keywords
        health_keywords = {
            'cure', 'cures', 'treat', 'treats', 'prevent', 'prevents',
            'heal', 'heals', 'remedy', 'remedies', 'vaccine', 'vaccines',
            'drug', 'drugs', 'medication', 'medicine', 'therapy',
            'disease', 'diseases', 'illness', 'cancer', 'covid', 'virus',
            'infection', 'immune', 'immunity', 'health', 'healthy',
            'diagnosis', 'symptom', 'symptoms', 'side effect', 'toxin',
            'detox', 'cleanse', 'boost', 'strengthen'
        }

        for sent in doc.sents:
            sent_text = sent.text.strip()
            sent_lower = sent_text.lower()

            # Check if sentence contains health keywords
            has_health_keyword = any(keyword in sent_lower
                                    for keyword in health_keywords)

            if has_health_keyword:
                # Higher confidence for medical claims (more critical)
                claims.append({
                    'text': sent_text,
                    'type': 'health_medical',
                    'confidence': 0.85,
                    'verifiable': True,
                    'requires_source': True,
                    'high_risk': True  # Medical misinformation is dangerous
                })

        return claims

    def _extract_factual_statements(self, doc) -> List[Dict]:
        """Extract declarative factual statements."""
        claims = []

        # Verbs that indicate factual claims
        factual_verbs = {'is', 'are', 'was', 'were', 'has', 'have', 'had',
                        'contains', 'contain', 'causes', 'cause', 'shows', 'show',
                        'proves', 'prove', 'demonstrates', 'demonstrate',
                        'reveals', 'reveal', 'confirms', 'confirm'}

        # Event verbs that indicate historical/news claims
        event_verbs = {'found', 'discovered', 'stolen', 'shattered', 'broken',
                      'destroyed', 'lost', 'recovered', 'seized', 'occurred',
                      'happened', 'took', 'died', 'killed', 'announced',
                      'reported', 'revealed', 'confirmed', 'declared',
                      'arrested', 'caught', 'escaped', 'attacked', 'invaded'}

        for sent in doc.sents:
            sent_text = sent.text.strip()

            # Skip very short sentences (reduced from 5 to 3 words)
            if len(sent_text.split()) < 3:
                continue

            # Skip questions
            if sent_text.endswith('?'):
                continue

            # Check for factual verbs
            tokens = [token.lemma_.lower() for token in sent]
            has_factual_verb = any(verb in tokens for verb in factual_verbs)
            has_event_verb = any(verb in tokens for verb in event_verbs)

            # Check for proper nouns (entities) - factual claims often reference entities
            has_entities = len(sent.ents) > 0

            # Check for dates, numbers, or locations (strong indicators of factual claims)
            has_temporal = any(ent.label_ in ['DATE', 'TIME', 'CARDINAL', 'GPE', 'LOC'] for ent in sent.ents)

            # Accept claims if they have:
            # 1. Factual verb AND entities
            # 2. Event verb (even without entities - events are inherently factual)
            # 3. Temporal/location info with any verb
            if (has_factual_verb and has_entities) or has_event_verb or has_temporal:
                claims.append({
                    'text': sent_text,
                    'type': 'factual',
                    'confidence': 0.7,
                    'verifiable': True,
                    'requires_source': False
                })

        return claims

    def _extract_authority_claims(self, doc) -> List[Dict]:
        """Extract claims citing authorities or experts."""
        claims = []

        # Authority patterns
        authority_patterns = [
            r'(doctor|dr\.|scientist|researcher|expert|study|studies|research)s?\s+(say|says|said|show|shows|showed|found|report|reports|reported)',
            r'according to\s+(a|an|the)?\s*(doctor|scientist|expert|study|research)',
            r'(studies|research|evidence)\s+(show|shows|suggest|suggests|prove|proves)',
        ]

        for sent in doc.sents:
            sent_text = sent.text.strip()
            sent_lower = sent_text.lower()

            # Check for authority patterns
            has_authority = any(re.search(pattern, sent_lower, re.IGNORECASE)
                              for pattern in authority_patterns)

            if has_authority:
                # Check if specific source is mentioned
                has_specific_source = bool(re.search(r'(university|journal|institution|organization)',
                                                     sent_lower))

                claims.append({
                    'text': sent_text,
                    'type': 'authority_citation',
                    'confidence': 0.75,
                    'verifiable': has_specific_source,
                    'requires_source': True,
                    'vague_source': not has_specific_source
                })

        return claims

    def _count_claim_types(self, claims: List[Dict]) -> Dict:
        """Count claims by type."""
        counts = {}
        for claim in claims:
            claim_type = claim['type']
            counts[claim_type] = counts.get(claim_type, 0) + 1
        return counts

    def _empty_result(self) -> Dict:
        """Return empty result structure."""
        return {
            'claims': [],
            'total_claims': 0,
            'claim_types': {},
            'sentiment': {'polarity': 0.0, 'subjectivity': 0.0},
            'has_claims': False,
            'text_length': 0,
            'sentence_count': 0
        }


# Singleton instance
claim_extractor = ClaimExtractor()
