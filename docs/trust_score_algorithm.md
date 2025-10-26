# Trust Score Algorithm

## Overview

The Trust Score Algorithm calculates a comprehensive trustworthiness score (0-100) for Instagram posts based on multiple analysis components. The algorithm uses a **penalty-based system** starting from 100 points, with configurable weights for transparency and tuning.

## Architecture

### Components

```
┌─────────────────────────────────────────────────────────┐
│                   Trust Score Calculator                 │
│                                                          │
│  Base Score: 100                                        │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ AI Detection │  │  Fact-Check  │  │Source Cred.  │ │
│  │  -30 max     │  │  -40 max     │  │  -25 max     │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐                    │
│  │  Deepfake    │  │   Bonuses    │                    │
│  │  -40 fixed   │  │  +4 max      │                    │
│  └──────────────┘  └──────────────┘                    │
│                                                          │
│  Final Score: 0-100 → Grade: A+ to F                   │
└─────────────────────────────────────────────────────────┘
```

### Scoring Pipeline

1. **Start with base score** (100 points)
2. **Apply AI Detection penalties** (scaled by confidence)
3. **Apply Deepfake Detection penalties** (fixed penalty if detected)
4. **Apply Fact-Checking penalties/bonuses** (based on credibility score + red flags)
5. **Apply Source Credibility penalties/bonuses** (based on source reliability)
6. **Calculate component scores** (total impact per component)
7. **Generate grade** (A+ to F based on final score)
8. **Create detailed breakdown** (list of all adjustments with reasons)

## Scoring Weights

All weights are configurable in `app/config/scoring_config.py`.

### AI Detection

| Parameter | Weight | Description |
|-----------|--------|-------------|
| Max Penalty | -30.0 | Maximum penalty for AI-generated content |
| Confidence Multiplier | 1.0 | Scales penalty by detection confidence |

**Formula**: `penalty = -confidence × max_penalty`

**Example**:
- AI detected with 85% confidence → `-25.5 points`
- AI detected with 50% confidence → `-15.0 points`

### Deepfake Detection

| Parameter | Weight | Description |
|-----------|--------|-------------|
| Deepfake Penalty | -40.0 | Fixed penalty for detected manipulation |

**Formula**: `penalty = -40.0` (if deepfake detected)

### Fact-Checking

#### Credibility Score Impact

| Credibility Score | Action | Multiplier | Max Impact |
|------------------|--------|------------|------------|
| < 50 (Low) | Penalty | 0.8 | -40.0 |
| 50-70 (Questionable) | Penalty | 0.5 | -10.0 |
| 70-80 (Neutral) | None | - | 0 |
| ≥ 80 (High) | Bonus | 0.2 | +4.0 |

**Formulas**:
- Low: `penalty = -(50 - score) × 0.8`
- Questionable: `penalty = -(70 - score) × 0.5`
- High: `bonus = (score - 80) × 0.2`

#### Red Flag Penalties

| Flag | Weight | Description |
|------|--------|-------------|
| Medical Claims | -15.0 | Medical/health claims without verification |
| Conspiracy Language | -12.0 | Conspiracy theory language detected |
| Unverified Sources | -10.0 | Anonymous or unverified sources cited |
| Urgent Language | -8.0 | Alarmist or urgent language |
| Emotional Manipulation | -7.0 | Emotionally manipulative language |
| Absolutist Claims | -6.0 | Absolutist language (always/never) |
| Sensationalism | -5.0 | Sensationalist language |

### Source Credibility

#### Major Source Penalties

| Source Type | Weight | Description |
|-------------|--------|-------------|
| Conspiracy Sources | -25.0 | Links to known conspiracy websites |
| Unreliable Sources | -20.0 | Links to low-credibility sources |
| Satire Content | -15.0 | Links to satire/parody (may mislead) |

#### Reliability Score Adjustments

