"""
Test full analysis pipeline with Instagram integration
"""
from app.database import get_db_context
from app.services.crud_analysis import crud_analysis
from app.tasks.analysis_tasks import process_instagram_post

def test_full_analysis():
    """Test creating analysis and processing with Instagram extraction"""

    # Get Instagram URL from user
    url = input("Enter Instagram post URL to analyze: ").strip()

    if not url:
        print("No URL provided")
        return

    # Extract post ID
    from app.services.instagram_service import instagram_service
    post_id = instagram_service.extract_post_id(url)

    if not post_id:
        print("❌ Invalid Instagram URL")
        return

    print(f"\n📊 Creating analysis for post: {post_id}")

    # Create analysis record
    with get_db_context() as db:
        analysis = crud_analysis.create(
            db=db,
            instagram_url=url,
            post_id=post_id
        )
        print(f"✅ Analysis created: {analysis.id}")

    # Submit to Celery
    print("\n⚙️  Submitting to task queue...")
    task = process_instagram_post.delay(str(analysis.id))
    print(f"✅ Task submitted: {task.id}")

    print("\n⏳ Waiting for analysis to complete...")
    result = task.get(timeout=60)

    print("\n📋 Analysis Results:")
    print(f"   Status: {result['status']}")
    print(f"   Trust Score: {result.get('trust_score', 'N/A')}")
    print(f"   Post Type: {result.get('post_type', 'N/A')}")

    # Check database
    with get_db_context() as db:
        updated = crud_analysis.get_by_id(db, analysis.id)
        print(f"\n📊 Database Record:")
        print(f"   Status: {updated.status}")
        print(f"   Trust Score: {updated.trust_score}")
        print(f"   Content Type: {updated.content['type'] if updated.content else 'N/A'}")
        print(f"   Images: {len(updated.content['images']) if updated.content else 0}")
        print(f"   Videos: {len(updated.content['videos']) if updated.content else 0}")

if __name__ == "__main__":
    test_full_analysis()
