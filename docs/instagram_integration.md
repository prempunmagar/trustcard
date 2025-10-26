# Instagram Integration Guide

## Overview

TrustCard uses the `instagrapi` library to extract content from Instagram posts. This provides reliable access to post metadata, media URLs, and user information.

## Authentication

### Setup Credentials

1. **Create a test Instagram account** (DO NOT use personal account)
   - Go to instagram.com
   - Sign up with a new email
   - Create a username like `trustcard_test_123`
   - Complete basic profile setup
   - Follow a few public accounts to look legitimate

2. **Add credentials to `.env`:**
   ```env
   INSTAGRAM_USERNAME=your_test_account
   INSTAGRAM_PASSWORD=your_test_password
   ```

### Authenticate via API

```bash
curl -X POST "http://localhost:8000/instagram/auth"
```

Response:
```json
{
  "status": "authenticated",
  "message": "Successfully authenticated with Instagram"
}
```

### Authenticate via Python

```python
from app.services.instagram_service import instagram_service
instagram_service.authenticate()
```

## Extracting Posts

### Via API

```bash
curl -X POST "http://localhost:8000/instagram/extract" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.instagram.com/reel/DP2jtydEREy/"}'
```

### Via Python

```python
from app.services.instagram_service import instagram_service

post_info = instagram_service.get_post_info("https://www.instagram.com/p/ABC123/")
print(post_info)
```

### Response Format

```json
{
  "post_id": "DP2jtydEREy",
  "url": "https://www.instagram.com/reel/DP2jtydEREy/",
  "type": "video",
  "caption": "Post caption text...",
  "images": ["https://scontent-..."],
  "videos": ["https://scontent-..."],
  "user": {
    "username": "example_user",
    "full_name": "Example User",
    "is_verified": false,
    "profile_pic_url": "https://..."
  },
  "timestamp": "2025-10-16T01:58:24+00:00",
  "like_count": 344194,
  "comment_count": 1315,
  "location": "USA",
  "is_video": true
}
```

## Supported Post Types

- **Photos** - Single image posts
- **Videos** - Single video posts
- **Carousels** - Multiple images/videos
- **Reels** - Short video posts
- **IGTV** - Long video posts

## URL Formats Supported

```
https://www.instagram.com/p/ABC123/
https://instagram.com/p/ABC123/
https://www.instagram.com/reel/XYZ789/
https://instagram.com/tv/DEF456/
```

## Rate Limiting

Instagram enforces rate limits:
- **Too many requests:** Wait 60+ seconds
- **Suspicious activity:** Account may be flagged
- **Best practice:** Use delays between requests (built into service)

The service automatically:
- Adds 1-3 second random delays between requests
- Implements exponential backoff on errors
- Retries up to 3 times
- Saves session to avoid repeated logins

## Error Handling

### Common Errors

| Error | Meaning | Solution |
|-------|---------|----------|
| `LoginRequired` | Not authenticated | Call `/instagram/auth` |
| `MediaNotFound` | Post doesn't exist | Check URL is valid |
| `PrivateError` | Private account | Cannot access |
| `RateLimitError` | Too many requests | Wait before retrying |
| `Invalid Instagram URL` | Malformed URL | Check URL format |

### Example Error Response

```json
{
  "detail": "Post not found or deleted"
}
```

### Retry Logic

The service automatically retries with exponential backoff:
- **Attempt 1**: Immediate
- **Attempt 2**: Wait 5 seconds
- **Attempt 3**: Wait 10 seconds

## Session Management

Sessions are saved to `instagram_session.json` and reused across restarts to avoid repeated logins.

**⚠️ Security:**
- Session file is in `.gitignore` (NEVER commit)
- Contains sensitive authentication tokens
- Automatically reused on service restart

## Testing

### Test Script

Run the test script to verify authentication and extraction:

```bash
python test_instagram.py
```

This will:
1. Test Instagram authentication
2. Prompt for a test URL
3. Extract and display post information

### Manual API Test

1. **Start the API:**
   ```bash
   docker compose up
   ```

2. **Test authentication:**
   ```bash
   curl -X POST "http://localhost:8000/instagram/auth"
   ```

3. **Test extraction:**
   ```bash
   curl -X POST "http://localhost:8000/instagram/extract" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://www.instagram.com/reel/DP2jtydEREy/"}'
   ```

4. **Check status:**
   ```bash
   curl http://localhost:8000/instagram/test
   ```

### Interactive API Documentation

Visit: http://localhost:8000/docs

Test endpoints interactively:
- POST `/instagram/auth` - Authenticate
- POST `/instagram/extract` - Extract post
- GET `/instagram/test` - Check status

## Integration with Analysis Pipeline