| Avg Reliability | Action | Multiplier | Max Impact |
|----------------|--------|------------|------------|
| < 0.5 (Low) | Penalty | 20.0 | -10.0 |
| 0.5-0.7 (Neutral) | None | - | 0 |
| > 0.7 (High) | Bonus | 10.0 | +3.0 |

**Formulas**:
- Low: `penalty = -(0.5 - reliability) × 20.0`
- High: `bonus = (reliability - 0.7) × 10.0`

## Grade Conversion

| Score Range | Grade | Description |
|-------------|-------|-------------|
| ≥ 95.0 | A+ | Excellent - Highly trustworthy content |
| ≥ 90.0 | A | Excellent - Very trustworthy |
| ≥ 85.0 | A- | Very Good - Trustworthy |
| ≥ 80.0 | B+ | Good - Generally trustworthy |
| ≥ 75.0 | B | Good - Mostly reliable |
| ≥ 70.0 | B- | Satisfactory - Some concerns |
| ≥ 65.0 | C+ | Fair - Multiple concerns |
| ≥ 60.0 | C | Fair - Questionable reliability |
| ≥ 55.0 | C- | Poor - Significant concerns |
| ≥ 50.0 | D+ | Poor - Low credibility |
| ≥ 45.0 | D | Very Poor - Not trustworthy |
| ≥ 40.0 | D- | Very Poor - Unreliable |
| < 40.0 | F | Failing - Highly unreliable |

## Score Breakdown Structure

The API returns a detailed breakdown showing exactly how the score was calculated:

```json
{
  "trust_score": 67.5,
  "grade": "C+",
  "grade_info": {
    "description": "Fair - Multiple concerns",
    "color": "#facc15",
    "emoji": "⚠️"
  },
  "trust_score_breakdown": {
    "final_score": 67.5,
    "grade": "C+",
    "adjustments": [
      {
        "component": "AI Detection",
        "category": "AI-Generated Content",
        "impact": -18.0,
        "reason": "AI-generated content detected with 60% confidence",
        "metadata": {
          "confidence": 0.6,
          "ai_images": 2,
          "total_images": 4
        }
      },
      {
        "component": "Fact-Checking",
        "category": "Questionable Credibility",
        "impact": -7.5,
        "reason": "Claims show questionable credibility (score: 55/100)",
        "metadata": {
          "credibility_score": 55.0
        }
      },
      {
        "component": "Fact-Checking",
        "category": "Urgent Language",
        "impact": -8.0,
        "reason": "Urgent/alarmist language detected",
        "metadata": {}
      },
      {
        "component": "Source Credibility",
        "category": "Low Source Reliability",
        "impact": -2.0,
        "reason": "Sources have low average reliability (40%)",
        "metadata": {
          "avg_reliability": 0.4
        }
      }
    ],
    "component_scores": {
      "AI Detection": -18.0,
      "Fact-Checking": -15.5,
      "Source Credibility": -2.0
    },
    "total_penalties": -35.5,
    "total_bonuses": 0.0,
    "flags": [],
    "requires_review": false
  }
}
```

## Example Scenarios

### Scenario 1: Perfect Trustworthy Post

**Input**:
- No AI detection
- No deepfakes
- High credibility claims (85/100)
- Reliable sources (0.8 reliability)

**Calculation**:
```
Base Score:                    100.0
+ High Credibility Bonus:       +1.0  (85-80) × 0.2
+ High Source Reliability:      +1.0  (0.8-0.7) × 10.0
─────────────────────────────────────
Final Score:                   102.0 → capped at 100.0
Grade:                         A+
```

### Scenario 2: AI-Generated Content

**Input**:
- AI detected (85% confidence)
- No deepfakes
- Neutral credibility (70/100)
- Neutral sources (0.5 reliability)

**Calculation**:
```
Base Score:                    100.0
- AI Detection:                -25.5  0.85 × 30
─────────────────────────────────────
Final Score:                    74.5
Grade:                          B
```

