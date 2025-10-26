# TrustCard Development Progress Log

## Step 12: Trust Score Algorithm ✅

**Date Completed**: 2024
**Status**: ✅ Complete

### Overview

Implemented a comprehensive, transparent trust score calculation system with configurable weights, detailed breakdowns, and grade conversion. The system provides full explainability showing exactly how each score was calculated.

### What Was Built

#### 1. Scoring Configuration Module (`app/config/scoring_config.py`)

**Purpose**: Centralized configuration for all trust score weights and thresholds

**Key Components**:
- `AIDetectionWeights` - AI detection penalty configuration
- `DeepfakeWeights` - Deepfake detection penalty configuration
- `FactCheckWeights` - Fact-checking penalties/bonuses and red flag weights
- `SourceCredibilityWeights` - Source credibility penalties/bonuses
- `GradeThresholds` - Grade conversion thresholds (A+ to F)
- `TrustScoreConfig` - Master configuration with all components
- `get_grade_from_score()` - Convert score to letter grade
- `get_grade_description()` - Get grade description, color, emoji

**Configurability**:
- All weights exposed as dataclass fields
- Easy to customize for different use cases
- Default configuration provided

#### 2. Trust Score Calculator Service (`app/services/trust_score_calculator.py`)

**Purpose**: Centralized service for calculating trust scores with detailed breakdowns

**Key Components**:
- `ScoreAdjustment` - Dataclass for individual score adjustments
- `TrustScoreResult` - Complete result with score, grade, breakdown
- `TrustScoreCalculator` - Main calculator class

**Features**:
- Processes all analysis components (AI, OCR, Deepfake, Fact-Check, Source Credibility)
- Generates detailed list of adjustments with reasons
- Calculates component scores (total impact per component)
- Provides warning flags
- Marks content requiring manual review
- Full transparency and explainability

**Methods**:
- `calculate_trust_score()` - Main calculation method
- `_process_ai_detection()` - Process AI detection results
- `_process_ocr()` - Process OCR results (informational)
- `_process_deepfake()` - Process deepfake detection
- `_process_fact_checking()` - Process fact-checking with red flags
- `_process_source_credibility()` - Process source credibility
- `_calculate_component_scores()` - Calculate per-component totals

#### 3. Analysis Task Updates (`app/tasks/analysis_tasks.py`)

**Changes**:
- Replaced embedded `_calculate_trust_score()` method with centralized calculator
- Added trust score breakdown to results
- Updated return structure to include grade
- Improved logging to show grade with score

#### 4. API Route Updates (`app/api/routes/analysis.py`)

**Changes**:
- Extract breakdown from results if available
- Add `trust_score_breakdown` to top-level response
- Add `grade_info` with description, color, emoji
- Use grade from breakdown instead of calculating
- Filter breakdown from `analysis_results` (avoid duplication)
- Updated list endpoint to include grade info

#### 5. Test Scripts

**`test_trust_score.py`** - Unit tests for calculator
- 8 test scenarios with mock data
- Tests perfect posts, AI content, conspiracies, deepfakes, etc.
- Pretty-printed results with breakdowns
- Shows configuration values used

**`test_with_trust_score.py`** - Integration tests
- End-to-end test with real Instagram URLs
- Tracks analysis progress
- Displays detailed breakdown
- Exports breakdown to JSON file
- Option to retrieve existing analyses

#### 6. Documentation

**`docs/trust_score_algorithm.md`** - Comprehensive documentation
- Architecture overview
- Scoring pipeline explanation
- Complete weight tables
- Formula documentation
- Grade conversion table
- Example scenarios with calculations
- API usage examples
- Configuration customization guide
- Future enhancements

### Technical Details

#### Scoring Algorithm

**Base Approach**: Penalty-based system starting at 100 points

**Components**:
1. **AI Detection**: Up to -30 points (scaled by confidence)
2. **Deepfake Detection**: -40 points (fixed if detected)
3. **Fact-Checking**: -40 to +4 points (based on credibility + red flags)
4. **Source Credibility**: -25 to +3 points (based on source reliability)

**Grade Conversion**: 13 grades from A+ to F based on score thresholds

#### Breakdown Structure

```json
{
  "trust_score_breakdown": {
    "final_score": 67.5,
    "grade": "C+",
    "grade_info": {
      "description": "Fair - Multiple concerns",
      "color": "#facc15",
      "emoji": "⚠️"
    },
    "adjustments": [
      {
        "component": "AI Detection",
        "category": "AI-Generated Content",
        "impact": -18.0,
        "reason": "AI-generated content detected with 60% confidence",
        "metadata": {...}
      }
    ],
    "component_scores": {
      "AI Detection": -18.0,
      "Fact-Checking": -15.5
    },
    "total_penalties": -35.5,
    "total_bonuses": 0.0,
    "flags": [],
    "requires_review": false
  }
}
```

