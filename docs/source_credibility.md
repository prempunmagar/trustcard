# Source Credibility Guide

## Overview

TrustCard evaluates the credibility and reliability of content sources to help users assess the trustworthiness of information shared in Instagram posts. This evaluation considers both the Instagram account sharing the content and any external sources linked in the post.

## Why Source Credibility Matters

The credibility of the source is often as important as the content itself:

- **Established news organizations** have editorial standards and fact-checking processes
- **Government agencies** provide authoritative information in their domains
- **Academic/scientific sources** undergo peer review
- **Known misinformation sites** have track records of false claims
- **Satire sites** create humor content often shared as real news

Understanding the source helps users make informed decisions about information credibility.

## How It Works

### 1. Source Database

TrustCard maintains a database of ~70 known publishers with ratings based on:
- **Media Bias/Fact Check** (MBFC)
- **AllSides Media Bias Ratings**
- **NewsGuard**
- **Ad Fontes Media Bias Chart**

### 2. Two-Dimensional Rating System

#### Reliability Rating

| Rating | Meaning | Score |
|--------|---------|-------|
| **Very High** | Excellent factual record, transparent corrections | 1.0 |
| **High** | Good factual record, minor occasional issues | 0.8 |
| **Mixed** | Some factual issues, inconsistent quality | 0.5 |
| **Low** | Poor factual record, frequent inaccuracies | 0.3 |
| **Very Low** | Consistently unreliable, conspiracy theories | 0.1 |
| **Satire** | Humor content, not intended as factual | 0.0 |
| **Unknown** | Not in database, verify independently | 0.5 |

#### Bias Rating

| Rating | Position | Score |
|--------|----------|-------|
| **Extreme Left** | Far left ideological lean | -2 |
| **Left** | Clear left bias | -1 |
| **Left-Center** | Slight left lean | -0.5 |
| **Center** | Minimal bias | 0 |
| **Right-Center** | Slight right lean | +0.5 |
| **Right** | Clear right bias | +1 |
| **Extreme Right** | Far right ideological lean | +2 |
| **Satire** | N/A | 0 |
| **Varies** | User-generated content | 0 |

**Important**: **Bias ≠ Unreliable**. Many biased sources maintain high factual accuracy. Bias indicates perspective, not truthfulness.

### 3. Evaluation Process

```
Step 1: Extract Sources
├─ Parse caption and OCR text for URLs
├─ Extract domains from URLs
└─ Get Instagram user information

Step 2: Database Lookup
├─ Query credibility database for each domain
├─ Retrieve reliability and bias ratings
└─ Handle unknown sources with default ratings

Step 3: Calculate Scores
├─ Average reliability across multiple sources
├─ Identify lowest reliability source
├─ Flag problematic sources (conspiracy, satire, unreliable)
└─ Evaluate Instagram account verification

Step 4: Generate Assessment
├─ Overall credibility evaluation
├─ Warnings for specific issues
└─ Actionable recommendations
```

## Rating Examples

### High Reliability Sources

#### Reuters (Center)
```json
{
  "domain": "reuters.com",
  "bias_rating": "center",
  "reliability_rating": "very-high",
  "reliability_score": 1.0,
  "assessment": "✅ This source has excellent factual reporting with minimal bias."
}
```

#### New York Times (Left-Center)
```json
{
  "domain": "nytimes.com",
  "bias_rating": "left-center",
  "reliability_rating": "very-high",
  "reliability_score": 1.0,
  "assessment": "✅ This source has excellent factual reporting with left-center bias."
}
```

#### Wall Street Journal (Right-Center)
```json
{
  "domain": "wsj.com",
  "bias_rating": "right-center",
  "reliability_rating": "high",
  "reliability_score": 0.8,
  "assessment": "✅ This source has good factual reporting with right-center bias."
}
```

### Mixed Reliability Sources

#### Fox News (Right)
```json
{
  "domain": "foxnews.com",
  "bias_rating": "right",
  "reliability_rating": "mixed",
  "reliability_score": 0.5,
  "assessment": "⚡ This source has mixed factual reporting with right bias. Verify important claims."
}
```

### Low Reliability Sources

#### InfoWars (Extreme Right)
```json
{
  "domain": "infowars.com",
  "bias_rating": "extreme-right",
  "reliability_rating": "very-low",
  "reliability_score": 0.1,
  "assessment": "❌ This source has a very poor factual record. Claims should be verified with reliable sources."
}
```

### Satire Sources

#### The Onion
```json
{
  "domain": "theonion.com",
  "bias_rating": "satire",
  "reliability_rating": "satire",
  "reliability_score": 0.0,
  "assessment": "⚠️ This is a SATIRE site. Content is not intended to be factual."
}
```