### Scenario 3: Conspiracy Theory Content

**Input**:
- No AI detection
- No deepfakes
- Low credibility (35/100)
- Conspiracy sources
- Red flags: conspiracy language, medical claims, unverified sources

**Calculation**:
```
Base Score:                    100.0
- Low Credibility:             -12.0  (50-35) × 0.8
- Conspiracy Language:         -12.0
- Medical Claims:              -15.0
- Unverified Sources:          -10.0
- Conspiracy Sources:          -25.0
─────────────────────────────────────
Final Score:                    26.0
Grade:                          F
```

### Scenario 4: Deepfake Detected

**Input**:
- No AI detection
- Deepfake detected
- Questionable credibility (60/100)
- Neutral sources

**Calculation**:
```
Base Score:                    100.0
- Deepfake Detection:          -40.0
- Questionable Credibility:     -5.0  (70-60) × 0.5
─────────────────────────────────────
Final Score:                    55.0
Grade:                          C-
```

## Configuration Customization

To customize scoring weights, modify `app/config/scoring_config.py`:

```python
from app.config.scoring_config import TrustScoreConfig, AIDetectionWeights

# Create custom config
custom_config = TrustScoreConfig(
    base_score=100.0,
    ai_detection=AIDetectionWeights(
        max_penalty=40.0,  # Increase AI penalty
        confidence_multiplier=1.2  # Scale penalty higher
    )
)

# Use custom config
from app.services.trust_score_calculator import calculate_trust_score
result = calculate_trust_score(results, config=custom_config)
```

## Testing

### Unit Tests

Test the calculator with mock data:

```bash
python test_trust_score.py
```

This runs 8 test scenarios:
1. Perfect trustworthy post
2. AI-generated content
3. Conspiracy theory content
4. Deepfake detected
5. Unreliable sources
6. Satire content
7. Multiple issues combined
8. High credibility with bonus

### Integration Tests

Test with real Instagram URLs:

```bash
python test_with_trust_score.py
```

## API Usage

### Get Analysis with Breakdown

```bash
# Submit analysis
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.instagram.com/p/XXXXXXX/"}'

# Get results (wait for completion)
curl http://localhost:8000/api/results/{analysis_id}
```

### Response Structure

```json
{
  "analysis_id": "...",
  "trust_score": 75.0,
  "grade": "B",
  "grade_info": {
    "description": "Good - Mostly reliable",
    "color": "#84cc16",
    "emoji": "👍"
  },
  "trust_score_breakdown": {
    "final_score": 75.0,
    "adjustments": [...],
    "component_scores": {...},
    "total_penalties": -25.0,
    "total_bonuses": 0.0,
    "flags": [],
    "requires_review": false
  },
  "analysis_results": {...}
}
```

## Transparency & Explainability

The trust score breakdown provides:

✅ **Full Transparency** - Every penalty and bonus is listed with exact values
✅ **Clear Reasoning** - Each adjustment includes a human-readable reason
✅ **Component Attribution** - Shows which analysis components affected the score
✅ **Metadata Context** - Additional details (confidence, scores, etc.)
✅ **Warning Flags** - Lists specific concerns that require attention
✅ **Review Flagging** - Marks content that needs manual review

## Future Enhancements

1. **Machine Learning Weights** - Learn optimal weights from user feedback
2. **Time-Based Decay** - Older sources may become less reliable
3. **User Trust History** - Account for poster's historical reliability
4. **Engagement Signals** - Consider likes, shares, comment sentiment
5. **External Verification** - Integration with professional fact-checking APIs
6. **Confidence Intervals** - Provide uncertainty ranges for scores
7. **Comparative Scoring** - Show how content compares to similar posts

---

**Implementation**: Step 12
**Status**: ✅ Complete
**Key Features**: Configurable weights, detailed breakdowns, grade conversion, full transparency