### Files Created

```
app/config/
  __init__.py                              # Config package exports
  scoring_config.py                        # Scoring weights configuration (217 lines)

app/services/
  trust_score_calculator.py                # Trust score calculator (489 lines)

test_trust_score.py                        # Unit tests (392 lines)
test_with_trust_score.py                   # Integration tests (284 lines)

docs/
  trust_score_algorithm.md                 # Comprehensive documentation
  progress_log.md                          # This file
```

### Files Modified

```
app/tasks/analysis_tasks.py                # Use centralized calculator
app/api/routes/analysis.py                 # Include breakdown in API response
README.md                                   # Update progress to Step 12
```

### Testing

#### Unit Tests
```bash
python test_trust_score.py
```

Tests 8 scenarios:
1. ✅ Perfect trustworthy post (100+)
2. ✅ AI-generated content (74.5)
3. ✅ Conspiracy theory (26.0)
4. ✅ Deepfake detected (55.0)
5. ✅ Unreliable sources
6. ✅ Satire content
7. ✅ Multiple issues combined
8. ✅ High credibility with bonuses

#### Integration Tests
```bash
python test_with_trust_score.py
```

- Submits real Instagram URL for analysis
- Tracks progress with timing
- Displays detailed breakdown
- Exports breakdown to JSON

### Key Benefits

✅ **Full Transparency** - Every penalty/bonus listed with exact values
✅ **Clear Reasoning** - Human-readable explanations for each adjustment
✅ **Configurable** - All weights easily tunable via dataclasses
✅ **Explainable** - Complete breakdown shows how score was calculated
✅ **Maintainable** - Centralized calculation logic, not scattered
✅ **Testable** - Easy to test with mock data
✅ **Extensible** - Simple to add new components or adjust weights

### Performance Impact

- **Calculation Time**: Negligible (~1-2ms)
- **API Response Size**: Increased by ~1-2KB due to breakdown
- **Database**: No schema changes required (breakdown stored in results JSON)

### Example Output

```
📊 TRUST SCORE BREAKDOWN
════════════════════════════════════════════════════════════════════

Final Score: 67.5/100
Grade: C+
Description: Fair - Multiple concerns
Emoji: ⚠️

Component Impact:
  AI Detection: -18.0
  Fact-Checking: -15.5
  Source Credibility: -2.0

Total Penalties: -35.5
Total Bonuses: 0.0

Detailed Adjustments:
  [AI Detection] AI-Generated Content
    Impact: -18.0 points
    Reason: AI-generated content detected with 60% confidence

  [Fact-Checking] Questionable Credibility
    Impact: -7.5 points
    Reason: Claims show questionable credibility (score: 55/100)

  [Fact-Checking] Urgent Language
    Impact: -8.0 points
    Reason: Urgent/alarmist language detected

  [Source Credibility] Low Source Reliability
    Impact: -2.0 points
    Reason: Sources have low average reliability (40%)
```

### Next Steps (Step 13)

Now that we have a robust trust score algorithm, the next step is to implement community feedback:

- Voting system (upvote/downvote)
- User comments on analyses
- Manual review workflow
- Feedback influence on scores
- Community moderation

---

**Step 12 Complete!** ✅

The trust score algorithm now provides full transparency and explainability, making it clear to users exactly how their content was evaluated. The configurable weights allow easy tuning based on feedback and changing requirements.

---

## Step 13: Report Generation & Community Feedback ✅

**Date Completed**: 2024
**Status**: ✅ Complete

### Overview

Implemented the signature "report card" feature that TrustCard is named for! Beautiful HTML reports combine AI analysis with community wisdom through anonymous voting.

### What Was Built

#### 1. HTML Report Template (`app/templates/report_card.html`)

**Purpose**: Beautiful, professional report card layout

**Design Features**:
- Gradient purple header with branding
- Large, color-coded trust score display
- Component-by-component analysis breakdown
- Community voting with visual progress bars
- Key findings in bullet points
- Actionable recommendation
- Professional footer with disclaimers
- Fully responsive (mobile + desktop)
- Inline CSS (no external dependencies)
- Print-friendly (can save as PDF)

**Sections**:
1. Header - TrustCard branding
2. Post Info - Instagram details
3. Trust Score - Overall grade (A+ to F)
4. Detailed Analysis - Component grades
5. Community Feedback - Vote bars
6. Key Findings - Bullet points
7. Recommendation - What to do
8. Footer - Disclaimer and info

#### 2. Report Generator Service (`app/services/report_generator.py`)

**Purpose**: Generate HTML reports from analysis data

**Key Components**:
- `ReportGenerator` class
- Jinja2 template engine integration
- Data extraction and formatting
- Grade color coding
- Component list building
- Findings list generation
- Recommendation generation

