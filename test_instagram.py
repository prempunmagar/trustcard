"""
Test script for Instagram integration
"""
import os
from dotenv import load_dotenv
load_dotenv()

from app.services.instagram_service import instagram_service

def test_authentication():
    """Test Instagram authentication"""
    print("\n=== Testing Instagram Authentication ===")

    username = os.getenv("INSTAGRAM_USERNAME")
    password = os.getenv("INSTAGRAM_PASSWORD")

    if not username or not password:
        print("❌ Instagram credentials not set in .env file")
        print("Please add INSTAGRAM_USERNAME and INSTAGRAM_PASSWORD to .env")
        return False

    print(f"Attempting to authenticate as: {username}")
    success = instagram_service.authenticate()

    if success:
        print("✅ Authentication successful!")
        return True
    else:
        print("❌ Authentication failed")
        return False

def test_extract_post():
    """Test extracting a public Instagram post"""
    print("\n=== Testing Post Extraction ===")

    print("\n⚠️  NOTE: You need to provide a real Instagram post URL to test")
    print("Find any public Instagram post and copy its URL\n")

    test_url = input("Enter an Instagram post URL to test (or press Enter to skip): ").strip()

    if not test_url:
        print("Skipping post extraction test")
        return

    print(f"\nExtracting post: {test_url}")
    post_info = instagram_service.get_post_info(test_url)

    if post_info and "error" not in post_info:
        print("\n✅ Post extracted successfully!")
        print(f"   Post ID: {post_info['post_id']}")
        print(f"   Type: {post_info['type']}")
        print(f"   User: @{post_info['user']['username']}")
        print(f"   Caption: {post_info['caption'][:100]}..." if len(post_info['caption']) > 100 else f"   Caption: {post_info['caption']}")
        print(f"   Images: {len(post_info['images'])}")
        print(f"   Videos: {len(post_info['videos'])}")
        print(f"   Likes: {post_info['like_count']}")
        print(f"   Comments: {post_info['comment_count']}")
    else:
        print(f"❌ Failed to extract post: {post_info.get('error', 'Unknown error')}")

def main():
    print("=" * 60)
    print("TrustCard - Instagram Integration Test")
    print("=" * 60)

    # Test authentication
    if not test_authentication():
        print("\n❌ Tests stopped due to authentication failure")
        return

    # Test post extraction
    test_extract_post()

    print("\n" + "=" * 60)
    print("Tests completed!")
    print("=" * 60)

if __name__ == "__main__":
    main()
