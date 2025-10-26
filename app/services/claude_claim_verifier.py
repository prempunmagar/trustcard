"""
Claude-powered Claim Verification Service

Uses web search and Claude AI to verify factual claims against official sources.
"""

import os
import logging
import json
import requests
from typing import Dict, List, Optional
from anthropic import Anthropic

logger = logging.getLogger(__name__)


class ClaudeClaimVerifier:
    """Verify claims using web search and Claude analysis"""

    def __init__(self):
        self._client = None
        self.serper_api_key = os.getenv("SERPER_API_KEY")  # Google Search API

    @property
    def client(self):
        """Lazy load Anthropic client"""
        if self._client is None:
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY environment variable is required")
            self._client = Anthropic(api_key=api_key)
        return self._client

    def verify_claims(self, claims: List[Dict], post_context: str = "") -> Dict:
        """
        Verify a list of claims using web search and Claude analysis.

        Args:
            claims: List of claim dicts with 'text' field
            post_context: Additional context about the post

        Returns:
            Dict with verification results for each claim
        """
        try:
            if not claims:
                return {
                    "status": "no_claims",
                    "verified_claims": [],
                    "summary": "No claims to verify"
                }

            verified_claims = []

            for claim in claims[:3]:  # Limit to top 3 claims to save API calls
                claim_text = claim.get("text", "")

                if not claim_text:
                    continue

                # Search for information about the claim
                search_results = self._search_web(claim_text)

                # Have Claude analyze the search results
                verification = self._analyze_with_claude(
                    claim_text=claim_text,
                    search_results=search_results,
                    post_context=post_context
                )

                verified_claims.append({
                    "claim": claim_text,
                    "verification": verification,
                    "sources_checked": len(search_results)
                })

            # Generate overall summary
            summary = self._generate_summary(verified_claims)

            return {
                "status": "completed",
                "verified_claims": verified_claims,
                "total_verified": len(verified_claims),
                "summary": summary
            }

        except Exception as e:
            logger.error(f"Claim verification failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "verified_claims": []
            }

    def _search_web(self, query: str) -> List[Dict]:
        """
        Search the web for information about a claim.

        Args:
            query: Search query

        Returns:
            List of search results
        """
        try:
            if not self.serper_api_key:
                # Fallback: return empty results if no search API
                logger.warning("No SERPER_API_KEY configured, skipping web search")
                return []

            # Use Serper.dev Google Search API
            url = "https://google.serper.dev/search"
            headers = {
                "X-API-KEY": self.serper_api_key,
                "Content-Type": "application/json"
            }

            # Focus on news sources
            payload = {
                "q": query,
                "num": 5,
                "type": "news"
            }

            response = requests.post(url, headers=headers, json=payload, timeout=10)
            response.raise_for_status()

            data = response.json()

            # Extract relevant results
            results = []
            for item in data.get("news", [])[:5]:
                results.append({
                    "title": item.get("title", ""),
                    "snippet": item.get("snippet", ""),
                    "link": item.get("link", ""),
                    "source": item.get("source", ""),
                    "date": item.get("date", "")
                })

            return results

        except Exception as e:
            logger.error(f"Web search failed: {e}")
            return []

    def _analyze_with_claude(self, claim_text: str, search_results: List[Dict],
                            post_context: str = "") -> Dict:
        """
        Use Claude to analyze claim against search results.

        Args:
            claim_text: The claim to verify
            search_results: Web search results
            post_context: Additional context

        Returns:
            Dict with verification result
        """
        try:
            # Build context from search results
            search_context = "\n\n".join([
                f"Source: {r['source']} ({r.get('date', 'unknown date')})\n"
                f"Title: {r['title']}\n"
                f"Snippet: {r['snippet']}\n"
                f"URL: {r['link']}"
                for r in search_results[:5]
            ]) if search_results else "No web search results available."

            prompt = f"""Analyze this claim and verify it against official news sources.

CLAIM TO VERIFY:
{claim_text}

POST CONTEXT:
{post_context}

WEB SEARCH RESULTS FROM NEWS SOURCES:
{search_context}

Your task:
1. Determine if the claim is TRUE, FALSE, UNVERIFIED, or MISLEADING based on the search results
2. Explain your reasoning with specific references to sources
3. Note any official confirmations or denials
4. Identify which sources are most credible (official news organizations, government sources, etc.)

Respond in JSON format:
{{
    "verdict": "TRUE|FALSE|UNVERIFIED|MISLEADING",
    "confidence": 0.0-1.0,
    "reasoning": "Detailed explanation with source references",
    "supporting_sources": ["list of URLs that support your verdict"],
    "contradicting_sources": ["list of URLs that contradict the claim"],
    "official_sources_found": true/false,
    "recommendation": "What users should do with this information"
}}

Focus on official, credible sources. Be skeptical of claims without verification."""

            message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1500,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            response_text = message.content[0].text

            # Extract JSON from response
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1

            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                result = json.loads(json_str)
                return result
            else:
                # Fallback if JSON not found
                return {
                    "verdict": "UNVERIFIED",
                    "confidence": 0.3,
                    "reasoning": "Could not parse verification result",
                    "supporting_sources": [],
                    "contradicting_sources": [],
                    "official_sources_found": False,
                    "recommendation": "Verify through official sources"
                }

        except Exception as e:
            logger.error(f"Claude analysis failed: {e}")
            return {
                "verdict": "ERROR",
                "confidence": 0.0,
                "reasoning": f"Verification failed: {str(e)}",
                "supporting_sources": [],
                "contradicting_sources": [],
                "official_sources_found": False,
                "recommendation": "Manual verification required"
            }

    def _generate_summary(self, verified_claims: List[Dict]) -> str:
        """Generate a summary of all verification results"""
        if not verified_claims:
            return "No claims were verified"

        verdicts = [c["verification"]["verdict"] for c in verified_claims]

        false_count = verdicts.count("FALSE")
        misleading_count = verdicts.count("MISLEADING")
        unverified_count = verdicts.count("UNVERIFIED")
        true_count = verdicts.count("TRUE")

        if false_count > 0:
            return f"⚠️ {false_count} claim(s) found to be FALSE based on official sources"
        elif misleading_count > 0:
            return f"⚠️ {misleading_count} claim(s) found to be MISLEADING"
        elif unverified_count > 0:
            return f"❓ {unverified_count} claim(s) could not be verified through official sources"
        elif true_count > 0:
            return f"✅ {true_count} claim(s) verified as TRUE"
        else:
            return "Verification completed"


# Singleton instance
claude_claim_verifier = ClaudeClaimVerifier()
