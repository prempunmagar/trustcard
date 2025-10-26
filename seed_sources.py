"""
Seed the Source Credibility Database

Run this script to populate the database with known publishers and their credibility ratings.
"""

import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.database import get_db_context
from app.services.source_credibility_seeder import source_seeder


def main():
    """Seed source credibility database."""
    print("=" * 70)
    print("🌱 SEEDING SOURCE CREDIBILITY DATABASE")
    print("=" * 70)
    print()
    print("This will populate the database with known publishers")
    print("including news outlets, fact-checkers, and government sources.")
    print()

    with get_db_context() as db:
        # Seed database (update existing records)
        count = source_seeder.seed_database(db, update_existing=True)

        # Get statistics
        stats = source_seeder.get_stats(db)

    print()
    print("=" * 70)
    print(f"✅ SUCCESS - Seeded {count} sources")
    print("=" * 70)
    print()
    print(f"📊 Database Statistics:")
    print(f"   Total sources: {stats['total_sources']}")
    print()
    print(f"   Reliability Distribution:")
    for reliability, count in sorted(stats['reliability_distribution'].items()):
        print(f"      {reliability}: {count}")
    print()
    print(f"   Bias Distribution:")
    for bias, count in sorted(stats['bias_distribution'].items()):
        print(f"      {bias}: {count}")
    print()
    print("=" * 70)


if __name__ == "__main__":
    main()
