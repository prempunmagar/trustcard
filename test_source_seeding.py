"""
Test Source Credibility Seeding

This script tests seeding the source credibility database.
"""

import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.database import get_db_context
from app.services.source_credibility_seeder import source_seeder
from app.models.source_credibility import SourceCredibility


def test_seeding():
    """Test seeding source credibility database."""

    print("=" * 70)
    print("🌱 SOURCE CREDIBILITY SEEDING TEST")
    print("=" * 70)
    print()

    # Seed database
    print("📥 Seeding database...")
    with get_db_context() as db:
        count = source_seeder.seed_database(db, update_existing=True)

    print(f"✅ Seeded {count} sources")
    print()

    # Get statistics
    print("📊 Database Statistics:")
    with get_db_context() as db:
        stats = source_seeder.get_stats(db)

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

    # Query and display some examples
    print("📋 Sample Sources:")
    print()

    with get_db_context() as db:
        # Get examples from different categories
        sources = db.query(SourceCredibility).limit(15).all()

        for source in sources:
            print(f"   {source.domain}")
            print(f"      Bias: {source.bias_rating}")
            print(f"      Reliability: {source.reliability_rating}")
            print(f"      {source.description[:70]}...")
            print()

    print("=" * 70)
    print("✅ SEEDING TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    test_seeding()
