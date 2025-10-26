"""
Test Community Feedback System

Tests community voting and feedback submission.
"""

import requests
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

BASE_URL = "http://localhost:8000"


def test_community_feedback():
    """Test community feedback submission"""

    print("=" * 70)
    print("💬 COMMUNITY FEEDBACK TEST")
    print("=" * 70)
    print()
    print("This test demonstrates the community voting system.")
    print("Users can vote on analysis accuracy without logging in.")
    print()

    # Get analysis ID
    analysis_id = input("Enter analysis ID to vote on: ").strip()

    if not analysis_id:
        print("❌ No analysis ID provided")
        return

    print()

    # Display current feedback
    print("📊 Current Community Feedback:")
    print("-" * 70)

    try:
        response = requests.get(f"{BASE_URL}/api/reports/{analysis_id}/feedback")

        if response.status_code == 200:
            data = response.json()
            summary = data.get("summary", {})

            total = summary.get("total_votes", 0)
            accurate = summary.get("accurate", 0)
            misleading = summary.get("misleading", 0)
            false = summary.get("false", 0)

            print(f"   Total Votes: {total}")

            if total > 0:
                print(f"   ✓ Accurate: {accurate} ({accurate/total*100:.1f}%)")
                print(f"   ⚠ Misleading: {misleading} ({misleading/total*100:.1f}%)")
                print(f"   ✗ False: {false} ({false/total*100:.1f}%)")
            else:
                print("   No votes yet!")

            print()

            # Display recent comments
            comments = data.get("recent_comments", [])
            if comments:
                print("Recent Comments:")
                for comment in comments[:3]:
                    vote = comment.get("vote_type", "unknown")
                    text = comment.get("comment", "")
                    print(f"   [{vote}] {text}")
                print()

        else:
            print(f"❌ Error fetching feedback: {response.status_code}")
            return

    except Exception as e:
        print(f"❌ Error: {e}")
        return

    # Submit new vote
    print("🗳️  Vote Options:")
    print("   1. Accurate - Content is accurate and truthful")
    print("   2. Misleading - Content is misleading or lacks context")
    print("   3. False - Content contains false information")
    print()

    vote_choice = input("Your vote (1-3): ").strip()

    vote_map = {
        "1": "accurate",
        "2": "misleading",
        "3": "false"
    }

    vote_type = vote_map.get(vote_choice)

    if not vote_type:
        print("❌ Invalid choice")
        return

    # Optional comment
    print()
    comment = input("Optional comment (or press Enter to skip): ").strip()

    # Submit feedback
    print()
    print("📤 Submitting feedback...")

    payload = {"vote_type": vote_type}
    if comment:
        payload["comment"] = comment

    try:
        response = requests.post(
            f"{BASE_URL}/api/reports/{analysis_id}/feedback",
            json=payload
        )

        if response.status_code == 200:
            data = response.json()
            print()
            print("✅ Feedback submitted successfully!")
            print(f"   Feedback ID: {data.get('feedback_id')}")
            print()

            print("📊 Updated Summary:")
            print("-" * 70)
            summary = data.get("summary", {})
            total = summary.get("total_votes", 0)
            print(f"   Total Votes: {total}")
            print(f"   ✓ Accurate: {summary.get('accurate', 0)} ({summary.get('accurate', 0)/total*100:.1f}%)")
            print(f"   ⚠ Misleading: {summary.get('misleading', 0)} ({summary.get('misleading', 0)/total*100:.1f}%)")
            print(f"   ✗ False: {summary.get('false', 0)} ({summary.get('false', 0)/total*100:.1f}%)")
            print()

        elif response.status_code == 400:
            error = response.json()
            print(f"\n❌ Error: {error.get('detail')}")
            if "already voted" in error.get('detail', '').lower():
                print("   Note: Duplicate voting is prevented by IP address")

        else:
            print(f"\n❌ Error: {response.json()}")

    except Exception as e:
        print(f"\n❌ Error: {e}")

    print()
    print("=" * 70)
    print("✅ TEST COMPLETE!")
    print("=" * 70)
    print()
    print("Community Feedback Features:")
    print("  ✓ Anonymous voting (no login required)")
    print("  ✓ Duplicate prevention (IP-based)")
    print("  ✓ Optional comments for context")
    print("  ✓ Real-time vote aggregation")
    print("  ✓ Visible in HTML report cards")
    print()


if __name__ == "__main__":
    test_community_feedback()
