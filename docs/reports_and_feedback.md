# Reports & Community Feedback Guide

## Overview

TrustCard generates beautiful, shareable "report cards" for analyzed content and incorporates community wisdom through anonymous voting. This combines **AI analysis with human judgment**.

## HTML Report Cards

### Features

- 📊 **Visual Trust Score Display** - Large, color-coded grade
- 📋 **Detailed Analysis Breakdown** - Component-by-component results
- 💬 **Community Voting Results** - Aggregated community opinion
- 📝 **Key Findings Summary** - Bullet-point highlights
- ⚡ **Actionable Recommendations** - What to do with the information
- 🎨 **Beautiful Design** - Professional, print-ready layout
- 📱 **Responsive** - Works on desktop and mobile
- 🔗 **Shareable** - Standalone HTML, no dependencies

### Accessing Reports

#### Via API

```bash
GET /api/reports/{analysis_id}
```

Returns HTML report card.

#### Example

```bash
# Get report for a completed analysis
curl http://localhost:8000/api/reports/123e4567-e89b-12d3-a456-426614174000

# Or open in browser
open http://localhost:8000/api/reports/123e4567-e89b-12d3-a456-426614174000
```

### Using Reports

Reports can be:
- **Viewed in browser** - Click the URL
- **Shared via link** - Send URL to others
- **Saved as PDF** - Use browser's Print → Save as PDF
- **Embedded** - Use iframe (if CORS configured)

### Report Sections

#### 1. Header
- TrustCard branding
- "Every post gets a report card" tagline
- Gradient purple background

#### 2. Post Information
- Instagram username
- Post ID
- Analysis timestamp
- Processing time

#### 3. Trust Score
- Large, prominent display
- Color-coded (green = good, red = bad)
- Letter grade (A+ to F)
- Overall assessment text

#### 4. Detailed Analysis
- Grid of components:
  - AI Detection
  - Deepfake Check
  - Fact Verification
  - Source Credibility
- Each shows grade and status

#### 5. Community Feedback
- Total vote count
- Vote breakdown with visual bars:
  - ✓ Accurate (green)
  - ⚠ Misleading (yellow)
  - ✗ False (red)
- Percentage and count for each
- "Add Your Voice" button

#### 6. Key Findings
- Bullet-point list
- Most important insights
- Easy to scan

#### 7. Recommendation
- Purple gradient box
- Clear action to take
- Based on trust score

#### 8. Footer
- Disclaimer
- Version info
- Copyright

## Community Feedback System

### Philosophy

**AI + Human Wisdom = Better Truth**

While AI analyzes content automatically, human judgment adds crucial context that machines miss. The community voting system allows people to:
- Confirm or challenge AI findings
- Add local knowledge and context
- Flag edge cases
- Build collective intelligence

### Vote Types

| Vote Type | Meaning | When to Use |
|-----------|---------|-------------|
| **✓ Accurate** | Content is truthful and correct | Claims verified, sources reliable |
| **⚠ Misleading** | Partially false or lacks context | Cherry-picked data, missing info |
| **✗ False** | Demonstrably false information | Debunked claims, fake content |

### Submitting Feedback

#### Via API

```bash
POST /api/reports/{analysis_id}/feedback

{
  "vote_type": "accurate",
  "comment": "Optional explanation of your vote"
}
```

#### Example - Vote Accurate

```bash
curl -X POST http://localhost:8000/api/reports/{analysis_id}/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "vote_type": "accurate",
    "comment": "I verified these claims with the original source"
  }'
```

#### Example - Vote Misleading

```bash
curl -X POST http://localhost:8000/api/reports/{analysis_id}/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "vote_type": "misleading",
    "comment": "Missing important context about the situation"
  }'
```

#### Example - Vote False

```bash
curl -X POST http://localhost:8000/api/reports/{analysis_id}/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "vote_type": "false",
    "comment": "This claim was debunked by multiple fact-checkers"
  }'
```

### Response

```json
{
  "message": "Thank you for your feedback!",
  "feedback_id": "987fcdeb-51a2-43c7-b123-456789abcdef",
  "summary": {
    "total_votes": 148,
    "accurate": 101,
    "misleading": 32,
    "false": 15
  }
}
```

### Features

#### Anonymous Voting
- ✅ No login or account required
- ✅ Quick and easy to participate
- ✅ Encourages honest feedback
- ✅ Privacy-friendly

#### Duplicate Prevention
- IP address hashed (SHA-256)
- One vote per analysis per IP
- Prevents ballot stuffing
- Hash not reversible (anonymous)

#### Optional Comments
- Add context to your vote
- Explain reasoning
- Help others understand
- Build knowledge base

#### Real-time Aggregation
- Vote counts update immediately
- Percentages calculated automatically
- Recent comments displayed
- Always current data

### Getting Feedback Summary

```bash
GET /api/reports/{analysis_id}/feedback
```

#### Example

```bash
curl http://localhost:8000/api/reports/{analysis_id}/feedback
```

#### Response

```json
{
  "analysis_id": "123e4567-e89b-12d3-a456-426614174000",
  "summary": {
    "total_votes": 147,
    "accurate": 100,
    "misleading": 32,
    "false": 15
  },
  "recent_comments": [
    {
      "vote_type": "accurate",
      "comment": "Verified with original sources",
      "created_at": "2024-01-15T14:30:00Z"
    },
    {
      "vote_type": "misleading",
      "comment": "Missing important context",
      "created_at": "2024-01-15T14:28:00Z"
    }
  ]
}
```

