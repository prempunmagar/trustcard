# Fact-Checking Integration Guide

## Overview

TrustCard's fact-checking system uses heuristic pattern matching and NLP to identify and analyze factual claims in Instagram posts. This system helps detect potential misinformation by analyzing claim credibility, detecting red flags, and assessing content risk.

## Important Limitations

### What This System Does

✅ **Claim Identification**
- Extracts factual statements from text
- Identifies statistical claims (numbers, percentages)
- Detects health/medical claims
- Recognizes authority citations
- Classifies claim types

✅ **Red Flag Detection**
- Urgent/manipulative language
- Absolutist statements
- Unverified sources
- Conspiracy indicators
- Emotional manipulation
- Sensationalism

✅ **Credibility Scoring**
- Analyzes language patterns
- Checks for verifiable sources
- Assesses claim types
- Calculates confidence scores

### What This System Does NOT Do

❌ **Cannot Verify Facts**
- Does not check if specific claims are true/false
- Cannot access real-time fact-checking databases
- Does not verify against authoritative sources
- Cannot replace human fact-checkers

❌ **Not a Truth Engine**
- This is a **credibility analysis system**, not a truth verification system
- Provides signals and indicators, not definitive verdicts
- Flags suspicious content for human review
- Uses heuristics, not deep fact verification

## Architecture

### Two-Stage Pipeline

```
Stage 1: Claim Extraction (claim_extractor.py)
  └─ Input: Text (caption + OCR)
  └─ Process: NLP analysis with spaCy
  └─ Output: Extracted claims with metadata

Stage 2: Credibility Analysis (fact_checking_service.py)
  └─ Input: Extracted claims + full text
  └─ Process: Pattern matching & scoring
  └─ Output: Credibility score + flags
```

## Components

### 1. Claim Extractor (`claim_extractor.py`)

Uses spaCy NLP to extract different types of claims:

#### Statistical Claims
```python
# Examples:
"90% of users report improvement"
"Sales increased by 150%"
"1 in 5 people affected"
```

Pattern matching for:
- Percentages (`\d+%`)
- Large numbers (`\d+ million`)
- Ratios (`\d+ in \d+`)
- Multipliers (`10x more`)

#### Health/Medical Claims
```python
# Examples:
"This cures cancer"
"Vaccine causes autism"
"Natural remedy prevents disease"
```

Keywords:
- Treatment: cure, treat, heal, remedy
- Prevention: prevent, protect, boost immunity
- Medical: vaccine, drug, medication, therapy

#### Factual Statements
```python
# Examples:
"The study shows that..."
"Research demonstrates..."
"Data proves..."
```

Requires:
- Factual verbs (is, are, shows, proves)
- Named entities (proper nouns)
- Declarative structure

#### Authority Citations
```python
# Examples:
"According to a doctor..."
"Studies show that..."
"Research suggests..."
```

Patterns:
- Expert references without specific names
- Study citations without sources
- Vague authority claims

### 2. Fact-Checking Service (`fact_checking_service.py`)

Analyzes extracted claims for credibility signals.

#### Red Flag Patterns

**Urgent Language**
```python
- "URGENT! ACT NOW!"
- "Before it's too late"
- "They don't want you to know"
```
**Impact:** -10 to -15 points

**Absolutist Language**
```python
- "ALWAYS works"
- "NEVER fails"
- "100% proven"
- "Everyone knows"
```
**Impact:** -8 to -12 points

**Unverified Sources**
```python
- "A doctor said..."
- "Studies show..." (without citation)
- "I heard that..."
- "They say..."
```
**Impact:** -7 to -10 points per claim

**Conspiracy Indicators**
```python
- "Cover-up"
- "Big Pharma hiding"
- "Wake up sheeple"
- "Deep state"
```
**Impact:** -12 to -20 points

**Emotional Manipulation**
```python
- "SHOCKING truth"
- "You won't believe"
- "This will blow your mind"
```
**Impact:** -8 to -12 points

**Sensationalism**
```python
- Multiple exclamation marks (!!!)
- ALL CAPS WORDS
- Excessive punctuation
```
**Impact:** -5 to -10 points

#### Medical Misinformation Patterns

Extra scrutiny for health claims:

```python
- "Natural cure for [disease]"
- "Big pharma hiding [remedy]"
- "Vaccine causes [condition]"
- "Detox/cleanse toxins"
- "100% effective treatment"
```

**Impact:** -15 to -40 points (high risk)