## Instagram Account Evaluation

### Verified Accounts
- Instagram's blue checkmark confirms account authenticity
- Higher base credibility (0.6 vs 0.4)
- **Does NOT guarantee content accuracy**
- Still requires claim verification

### Unverified Accounts
- No verification badge
- Lower base credibility (0.4)
- More common for regular users
- Requires extra scrutiny

## Trust Score Impact

Source credibility affects the overall trust score:

| Condition | Penalty/Bonus | Rationale |
|-----------|---------------|-----------|
| **Conspiracy sources** | -25 points | Extremely unreliable, likely false |
| **Unreliable sources** | -20 points | Poor track record |
| **Satire content** | -15 points | Often shared as real news |
| **Low avg reliability** (<0.5) | Up to -10 points | Mixed to poor sources |
| **High reliability** (>0.7) | Up to +3 points | Established credible sources |

## Source Categories

### News Organizations

**High Reliability**
- Reuters, Associated Press, BBC
- New York Times, Washington Post
- Wall Street Journal, The Economist

**Mixed Reliability**
- Fox News, HuffPost, BuzzFeed
- Daily Mail, New York Post

**Low Reliability**
- InfoWars, Natural News, Before It's News
- Zero Hedge, Breitbart (varies)

### Fact-Checking Sites
- Snopes, FactCheck.org, PolitiFact
- Full Fact (UK)
- All rated "very-high" reliability

### Government/Academic
- CDC, NIH, FDA, NASA, NOAA
- Nature, Science, medical journals
- All rated "very-high" reliability

### Social Media
- Instagram, Twitter/X, Facebook, TikTok
- Rated "low" reliability (user-generated content)
- Individual posts must be evaluated on merit

### Satire
- The Onion, Babylon Bee, ClickHole
- Humor content, not factual
- Special handling to alert users

## Unknown Sources

When a source is not in our database:

```json
{
  "domain": "unknownsite.com",
  "bias_rating": "unknown",
  "reliability_rating": "unknown",
  "reliability_score": 0.5,
  "in_database": false,
  "assessment": "Unknown source. Exercise caution and verify claims independently."
}
```

- Default neutral score (0.5)
- No penalty (might be legitimate but obscure)
- Clear warning to verify independently
- Recommendation to check with known sources

## Overall Assessment Generation

### Example 1: High Quality Sources

```
External Sources: 3
  1. reuters.com - very-high
  2. nytimes.com - very-high
  3. bbc.com - high

Average Reliability: 0.93
Lowest Reliability: 0.8

Overall Assessment:
✅ Sources appear credible, but always verify important claims.

Recommendation:
Sources are generally reliable, but verify before sharing important claims.
```

### Example 2: Mixed Sources

```
External Sources: 2
  1. reuters.com - very-high
  2. foxnews.com - mixed

Average Reliability: 0.65
Lowest Reliability: 0.5

Overall Assessment:
⚡ Mixed source credibility. Verify important claims.

Recommendation:
Check additional sources before accepting claims as factual.
```

### Example 3: Unreliable Sources

```
External Sources: 2
  1. infowars.com - very-low
  2. naturalnews.com - very-low

Average Reliability: 0.1
Lowest Reliability: 0.1
Has Conspiracy: true

Overall Assessment:
❌ Post links to conspiracy/unreliable sources. Claims are likely false.

Recommendation:
Do not trust claims without verification from reliable sources.
```

### Example 4: Satire

```
External Sources: 1
  1. theonion.com - satire

Has Satire: true

Overall Assessment:
⚠️ Post links to satire content. Not intended as factual.

Recommendation:
This content is satirical. Do not share as factual information.
```

## API Response Format

```json
{
  "source_credibility": {
    "status": "completed",
    "assessment": {
      "instagram_user": {
        "username": "example_user",
        "is_verified": true,
        "follower_count": 50000,
        "reliability_score": 0.6,
        "note": "✓ Verified account. However, verify claims independently."
      },
      "external_sources": [
        {
          "domain": "reuters.com",
          "bias_rating": "center",
          "reliability_rating": "very-high",
          "reliability_score": 1.0,
          "bias_score": 0,
          "in_database": true,
          "assessment": "✅ This source has excellent factual reporting with minimal bias."
        }
      ],
      "external_source_count": 1,
      "avg_reliability_score": 1.0,
      "lowest_reliability_score": 1.0,
      "has_unreliable_sources": false,
      "has_satire": false,
      "has_conspiracy": false,
      "overall_assessment": "✅ Sources appear credible, but always verify important claims.",
      "recommendation": "Sources are generally reliable, but verify before sharing important claims."
    }
  }
}
```