## Testing

### Test Report Generation

```bash
python test_report_generation.py
```

This script:
1. Prompts for Instagram URL
2. Submits analysis
3. Waits for completion
4. Generates HTML report
5. Opens report in browser

### Test Community Feedback

```bash
python test_community_feedback.py
```

This script:
1. Prompts for analysis ID
2. Shows current votes
3. Allows vote submission
4. Displays updated results

## Integration Examples

### Frontend Integration

```javascript
// Submit analysis
const response = await fetch('http://localhost:8000/api/analyze', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ url: instagramUrl })
});

const { analysis_id } = await response.json();

// Poll for completion
let status = 'pending';
while (status !== 'completed') {
  await new Promise(resolve => setTimeout(resolve, 2000));

  const statusRes = await fetch(`http://localhost:8000/api/results/${analysis_id}`);
  const data = await statusRes.json();
  status = data.status;
}

// Redirect to report
window.location.href = `http://localhost:8000/api/reports/${analysis_id}`;
```

### Submit Feedback

```javascript
// Submit vote
await fetch(`http://localhost:8000/api/reports/${analysis_id}/feedback`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    vote_type: 'accurate',
    comment: 'I verified this information'
  })
});

// Refresh feedback
const feedbackRes = await fetch(`http://localhost:8000/api/reports/${analysis_id}/feedback`);
const feedback = await feedbackRes.json();

console.log(`Total votes: ${feedback.summary.total_votes}`);
```

## Best Practices

### For Users

1. **Vote Honestly** - Base votes on evidence, not bias
2. **Add Comments** - Explain reasoning when possible
3. **Verify Claims** - Check sources before voting
4. **Don't Brigade** - One honest vote per person
5. **Report Abuse** - Flag spam or manipulation

### For Developers

1. **Rate Limiting** - Implement to prevent abuse
2. **Moderation** - Monitor comments for spam
3. **Analytics** - Track voting patterns
4. **Cache Reports** - Reduce generation overhead
5. **Monitor Performance** - Keep report generation fast

## Database Schema

### Community Feedback Table

```sql
CREATE TABLE community_feedback (
  id UUID PRIMARY KEY,
  analysis_id UUID REFERENCES analyses(id) ON DELETE CASCADE,
  vote_type VARCHAR(20) NOT NULL,  -- accurate, misleading, false
  comment TEXT,
  ip_hash VARCHAR(64),  -- SHA-256 hash for duplicate prevention
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_feedback_analysis ON community_feedback(analysis_id);
CREATE INDEX idx_feedback_ip ON community_feedback(ip_hash);
```

## Future Enhancements

### Short-term
- Vote editing (change your vote)
- Comment threading (replies)
- Helpful/not helpful on comments
- Export report as PDF directly

### Medium-term
- User accounts (optional verified votes)
- Reputation system (weight trusted voters)
- Vote reasoning categories
- Report sharing analytics

### Long-term
- Fact-checker integration
- Expert verification badges
- Crowdsourced corrections
- Machine learning from votes

## Troubleshooting

### Report Not Generating

**Problem**: 404 error when accessing report

**Solution**:
- Verify analysis is completed
- Check analysis_id is correct
- Ensure templates directory exists

### Duplicate Vote Error

**Problem**: "You have already voted" error

**Solution**:
- This is expected behavior (one vote per IP)
- Use different network or wait for IP change
- Feature working as designed

### Template Not Found

**Problem**: "Template not found" error

**Solution**:
- Verify `app/templates/report_card.html` exists
- Check Jinja2 is installed: `pip install jinja2`
- Restart application

### Styling Issues

**Problem**: Report looks unstyled

**Solution**:
- CSS is inline, should always work
- Check browser console for errors
- Try different browser

## API Reference

### GET /api/reports/{analysis_id}

Get HTML report card.

**Parameters**:
- `analysis_id` (path) - UUID of analysis

**Response**: HTML document

**Status Codes**:
- 200 - Success
- 400 - Analysis not completed
- 404 - Analysis not found

### POST /api/reports/{analysis_id}/feedback

Submit community feedback.

**Parameters**:
- `analysis_id` (path) - UUID of analysis

**Body**:
```json
{
  "vote_type": "accurate",  // required: accurate/misleading/false
  "comment": "Optional explanation"  // optional
}
```

**Response**:
```json
{
  "message": "Thank you for your feedback!",
  "feedback_id": "uuid",
  "summary": {
    "total_votes": 148,
    "accurate": 101,
    "misleading": 32,
    "false": 15
  }
}
```

**Status Codes**:
- 200 - Success
- 400 - Invalid vote type or duplicate vote
- 404 - Analysis not found

### GET /api/reports/{analysis_id}/feedback

Get feedback summary and recent comments.

**Parameters**:
- `analysis_id` (path) - UUID of analysis

**Response**:
```json
{
  "analysis_id": "uuid",
  "summary": {
    "total_votes": 147,
    "accurate": 100,
    "misleading": 32,
    "false": 15
  },
  "recent_comments": [
    {
      "vote_type": "accurate",
      "comment": "Verified with sources",
      "created_at": "2024-01-15T14:30:00Z"
    }
  ]
}
```

**Status Codes**:
- 200 - Success
- 404 - Analysis not found

---

**Implementation**: Step 13
**Status**: ✅ Complete
**Key Features**: HTML reports, anonymous voting, community wisdom, beautiful design