## Credibility Scoring

### Score Calculation (0-100)

```python
Base Score: 70 (neutral)

Penalties:
- Red flag patterns: -5 per flag (up to -30)
- Unverifiable claims: -5 per claim (up to -20)
- Vague sources: -7 per claim (up to -25)
- Medical claims: -15 per claim (up to -40)
- Clickbait: -15
- Excessive caps: -10
- Viral pressure ("share this"): -10
- High subjectivity (>0.7): -12

Bonuses:
- Source URLs provided: +5 per URL (up to +15)
- Objective tone (<0.3): +8
- No red flags: +10

Final Score = Base + Bonuses - Penalties (clamped 0-100)
```

### Score Interpretation

| Score | Interpretation | Action |
|-------|---------------|--------|
| 80-100 | Highly credible | Few concerns, likely trustworthy |
| 65-79 | Generally credible | Minor red flags, acceptable |
| 50-64 | Questionable | Multiple concerns, review recommended |
| 30-49 | Low credibility | Many warning signs, likely problematic |
| 0-29 | Very low | High risk of misinformation |

## Risk Assessment

### Risk Levels

**High Risk**
- Credibility score < 30
- Medical claims without sources
- Conspiracy language + health claims
- **Action:** Immediate manual review required

**Medium Risk**
- Credibility score 30-50
- Multiple unverifiable claims
- Vague sources + sensationalism
- **Action:** Review recommended

**Low Risk**
- Credibility score 50-70
- Minor red flags only
- **Action:** Monitor, no immediate action

**Very Low Risk**
- Credibility score > 70
- Few or no red flags
- **Action:** Normal processing

## Flags and Warnings

### System Flags

- `MEDICAL_CLAIMS:N` - N unverified medical/health claims
- `MULTIPLE_UNVERIFIABLE:N` - N unverifiable claims total
- `CLICKBAIT_DETECTED` - Clickbait patterns found
- `EXCESSIVE_CAPS` - Too much ALL CAPS text
- `VIRAL_PRESSURE` - Urgency to share/spread
- `CONSPIRACY_LANGUAGE` - Conspiracy indicators detected

### Manual Review Triggers

Automatic flagging when:
1. Credibility score < 40
2. Any medical claims present
3. 3+ red flags detected
4. High-risk language patterns

## Integration

### In Analysis Pipeline

```python
# Step 4 in analysis_tasks.py
1. Get combined text (caption + OCR)
2. Extract claims (claim_extractor)
3. Analyze credibility (fact_checking_service)
4. Update trust score based on credibility
5. Flag for manual review if needed
```

### Trust Score Impact

```python
# In _calculate_trust_score()

If credibility < 50:
    penalty = (50 - credibility) * 0.8  # Up to -40 points

If credibility < 70:
    penalty = (70 - credibility) * 0.5  # Up to -10 points

If credibility >= 80:
    bonus = (credibility - 80) * 0.2    # Up to +4 points

# Additional penalties
- Medical claims: -15 points
- Conspiracy language: -12 points
```

## API Response Format

```json
{
  "fact_check": {
    "status": "completed",
    "claim_extraction": {
      "total_claims": 3,
      "claim_types": {
        "statistical": 1,
        "health_medical": 1,
        "authority_citation": 1
      },
      "has_claims": true,
      "sentiment": {
        "polarity": -0.2,
        "subjectivity": 0.6
      }
    },
    "credibility_analysis": {
      "score": 45.5,
      "interpretation": "Questionable - Multiple red flags detected",
      "penalties": [
        {
          "reason": "3 red flag pattern(s) detected",
          "penalty": 15
        },
        {
          "reason": "1 unverified medical claim(s)",
          "penalty": 15
        }
      ],
      "bonuses": []
    },
    "flags": [
      "MEDICAL_CLAIMS:1",
      "VIRAL_PRESSURE"
    ],
    "risk_level": "medium",
    "requires_manual_review": true,
    "summary": "Credibility Score: 45.5/100 | 3 claim(s) | ⚠️ 1 high-risk medical claim(s)"
  }
}
```

## Testing

### Direct Testing

```bash
python test_fact_checking.py
```

Tests various text samples:
- High credibility with sources
- Low credibility with conspiracy language
- Medical misinformation
- Clickbait and sensationalism
- Neutral informational content

### API Testing

```bash
python test_with_fact_checking.py
```

End-to-end testing with Instagram posts:
1. Submits analysis request
2. Polls for results
3. Displays full fact-checking analysis