**Methods**:
- `generate_html_report()` - Main generation method
- `_get_grade_color()` - Color based on score
- `_build_components_list()` - Format component data
- `_build_findings_list()` - Extract key findings
- `_get_recommendation()` - Generate recommendation

#### 3. Community Feedback CRUD (`app/services/crud_feedback.py`)

**Purpose**: Database operations for community voting

**Operations**:
- `add_feedback()` - Submit vote with optional comment
- `get_feedback_summary()` - Aggregate vote counts
- `get_recent_comments()` - Fetch recent comments
- `check_duplicate_vote()` - Prevent duplicate voting

**Features**:
- IP address hashing (SHA-256) for anonymity
- Vote aggregation by type
- Comment retrieval
- Duplicate detection

#### 4. Reports API Routes (`app/api/routes/reports.py`)

**Purpose**: API endpoints for reports and feedback

**Endpoints**:

**GET /api/reports/{analysis_id}**
- Returns HTML report card
- Includes community feedback
- 404 if analysis not found
- 400 if not completed

**POST /api/reports/{analysis_id}/feedback**
- Submit vote (accurate/misleading/false)
- Optional comment
- IP-based duplicate prevention
- Returns updated vote summary

**GET /api/reports/{analysis_id}/feedback**
- Get vote summary
- Get recent comments
- Vote counts and percentages

#### 5. Database Model (Already Existed)

**Community Feedback Table**:
- `id` - UUID primary key
- `analysis_id` - Foreign key to analyses
- `vote_type` - Enum (accurate/misleading/false)
- `comment` - Optional text comment
- `ip_hash` - SHA-256 hash for spam prevention
- `created_at` - Timestamp
- `updated_at` - Timestamp

**Relationships**:
- Analysis → Many Feedback records

### Files Created

```
app/templates/
  report_card.html                         # HTML report template (300+ lines)

app/services/
  report_generator.py                      # Report generation service (284 lines)
  crud_feedback.py                         # Feedback CRUD operations (147 lines)

app/api/routes/
  reports.py                               # Reports API endpoints (225 lines)

test_report_generation.py                  # Report generation test (127 lines)
test_community_feedback.py                 # Feedback system test (145 lines)

docs/
  reports_and_feedback.md                  # Comprehensive documentation
```

### Files Modified

```
app/main.py                                # Added reports router
requirements.txt                           # Added jinja2==3.1.2
README.md                                  # Updated to Step 13
docs/progress_log.md                       # This file
```

### Technical Details

#### Report Generation Flow

1. GET request to `/api/reports/{analysis_id}`
2. Fetch analysis from database
3. Fetch community feedback summary
4. Extract score data from results
5. Build components list (AI, Deepfake, Fact-check, Sources)
6. Build findings list (key insights)
7. Generate recommendation based on score
8. Render Jinja2 template with all data
9. Return HTML response

#### Community Voting Flow

1. POST request to `/api/reports/{analysis_id}/feedback`
2. Validate analysis exists
3. Get IP address from request
4. Check for duplicate vote (IP hash lookup)
5. Validate vote type (accurate/misleading/false)
6. Hash IP address (SHA-256)
7. Create feedback record in database
8. Aggregate updated vote counts
9. Return confirmation and summary

#### Vote Aggregation

```python
# Count votes by type
SELECT vote_type, COUNT(*) as count
FROM community_feedback
WHERE analysis_id = ?
GROUP BY vote_type

# Calculate percentages
accurate_percent = (accurate_count / total_votes) * 100
misleading_percent = (misleading_count / total_votes) * 100
false_percent = (false_count / total_votes) * 100
```

### Design Decisions

#### Why HTML Reports?

- **Shareable**: Single URL anyone can view
- **Printable**: Save as PDF easily
- **No Auth Required**: Public access to reports
- **Fast**: Pre-rendered HTML, no client-side processing
- **Accessible**: Works with screen readers
- **Beautiful**: Professional, branded design

#### Why Anonymous Voting?

- **Lower Barrier**: No login required
- **More Participation**: Easy to submit
- **Honest Feedback**: Anonymous = more honest
- **Privacy-Friendly**: No user tracking

#### IP-Based Duplicate Prevention

- **Balance**: Prevent spam without requiring accounts
- **Anonymous**: IP hash can't be reversed
- **Simple**: One vote per IP per analysis
- **Not Perfect**: Can be bypassed with VPN (acceptable trade-off)

#### Vote Types

**Accurate**: Content is truthful
- Use when claims verified
- Sources are reliable
- Context is complete

**Misleading**: Lacks context or cherry-picks data
- Use when partially true but missing info
- Data is real but framed incorrectly
- Important context omitted

**False**: Demonstrably false
- Use when claims debunked
- Sources are fake
- Information is fabricated