## Database Management

### Seeding Initial Data

```bash
# Run seeding script
python seed_sources.py
```

Seeds ~70 known sources covering:
- Major news organizations
- Fact-checking sites
- Government agencies
- Academic publishers
- Known misinformation sites
- Satire sites
- Social media platforms

### Adding New Sources

```python
from app.database import get_db_context
from app.services.source_credibility_seeder import source_seeder

with get_db_context() as db:
    source_seeder.add_source(
        db=db,
        domain="example.com",
        bias="center",
        reliability="high",
        description="Example News - Quality reporting, minimal bias"
    )
```

### Updating Existing Sources

Re-run seeding script with `update_existing=True`:

```python
with get_db_context() as db:
    source_seeder.seed_database(db, update_existing=True)
```

## Testing

### 1. Test Database Seeding

```bash
python test_source_seeding.py
```

- Seeds database with known sources
- Displays statistics
- Shows sample sources

### 2. Test Source Evaluation

```bash
python test_source_evaluation.py
```

- Tests individual source lookups
- Tests Instagram user evaluation
- Tests overall assessments
- Covers various source types

### 3. Test Full Analysis

```bash
python test_with_source_eval.py
```

- End-to-end API testing
- Analyzes real Instagram posts
- Shows source credibility in context
- Requires running API

## Limitations

### What We Can Evaluate

✅ **Major Publishers**: Well-known news organizations
✅ **Established Outlets**: Traditional media with track records
✅ **Government Sources**: Official agencies and departments
✅ **Academic Journals**: Peer-reviewed publications
✅ **Known Bad Actors**: Sites with consistently poor records

### What We Cannot Evaluate

❌ **Individual Users**: Instagram users beyond verification status
❌ **Niche Sites**: Small or new websites not yet in database
❌ **Regional/Local**: Local news outlets (limited coverage)
❌ **Foreign Language**: Non-English sources (English focus)
❌ **Content Quality**: Individual article quality varies even within reliable sources

## Best Practices

### For Users

1. **Consider source credibility as one factor** among many
2. **Understand bias ≠ false** - biased sources can be factually accurate
3. **Verify important claims** with multiple sources
4. **Be skeptical of unknown sources** until you can verify their reputation
5. **Check multiple sources** for important or surprising claims

### For Developers

1. **Keep database updated** with new sources and rating changes
2. **Document rating methodology** for transparency
3. **Handle unknown sources gracefully** without harsh penalties
4. **Respect editorial independence** - provide info, don't censor
5. **Regular audits** of source ratings against current standards

## Privacy and Ethics

### Transparency
- Source ratings are visible to users
- Methodology is documented
- Bias/reliability dimensions are clear

### Neutrality
- Rate based on factual record, not ideology
- Distinguish bias from reliability
- Include sources across political spectrum

### Non-Censorship
- Provide context, not blocking
- Users decide what to trust
- Low-rated sources still accessible with warnings

## Performance

- **Database lookup**: <10ms
- **URL extraction**: <100ms
- **Full evaluation**: 100-200ms
- **Cache enabled**: Repeated lookups instant

## Troubleshooting

### "Source not found in database"

**Normal**: Database can't cover every website
**Action**: Returns neutral score, recommends verification

### "Unexpected bias/reliability rating"

**Check**: Ratings based on established organizations (MBFC, etc.)
**Update**: Source ratings can be updated as needed

### "Instagram verification not detected"

**Verify**: Check API response includes `is_verified` field
**Fallback**: Defaults to unverified if field missing

## Future Enhancements

- [ ] Expand database to 200+ sources
- [ ] Add international news sources
- [ ] Multi-language support
- [ ] Real-time updates from rating services
- [ ] Source reliability trends over time
- [ ] Domain reputation scores
- [ ] User-contributed ratings (with moderation)

## References

- [Media Bias/Fact Check](https://mediabiasfactcheck.com/)
- [AllSides Media Bias Ratings](https://www.allsides.com/media-bias)
- [NewsGuard](https://www.newsguardtech.com/)
- [Ad Fontes Media](https://adfontesmedia.com/)

## Conclusion

Source credibility evaluation provides users with important context about information sources. By combining database ratings with analysis of external links and Instagram account verification, TrustCard helps users make informed decisions about content trustworthiness.

**Remember**: Source credibility is one factor among many. Always consider the specific claim, supporting evidence, and multiple sources before accepting information as true.

---

**Next Steps:**
- Step 11: Historical Pattern Detection
- Step 12: Trust Score Algorithm Enhancement
- Step 13: Community Feedback System