The Instagram service is integrated into the main analysis task:

```python
# app/tasks/analysis_tasks.py

@shared_task(name="analysis.process_post")
def process_instagram_post(analysis_id: str):
    # 1. Extract Instagram content
    post_info = instagram_service.get_post_info(instagram_url)

    # 2. Store in database
    analysis.content = post_info

    # 3. Run ML analysis (Steps 6-9)
    # ... AI detection, deepfake, fact-checking

    # 4. Calculate trust score
    # ... combine all analysis results
```

## Security Best Practices

1. ✅ **Use dedicated test account**
   - Never use personal Instagram account
   - Create throwaway account for development

2. ✅ **Never commit credentials**
   - `.env` is in `.gitignore`
   - `instagram_session.json` is in `.gitignore`

3. ✅ **Keep session file secure**
   - Contains authentication tokens
   - Treat like a password

4. ✅ **Respect Instagram's ToS**
   - Use delays between requests
   - Don't abuse rate limits
   - Only extract public posts

5. ✅ **Monitor account health**
   - Check for login warnings
   - Rotate accounts if flagged
   - Use realistic behavior patterns

## Troubleshooting

### "Authentication failed"
- Check credentials in `.env`
- Ensure account is not locked/flagged
- Try logging in manually on instagram.com
- Delete `instagram_session.json` and retry

### "Please wait few minutes"
- Instagram rate limit triggered
- Wait 10-15 minutes before retrying
- Use longer delays between requests
- Consider using multiple test accounts

### "Media not found"
- Post may be deleted
- Check URL format is correct
- Post may be from private account
- Try a different public post

### "Client object has no attribute..."
- Instagrapi API version mismatch
- Check requirements.txt has instagrapi==2.1.2
- Rebuild Docker containers

### Session file not loading
- Check file permissions
- Ensure `.env` credentials match session
- Delete session file to force re-authentication

## Docker Integration

The Instagram service runs in both API and Celery worker containers:

```yaml
# docker-compose.yml
api:
  environment:
    - INSTAGRAM_USERNAME=${INSTAGRAM_USERNAME}
    - INSTAGRAM_PASSWORD=${INSTAGRAM_PASSWORD}

celery_worker:
  environment:
    - INSTAGRAM_USERNAME=${INSTAGRAM_USERNAME}
    - INSTAGRAM_PASSWORD=${INSTAGRAM_PASSWORD}
```

Session file is stored on the host and shared via volume mount.

## Health Check

The `/health` endpoint shows Instagram authentication status:

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "celery": "configured",
  "instagram": "authenticated"
}
```

## Next Steps

In Steps 6-9, we'll process the extracted Instagram content:

- **Step 6**: AI-generated content detection
- **Step 7**: OCR text extraction
- **Step 8**: Deepfake detection
- **Step 9**: Fact-checking verification

The Instagram extraction provides the raw data for all these ML models.

## API Reference

### POST /instagram/auth

Authenticate with Instagram using credentials from `.env`.

**Response:**
```json
{
  "status": "authenticated",
  "message": "Successfully authenticated with Instagram"
}
```

### POST /instagram/extract

Extract information from Instagram post URL.

**Request:**
```json
{
  "url": "https://www.instagram.com/p/ABC123/"
}
```

**Response:** See "Response Format" section above.

### GET /instagram/test

Check if Instagram service is authenticated and ready.

**Response:**
```json
{
  "status": "authenticated",
  "message": "Instagram service is ready"
}
```

## Development Tips

1. **Use real public posts for testing** - Don't create fake data
2. **Test different post types** - Photos, videos, carousels, reels
3. **Handle errors gracefully** - Instagram API can be unpredictable
4. **Monitor rate limits** - Add delays if getting rate limited
5. **Rotate test accounts** - If one gets flagged, use another
6. **Log everything** - Helps debug authentication issues

## Example Usage

```python
from app.services.instagram_service import instagram_service
from app.database import get_db_context
from app.services.crud_analysis import crud_analysis

# Authenticate
instagram_service.authenticate()

# Extract post
post_info = instagram_service.get_post_info(
    "https://www.instagram.com/reel/DP2jtydEREy/"
)

# Create analysis record
with get_db_context() as db:
    analysis = crud_analysis.create(
        db=db,
        instagram_url="https://www.instagram.com/reel/DP2jtydEREy/",
        post_id="DP2jtydEREy"
    )

    # Store content
    analysis.content = post_info
    db.commit()

print(f"Extracted {post_info['type']} post from @{post_info['user']['username']}")
print(f"Media: {len(post_info['images'])} images, {len(post_info['videos'])} videos")
```

---

**Last updated:** 2025-10-26
**Instagrapi version:** 2.1.2
**Python version:** 3.11+
