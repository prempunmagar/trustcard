# TrustCard API Examples

## Quick Start

### 1. Submit Instagram Post for Analysis

```bash
curl -X POST "http://localhost:8000/api/analyze" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.instagram.com/reel/DP2jtydEREy/"}'
```

**Response (202 Accepted):**
```json
{
  "analysis_id": "03512c64-6f38-4593-b625-7af719cf28ae",
  "post_id": "DP2jtydEREy",
  "status": "pending",
  "message": "Analysis started successfully. Poll /api/results/{analysis_id} for status.",
  "estimated_time": 30
}
```

### 2. Check Analysis Status

```bash
curl "http://localhost:8000/api/results/03512c64-6f38-4593-b625-7af719cf28ae"
```

**Response (In Progress):**
```json
{
  "analysis_id": "03512c64-6f38-4593-b625-7af719cf28ae",
  "post_id": "DP2jtydEREy",
  "status": "processing",
  "progress": 45,
  "message": "Running AI detection...",
  "created_at": "2025-10-26T06:00:19.811167"
}
```

**Response (Completed):**
```json
{
  "analysis_id": "03512c64-6f38-4593-b625-7af719cf28ae",
  "post_id": "DP2jtydEREy",
  "status": "completed",
  "progress": 100,
  "message": "Analysis completed successfully",
  "trust_score": 75.0,
  "grade": "C",
  "post_info": {
    "post_id": "DP2jtydEREy",
    "type": "video",
    "caption": "Follow (us) @InsideHistory to learn something NEW everyday...",
    "username": "insidehistory",
    "like_count": 344238,
    "comment_count": 1315
  },
  "processing_time": 3,
  "completed_at": "2025-10-26T06:00:38.931420"
}
```

## Python Client Example

```python
import requests
import time

def analyze_instagram_post(url: str):
    """Submit and wait for analysis"""

    # Step 1: Submit
    response = requests.post(
        "http://localhost:8000/api/analyze",
        json={"url": url}
    )
    data = response.json()
    analysis_id = data["analysis_id"]

    print(f"Analysis submitted: {analysis_id}")

    # Step 2: Poll for results
    while True:
        response = requests.get(
            f"http://localhost:8000/api/results/{analysis_id}"
        )
        data = response.json()

        status = data["status"]
        progress = data.get("progress", 0)
        message = data["message"]

        print(f"Status: {status} ({progress}%) - {message}")

        if status == "completed":
            print(f"Trust Score: {data['trust_score']}/100")
            print(f"Grade: {data['grade']}")
            return data

        elif status == "failed":
            print(f"Error: {data.get('error')}")
            return None

        time.sleep(2)

# Usage
result = analyze_instagram_post("https://www.instagram.com/reel/DP2jtydEREy/")
if result:
    print(f"Post by @{result['post_info']['username']}")
    print(f"Caption: {result['post_info']['caption'][:100]}...")
```

## JavaScript Client Example

```javascript
async function analyzeInstagramPost(url) {
  // Submit for analysis
  const submitResponse = await fetch('http://localhost:8000/api/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url })
  });

  const { analysis_id } = await submitResponse.json();
  console.log(`Analysis submitted: ${analysis_id}`);

  // Poll for results
  while (true) {
    const response = await fetch(
      `http://localhost:8000/api/results/${analysis_id}`
    );
    const data = await response.json();

    console.log(`Status: ${data.status} (${data.progress}%) - ${data.message}`);

    if (data.status === 'completed') {
      console.log(`Trust Score: ${data.trust_score}/100`);
      console.log(`Grade: ${data.grade}`);
      return data;
    }

    if (data.status === 'failed') {
      console.error(`Error: ${data.error}`);
      return null;
    }

    await new Promise(resolve => setTimeout(resolve, 2000));
  }
}

// Usage
analyzeInstagramPost('https://www.instagram.com/reel/DP2jtydEREy/')
  .then(result => {
    if (result) {
      console.log(`Post by @${result.post_info.username}`);
      console.log(`Caption: ${result.post_info.caption.substring(0, 100)}...`);
    }
  });
```

## Common Use Cases

### Analyze Multiple Posts

```python
import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

urls = [
    "https://www.instagram.com/p/POST1/",
    "https://www.instagram.com/p/POST2/",
    "https://www.instagram.com/p/POST3/"
]

# Submit all
analysis_ids = []
for url in urls:
    response = requests.post(
        "http://localhost:8000/api/analyze",
        json={"url": url}
    )
    analysis_ids.append(response.json()["analysis_id"])

print(f"Submitted {len(analysis_ids)} analyses")

# Wait for all to complete
results = []
for analysis_id in analysis_ids:
    while True:
        response = requests.get(
            f"http://localhost:8000/api/results/{analysis_id}"
        )
        data = response.json()

        if data["status"] == "completed":
            results.append(data)
            break

        time.sleep(2)

# Process results
for result in results:
    print(f"{result['post_id']}: {result['grade']} - {result['trust_score']}/100")
```

### Get Analysis History

```bash
# Get recent 10 analyses
curl "http://localhost:8000/api/results?limit=10"

# Get completed analyses only
curl "http://localhost:8000/api/results?status=completed&limit=10"

