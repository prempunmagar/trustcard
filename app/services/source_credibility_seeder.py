"""
Source Credibility Database Seeder

Seeds the database with known publishers and their credibility ratings.
Data based on Media Bias/Fact Check, AllSides, NewsGuard, and Ad Fontes Media.
"""

from sqlalchemy.orm import Session
from datetime import datetime
import logging

from app.models.source_credibility import SourceCredibility

logger = logging.getLogger(__name__)


class SourceCredibilitySeeder:
    """Seed source credibility database with known publishers."""

    # Known sources with ratings
    # Format: domain -> (bias, reliability, description)
    SOURCES = {
        # High Reliability - Left Bias
        "cnn.com": ("left", "high", "CNN - Cable news, left-center bias, mostly factual"),
        "nytimes.com": ("left-center", "very-high", "New York Times - High factual reporting, slight left bias"),
        "washingtonpost.com": ("left-center", "high", "Washington Post - Quality journalism, left-center"),
        "theguardian.com": ("left", "high", "The Guardian - UK publication, left bias, factual"),
        "npr.org": ("left-center", "very-high", "NPR - Public radio, minimal bias, very reliable"),
        "msnbc.com": ("left", "mixed", "MSNBC - Cable news, left bias, mixed factual record"),
        "vox.com": ("left", "high", "Vox - Explanatory journalism, left bias, mostly factual"),
        "motherjones.com": ("left", "high", "Mother Jones - Investigative journalism, left bias"),
        "thedailybeast.com": ("left", "mixed", "The Daily Beast - Left bias, mixed factual reporting"),
        "salon.com": ("left", "mixed", "Salon - Left bias, mixed reliability"),

        # High Reliability - Right Bias
        "wsj.com": ("right-center", "high", "Wall Street Journal - Right-center bias, factual reporting"),
        "economist.com": ("right-center", "very-high", "The Economist - Right-center, excellent factual record"),
        "nationalreview.com": ("right", "high", "National Review - Conservative magazine, mostly factual"),
        "weeklystandard.com": ("right", "high", "Weekly Standard - Conservative, factual reporting"),
        "reason.com": ("right-center", "high", "Reason - Libertarian perspective, factual"),

        # High Reliability - Center
        "reuters.com": ("center", "very-high", "Reuters - News agency, minimal bias, very factual"),
        "apnews.com": ("center", "very-high", "Associated Press - Minimal bias, very reliable"),
        "bbc.com": ("center", "high", "BBC - British public broadcaster, mostly factual"),
        "pbs.org": ("center", "very-high", "PBS - Public broadcasting, minimal bias"),
        "csmonitor.com": ("center", "very-high", "Christian Science Monitor - Nonpartisan, highly factual"),
        "thehill.com": ("center", "high", "The Hill - Political news, minimal bias"),
        "axios.com": ("center", "high", "Axios - News startup, minimal bias, factual"),
        "usatoday.com": ("center", "high", "USA Today - General news, minimal bias"),

        # Mixed Reliability
        "foxnews.com": ("right", "mixed", "Fox News - Right bias, mixed factual reporting"),
        "nypost.com": ("right", "mixed", "New York Post - Tabloid, right bias, mixed reliability"),
        "buzzfeed.com": ("left", "mixed", "BuzzFeed - Left bias, mixed reporting quality"),
        "buzzfeednews.com": ("left-center", "high", "BuzzFeed News - Separate news division, better factual record"),
        "huffpost.com": ("left", "mixed", "HuffPost - Left bias, mixed factual record"),
        "dailymail.co.uk": ("right", "low", "Daily Mail - UK tabloid, right bias, poor factual record"),
        "breitbart.com": ("extreme-right", "mixed", "Breitbart - Far-right bias, mixed factual reporting"),
        "theblaze.com": ("right", "mixed", "The Blaze - Conservative media, mixed reliability"),
        "dailycaller.com": ("right", "mixed", "Daily Caller - Conservative news, mixed factual record"),
        "thefederalist.com": ("right", "mixed", "The Federalist - Conservative, mixed reliability"),

        # Low Reliability - Conspiracy/Questionable
        "infowars.com": ("extreme-right", "very-low", "InfoWars - Conspiracy theories, very unreliable"),
        "naturalnews.com": ("extreme-right", "very-low", "Natural News - Pseudoscience, conspiracy theories"),
        "beforeitsnews.com": ("extreme-right", "very-low", "Before It's News - Conspiracy content"),
        "zerohedge.com": ("right", "low", "Zero Hedge - Conspiracy-prone, poor sourcing"),
        "globalresearch.ca": ("extreme-left", "very-low", "Global Research - Conspiracy theories, unreliable"),
        "activistpost.com": ("extreme-right", "very-low", "Activist Post - Conspiracy content"),
        "veteranstoday.com": ("extreme-right", "very-low", "Veterans Today - Conspiracy theories"),
        "yournewswire.com": ("extreme-right", "very-low", "YourNewsWire - Fake news, conspiracy theories"),
        "neonnettle.com": ("extreme-right", "very-low", "Neon Nettle - Conspiracy theories, clickbait"),

        # Satire (special category)
        "theonion.com": ("satire", "satire", "The Onion - Satirical news, not intended as factual"),
        "babylonbee.com": ("satire", "satire", "Babylon Bee - Conservative satire"),
        "clickhole.com": ("satire", "satire", "ClickHole - Satirical clickbait parody"),
        "thehardtimes.net": ("satire", "satire", "The Hard Times - Punk rock satire"),

        # Fact-Checking Sites (high reliability)
        "snopes.com": ("center", "very-high", "Snopes - Fact-checking site, very reliable"),
        "factcheck.org": ("center", "very-high", "FactCheck.org - Nonpartisan fact-checking"),
        "politifact.com": ("center", "high", "PolitiFact - Fact-checking, mostly reliable"),
        "fullfact.org": ("center", "very-high", "Full Fact - UK fact-checking charity"),
        "mediabiasfactcheck.com": ("center", "high", "Media Bias/Fact Check - Source credibility ratings"),

        # Science/Academic/Government
        "nature.com": ("center", "very-high", "Nature - Peer-reviewed scientific journal"),
        "sciencemag.org": ("center", "very-high", "Science Magazine - Peer-reviewed research"),
        "nejm.org": ("center", "very-high", "New England Journal of Medicine - Medical research"),
        "thelancet.com": ("center", "very-high", "The Lancet - Medical journal"),
        "nih.gov": ("center", "very-high", "NIH - National Institutes of Health"),
        "cdc.gov": ("center", "very-high", "CDC - Centers for Disease Control"),
        "fda.gov": ("center", "very-high", "FDA - Food and Drug Administration"),
        "who.int": ("center", "very-high", "WHO - World Health Organization"),
        "nasa.gov": ("center", "very-high", "NASA - National Aeronautics and Space Administration"),
        "noaa.gov": ("center", "very-high", "NOAA - National Oceanic and Atmospheric Administration"),

        # Social Media (lower reliability by default - user-generated content)
        "instagram.com": ("varies", "low", "Instagram - User-generated content, verify independently"),
        "twitter.com": ("varies", "low", "Twitter/X - User-generated content, verify claims"),
        "x.com": ("varies", "low", "X (formerly Twitter) - User-generated content, verify claims"),
        "facebook.com": ("varies", "low", "Facebook - User-generated content, mixed reliability"),
        "tiktok.com": ("varies", "low", "TikTok - User content, entertainment focused"),
        "youtube.com": ("varies", "low", "YouTube - User-generated video content, verify claims"),
        "reddit.com": ("varies", "low", "Reddit - User discussion forum, verify claims"),

        # Wikipedia (special case - crowdsourced but generally reliable)
        "wikipedia.org": ("center", "high", "Wikipedia - Crowdsourced encyclopedia, generally reliable but verify for important claims"),
    }

    def seed_database(self, db: Session, update_existing: bool = False) -> int:
        """
        Seed database with known sources.

        Args:
            db: Database session
            update_existing: Whether to update existing records

        Returns:
            int: Number of sources added/updated
        """
        count = 0

        for domain, (bias, reliability, description) in self.SOURCES.items():
            existing = db.query(SourceCredibility).filter(
                SourceCredibility.domain == domain
            ).first()

            if existing:
                if update_existing:
                    existing.bias_rating = bias
                    existing.reliability_rating = reliability
                    existing.description = description
                    existing.last_updated = datetime.utcnow()
                    count += 1
                    logger.info(f"Updated: {domain}")
            else:
                source = SourceCredibility(
                    domain=domain,
                    bias_rating=bias,
                    reliability_rating=reliability,
                    description=description,
                    last_updated=datetime.utcnow()
                )
                db.add(source)
                count += 1
                logger.info(f"Added: {domain}")

        db.commit()
        logger.info(f"✅ Seeded {count} sources into database")

        return count

    def add_source(
        self,
        db: Session,
        domain: str,
        bias: str,
        reliability: str,
        description: str
    ) -> None:
        """
        Add or update a single source.

        Args:
            db: Database session
            domain: Domain name
            bias: Bias rating
            reliability: Reliability rating
            description: Source description
        """
        existing = db.query(SourceCredibility).filter(
            SourceCredibility.domain == domain
        ).first()

        if existing:
            existing.bias_rating = bias
            existing.reliability_rating = reliability
            existing.description = description
            existing.last_updated = datetime.utcnow()
        else:
            source = SourceCredibility(
                domain=domain,
                bias_rating=bias,
                reliability_rating=reliability,
                description=description,
                last_updated=datetime.utcnow()
            )
            db.add(source)

        db.commit()
        logger.info(f"✅ Added/updated source: {domain}")

    def get_stats(self, db: Session) -> dict:
        """Get statistics about seeded sources."""
        all_sources = db.query(SourceCredibility).all()

        bias_counts = {}
        reliability_counts = {}

        for source in all_sources:
            bias_counts[source.bias_rating] = bias_counts.get(source.bias_rating, 0) + 1
            reliability_counts[source.reliability_rating] = reliability_counts.get(source.reliability_rating, 0) + 1

        return {
            "total_sources": len(all_sources),
            "bias_distribution": bias_counts,
            "reliability_distribution": reliability_counts
        }


# Singleton instance
source_seeder = SourceCredibilitySeeder()