## Performance

### Speed
- Claim extraction: ~1-2 seconds
- Credibility analysis: ~0.5-1 second
- Total: ~2-3 seconds per post

### Accuracy Expectations

**Claim Detection:**
- Statistical claims: 90-95% recall
- Health claims: 85-90% recall
- Factual statements: 70-80% recall (many false positives)

**Red Flag Detection:**
- High-confidence patterns: 95%+ precision
- Medium-confidence patterns: 80-85% precision
- Some false positives expected (better safe than sorry)

**Credibility Scoring:**
- Directional accuracy: 85-90%
- Absolute accuracy: Not applicable (heuristic scores)
- Best used as relative comparison

## Best Practices

### 1. Use as Screening Tool
- Fact-checking provides **signals**, not verdicts
- Low scores → flag for manual review
- High scores → likely okay, but not guaranteed

### 2. Combine with Other Signals
- Use with AI detection, OCR, source credibility
- Multiple weak signals → stronger indicator
- Cross-reference different analysis results

### 3. Manual Review Essential
- Always review medical claims
- Verify statistical claims when possible
- Check sources for important claims

### 4. Update Patterns Regularly
- Add new misinformation patterns
- Refine red flag detection
- Adjust scoring weights based on results

## Common Patterns

### High-Risk Content Indicators

**Medical Misinformation:**
```
"This natural remedy cures [disease]"
+ No medical sources cited
+ Conspiracy language about "Big Pharma"
→ Credibility score: 15-30 (Very low)
→ Risk: HIGH
```

**Statistical Manipulation:**
```
"90% of doctors recommend this"
+ No study citation
+ Vague source attribution
+ Urgent language
→ Credibility score: 30-45 (Low)
→ Risk: MEDIUM
```

**Clickbait Misinformation:**
```
"SHOCKING TRUTH they don't want you to know!!!"
+ All caps + excessive punctuation
+ Conspiracy indicators
+ Emotional manipulation
→ Credibility score: 25-40 (Low)
→ Risk: MEDIUM-HIGH
```

## Limitations and Future Improvements

### Current Limitations

1. **No Real Fact Verification**
   - Cannot verify if claims are actually true
   - Relies on pattern matching only

2. **Language-Specific**
   - Optimized for English only
   - Other languages need separate patterns

3. **Context-Insensitive**
   - May flag satire/parody content
   - Cannot understand sarcasm

4. **Pattern-Based**
   - Can be evaded with slight rewording
   - Requires continuous pattern updates

### Future Enhancements

- [ ] Integration with fact-checking APIs (ClaimBuster, Google Fact Check)
- [ ] Multi-language support
- [ ] Context-aware analysis (detect satire)
- [ ] ML-based claim verification
- [ ] Historical claim database
- [ ] Source credibility cross-referencing
- [ ] Community fact-checking integration
- [ ] Real-time claim verification

## Troubleshooting

### "No claims extracted from obvious claims"

**Cause:** Text structure doesn't match expected patterns

**Solution:**
- Check if text is actually declarative statements
- Verify spaCy model is loaded correctly
- May need to add more claim patterns

### "Too many false positives"

**Cause:** Overly aggressive pattern matching

**Solution:**
- Increase confidence thresholds
- Refine pattern specificity
- Add negative examples (what NOT to flag)

### "Medical claims not detected"

**Cause:** Using different terminology

**Solution:**
- Add medical keywords to health_keywords set
- Check for synonyms and alternative phrasings
- Expand medical_red_flags patterns

### "Score seems incorrect"

**Cause:** Edge case in scoring logic

**Solution:**
- Review penalties and bonuses applied
- Check if special cases are handled
- May need to adjust scoring weights

## Security and Privacy

### Safe Processing
- All text analysis runs in sandboxed environment
- No external API calls by default
- No data sent to third parties

### Data Storage
- Only extracted claims and scores stored
- Full text not retained after analysis
- Personally identifiable information filtered

## Conclusion

TrustCard's fact-checking system provides a **first-line defense** against misinformation by:
- Identifying factual claims automatically
- Detecting common misinformation patterns
- Scoring content credibility
- Flagging high-risk content for review

**Remember:** This is a screening tool, not a replacement for human fact-checkers. Always verify critical claims manually.

---

**Next Steps:**
- Step 10: Source Credibility Analysis
- Step 11: Historical Pattern Detection
- Step 12: Trust Score Algorithm Enhancement
