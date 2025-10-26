"""
Instagram content extraction service using Instagrapi
"""
from instagrapi import Client
from instagrapi.exceptions import (
    LoginRequired,
    PleaseWaitFewMinutes,
    RateLimitError,
    MediaNotFound,
    PrivateError
)
from typing import Dict, List, Optional
import os
import time
import logging
from pathlib import Path

from app.config import settings

logger = logging.getLogger(__name__)

class InstagramService:
    """Service for extracting Instagram content"""

    def __init__(self):
        self.client = Client()
        self.client.delay_range = [1, 3]  # Random delay between requests
        self.session_file = "instagram_session.json"
        self._authenticated = False

    def authenticate(self, username: Optional[str] = None, password: Optional[str] = None) -> bool:
        """
        Authenticate with Instagram

        Args:
            username: Instagram username (optional, reads from env if not provided)
            password: Instagram password (optional, reads from env if not provided)

        Returns:
            bool: True if authentication successful
        """
        username = username or settings.INSTAGRAM_USERNAME
        password = password or settings.INSTAGRAM_PASSWORD

        if not username or not password:
            logger.error("Instagram credentials not provided")
            return False

        try:
            # Try to load existing session
            if os.path.exists(self.session_file):
                logger.info("Loading existing Instagram session...")
                self.client.load_settings(self.session_file)
                self.client.login(username, password)
                logger.info("✅ Loaded existing session successfully")
                self._authenticated = True
                return True
        except Exception as e:
            logger.warning(f"Could not load existing session: {e}")

        try:
            # Fresh login
            logger.info("Performing fresh Instagram login...")
            self.client.login(username, password)

            # Save session for reuse
            self.client.dump_settings(self.session_file)
            logger.info("✅ Instagram login successful, session saved")
            self._authenticated = True
            return True

        except LoginRequired:
            logger.error("❌ Instagram login failed: Invalid credentials")
            return False
        except PleaseWaitFewMinutes:
            logger.error("❌ Instagram rate limit: Please wait before retrying")
            return False
        except Exception as e:
            logger.error(f"❌ Instagram login error: {e}")
            return False

    def extract_post_id(self, url: str) -> Optional[str]:
        """
        Extract post ID from Instagram URL

        Args:
            url: Instagram post URL (various formats supported)

        Returns:
            str: Post shortcode/ID or None if invalid
        """
        try:
            # Handle various URL formats
            # https://instagram.com/p/ABC123/
            # https://www.instagram.com/p/ABC123/
            # https://instagram.com/reel/ABC123/
            # https://www.instagram.com/reel/ABC123/

            if "/p/" in url or "/reel/" in url or "/tv/" in url:
                parts = url.split("/")
                for i, part in enumerate(parts):
                    if part in ["p", "reel", "tv"] and i + 1 < len(parts):
                        return parts[i + 1].strip("/").split("?")[0]

            logger.error(f"Could not extract post ID from URL: {url}")
            return None

        except Exception as e:
            logger.error(f"Error extracting post ID: {e}")
            return None

    def get_post_info(self, url: str, retry_count: int = 3) -> Optional[Dict]:
        """
        Extract comprehensive information from Instagram post

        Args:
            url: Instagram post URL
            retry_count: Number of retries on failure

        Returns:
            dict: Post information or None if failed
        """
        if not self._authenticated:
            logger.error("Not authenticated with Instagram")
            return None

        post_id = self.extract_post_id(url)
        if not post_id:
            return {"error": "Invalid Instagram URL"}

        for attempt in range(retry_count):
            try:
                logger.info(f"Fetching Instagram post: {post_id} (attempt {attempt + 1})")

                # Get media info using instagrapi
                # First convert shortcode to media_pk
                media_pk = self.client.media_pk_from_code(post_id)
                media = self.client.media_info(media_pk)

                # Extract basic info
                post_info = {
                    "post_id": post_id,
                    "url": url,
                    "type": self._get_media_type(media),
                    "caption": media.caption_text or "",
                    "images": [],
                    "videos": [],
                    "user": {
                        "username": getattr(media.user, 'username', 'unknown'),
                        "full_name": getattr(media.user, 'full_name', ''),
                        "is_verified": getattr(media.user, 'is_verified', False),
                        "profile_pic_url": str(media.user.profile_pic_url) if hasattr(media.user, 'profile_pic_url') and media.user.profile_pic_url else None
                    },
                    "timestamp": media.taken_at.isoformat() if hasattr(media, 'taken_at') and media.taken_at else None,
                    "like_count": getattr(media, 'like_count', 0),
                    "comment_count": getattr(media, 'comment_count', 0),
                    "location": media.location.name if hasattr(media, 'location') and media.location else None,
                    "is_video": media.media_type == 2,  # 1=photo, 2=video, 8=carousel
                }

                # Extract media URLs based on type
                if media.media_type == 1:  # Photo
                    post_info["images"].append(str(media.thumbnail_url))

                elif media.media_type == 2:  # Video
                    post_info["videos"].append(str(media.video_url))
                    post_info["images"].append(str(media.thumbnail_url))  # Thumbnail

                elif media.media_type == 8:  # Carousel (multiple photos/videos)
                    for resource in media.resources:
                        if resource.media_type == 1:  # Photo
                            post_info["images"].append(str(resource.thumbnail_url))
                        elif resource.media_type == 2:  # Video
                            post_info["videos"].append(str(resource.video_url))
                            post_info["images"].append(str(resource.thumbnail_url))

                logger.info(f"✅ Successfully extracted post info: {post_id}")
                return post_info

            except MediaNotFound:
                logger.error(f"❌ Media not found: {post_id}")
                return {"error": "Post not found or deleted"}

            except PrivateError:
                logger.error(f"❌ Private account: {post_id}")
                return {"error": "Post is from a private account"}

            except RateLimitError:
                wait_time = 60 * (attempt + 1)
                logger.warning(f"⚠️ Rate limited, waiting {wait_time} seconds...")
                time.sleep(wait_time)
                continue

            except PleaseWaitFewMinutes:
                wait_time = 120
                logger.warning(f"⚠️ Instagram asked to wait, waiting {wait_time} seconds...")
                time.sleep(wait_time)
                continue

            except Exception as e:
                logger.error(f"❌ Error fetching post (attempt {attempt + 1}): {e}")
                if attempt < retry_count - 1:
                    time.sleep(5 * (attempt + 1))  # Exponential backoff
                    continue
                return {"error": f"Failed to fetch post: {str(e)}"}

        return {"error": "Max retries exceeded"}

    def download_media(self, url: str, save_path: str) -> bool:
        """
        Download media file from URL

        Args:
            url: Media URL
            save_path: Local path to save file

        Returns:
            bool: True if successful
        """
        try:
            import requests
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            Path(save_path).parent.mkdir(parents=True, exist_ok=True)

            with open(save_path, 'wb') as f:
                f.write(response.content)

            logger.info(f"✅ Downloaded media to: {save_path}")
            return True

        except Exception as e:
            logger.error(f"❌ Error downloading media: {e}")
            return False

    def _get_media_type(self, media) -> str:
        """Convert media type to string"""
        if media.media_type == 1:
            return "photo"
        elif media.media_type == 2:
            return "video"
        elif media.media_type == 8:
            return "carousel"
        else:
            return "unknown"

    def logout(self):
        """Logout from Instagram"""
        if self._authenticated:
            self.client.logout()
            self._authenticated = False
            logger.info("Logged out from Instagram")

# Singleton instance
instagram_service = InstagramService()