# Pagination (skip first 10, get next 10)
curl "http://localhost:8000/api/results?skip=10&limit=10"
```

### Delete an Analysis

```bash
curl -X DELETE "http://localhost:8000/api/results/03512c64-6f38-4593-b625-7af719cf28ae"
```

**Response:**
```json
{
  "message": "Analysis deleted successfully",
  "analysis_id": "03512c64-6f38-4593-b625-7af719cf28ae"
}
```

## Error Handling

### Invalid URL (Not Instagram)

```bash
curl -X POST "http://localhost:8000/api/analyze" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://twitter.com/post/123"}'
```

**Response (422 Unprocessable Entity):**
```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "url"],
      "msg": "Value error, URL must be from Instagram",
      "input": "https://twitter.com/post/123",
      "ctx": {"error": {}}
    }
  ]
}
```

### Invalid URL Format (Missing /p/ or /reel/)

```bash
curl -X POST "http://localhost:8000/api/analyze" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.instagram.com/example_user/"}'
```

**Response (422 Unprocessable Entity):**
```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "url"],
      "msg": "Value error, URL must be an Instagram post, reel, or IGTV link",
      "input": "https://www.instagram.com/example_user/"
    }
  ]
}
```

### Analysis Not Found

```bash
curl "http://localhost:8000/api/results/00000000-0000-0000-0000-000000000000"
```

**Response (404 Not Found):**
```json
{
  "detail": "Analysis 00000000-0000-0000-0000-000000000000 not found"
}
```

### Instagram Extraction Failed

If the Instagram post cannot be extracted (deleted, private, etc.), the analysis status will be "failed":

```json
{
  "status": "failed",
  "error": "Failed to extract Instagram post: Post not found or deleted"
}
```

## Response Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success - analysis results returned |
| 202 | Accepted - analysis submitted successfully |
| 400 | Bad Request - invalid Instagram URL |
| 404 | Not Found - analysis ID doesn't exist |
| 422 | Unprocessable Entity - validation error |
| 500 | Internal Server Error - server error |

## Duplicate Detection

Submitting the same Instagram URL twice will return the existing analysis:

```bash
# First submission
curl -X POST "http://localhost:8000/api/analyze" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.instagram.com/p/ABC123/"}'
# Returns: analysis_id=uuid-1, status="pending"

# Second submission (same URL)
curl -X POST "http://localhost:8000/api/analyze" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.instagram.com/p/ABC123/"}'
# Returns: analysis_id=uuid-1, status="completed", estimated_time=0
```

This prevents wasting resources re-analyzing the same post.

## Grade Scale

TrustCard converts trust scores (0-100) to letter grades:

| Score Range | Grade |
|-------------|-------|
| 97-100 | A+ |
| 93-96 | A |
| 90-92 | A- |
| 87-89 | B+ |
| 83-86 | B |
| 80-82 | B- |
| 77-79 | C+ |
| 73-76 | C |
| 70-72 | C- |
| 67-69 | D+ |
| 63-66 | D |
| 60-62 | D- |
| 0-59 | F |

## Progress Tracking

The `progress` field shows percentage completion (0-100):

- **0-10%**: Analysis queued
- **10-20%**: Extracting Instagram content
- **20-40%**: Running AI detection
- **40-60%**: Checking for deepfakes
- **60-80%**: Fact-checking claims
- **80-100%**: Calculating final trust score
- **100%**: Analysis complete

## Interactive API Documentation

Visit http://localhost:8000/docs for interactive Swagger UI where you can:
- Test all endpoints
- See request/response schemas
- Try different parameters
- View validation rules

Visit http://localhost:8000/redoc for alternative ReDoc documentation.

## Rate Limiting

Currently no rate limiting is implemented. In production, consider:
- Limiting requests per user/IP
- Queuing analyses to prevent overload
- Caching results for popular posts

## Best Practices

1. **Poll Responsibly**: Wait 2-3 seconds between status checks
2. **Handle Failures**: Always check for "failed" status
3. **Cache Results**: Store completed analyses locally
4. **Validate URLs**: Check URL format before submitting
5. **Use Pagination**: Limit=10-20 for list endpoints
6. **Monitor Progress**: Show users the progress percentage
7. **Retry Failed**: Allow users to re-analyze failed posts

## Full Workflow Example (Bash)

```bash
#!/bin/bash

# Step 1: Submit analysis
echo "Submitting analysis..."
RESPONSE=$(curl -s -X POST "http://localhost:8000/api/analyze" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.instagram.com/reel/DP2jtydEREy/"}')

ANALYSIS_ID=$(echo $RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['analysis_id'])")
echo "Analysis ID: $ANALYSIS_ID"

# Step 2: Poll for results
while true; do
  RESPONSE=$(curl -s "http://localhost:8000/api/results/$ANALYSIS_ID")
  STATUS=$(echo $RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['status'])")
  PROGRESS=$(echo $RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('progress', 0))")

  echo "Status: $STATUS ($PROGRESS%)"

  if [ "$STATUS" = "completed" ]; then
    echo "Analysis complete!"
    echo $RESPONSE | python3 -m json.tool
    break
  elif [ "$STATUS" = "failed" ]; then
    echo "Analysis failed!"
    break
  fi

  sleep 2
done
```

---

**For more information, see:**
- API Documentation: http://localhost:8000/docs
- Instagram Integration Guide: `docs/instagram_integration.md`
- End-to-End Test: `test_e2e_api.py`