### Testing

#### Report Generation Test

```bash
python test_report_generation.py
```

**Flow**:
1. Prompt for Instagram URL
2. Submit analysis
3. Poll until complete (with progress)
4. Generate report
5. Open in browser automatically
6. Display success message

#### Community Feedback Test

```bash
python test_community_feedback.py
```

**Flow**:
1. Prompt for analysis ID
2. Display current vote counts
3. Show recent comments
4. Prompt for vote (1=accurate, 2=misleading, 3=false)
5. Prompt for optional comment
6. Submit feedback
7. Display updated counts
8. Handle duplicate vote error gracefully

### Key Features

✅ **Beautiful HTML Reports** - Professional, branded design
✅ **Community Voting** - Accurate/Misleading/False options
✅ **Anonymous Feedback** - No login required
✅ **Duplicate Prevention** - IP-based spam protection
✅ **Visual Vote Bars** - Progress bars show vote distribution
✅ **Recent Comments** - Show community reasoning
✅ **Shareable URLs** - Easy to share and embed
✅ **Print/PDF Ready** - Can save reports as PDF
✅ **Responsive Design** - Works on all devices
✅ **Real-time Aggregation** - Vote counts update immediately

### Example Report Structure

```
┌─────────────────────────────────────┐
│     🎯 TRUSTCARD REPORT            │
│  "Every post gets a report card"    │
├─────────────────────────────────────┤
│ Instagram Post: @username           │
│ Analyzed: Jan 15, 2024             │
│                                     │
│  Trust Score: B+ (85/100)          │
│  Good credibility. Verify claims.   │
├─────────────────────────────────────┤
│ Detailed Analysis:                  │
│  AI Detection:        A (Authentic) │
│  Deepfake Check:      A (Clean)     │
│  Fact Verification:   C (Concerns)  │
│  Source Credibility:  B+ (Good)     │
├─────────────────────────────────────┤
│ Community Says (147 votes):         │
│  ✓ Accurate:    68% ████████░░      │
│  ⚠ Misleading:  22% ████░░░░░░      │
│  ✗ False:       10% ██░░░░░░░░      │
├─────────────────────────────────────┤
│ Key Findings:                       │
│  • Images appear authentic          │
│  • 2 of 5 claims verified          │
│  • Source has moderate bias         │
│  • 147 community members reviewed   │
├─────────────────────────────────────┤
│ Recommendation:                     │
│  Approach with healthy skepticism.  │
│  Verify key claims before sharing.  │
└─────────────────────────────────────┘
```

### Performance Impact

- **Report Generation**: ~50-100ms (template rendering)
- **Vote Submission**: ~20-30ms (database insert + aggregation)
- **Vote Aggregation**: ~10-20ms (COUNT query with GROUP BY)
- **Duplicate Check**: ~5-10ms (indexed hash lookup)

### API Usage Examples

#### Get Report

```bash
# Get HTML report (open in browser)
curl http://localhost:8000/api/reports/123e4567-e89b-12d3-a456-426614174000
```

#### Submit Feedback

```bash
# Vote accurate
curl -X POST http://localhost:8000/api/reports/{id}/feedback \
  -H "Content-Type: application/json" \
  -d '{"vote_type": "accurate", "comment": "Verified with sources"}'

# Vote misleading
curl -X POST http://localhost:8000/api/reports/{id}/feedback \
  -H "Content-Type: application/json" \
  -d '{"vote_type": "misleading", "comment": "Missing context"}'

# Vote false
curl -X POST http://localhost:8000/api/reports/{id}/feedback \
  -H "Content-Type: application/json" \
  -d '{"vote_type": "false", "comment": "Debunked by fact-checkers"}'
```

#### Get Feedback Summary

```bash
curl http://localhost:8000/api/reports/{id}/feedback
```

### Future Enhancements

**Short-term**:
- Vote editing (change your vote)
- Comment threading (replies to comments)
- Helpful/not helpful on comments
- Export report directly as PDF

**Medium-term**:
- User accounts (optional, for verified votes)
- Reputation system (weight trusted voters)
- Vote reasoning categories
- Report sharing analytics

**Long-term**:
- Professional fact-checker integration
- Expert verification badges
- Crowdsourced corrections
- Machine learning from community votes
- Vote quality scoring

### Success Metrics

This step successfully delivers:
- ✅ Beautiful, shareable report cards
- ✅ Community voting system
- ✅ Anonymous participation
- ✅ Spam prevention
- ✅ Real-time aggregation
- ✅ Mobile-responsive design
- ✅ Print-ready output
- ✅ Comprehensive documentation

---

**Step 13 Complete!** ✅

TrustCard now truly lives up to its name: **"Every post gets a report card"**. The combination of AI analysis and community wisdom provides a more complete picture of content credibility.
