# TrustCard Development Progress - Step 2: Database Setup

**Step:** 2 of 17
**Task:** Database Setup with PostgreSQL, SQLAlchemy, and Alembic
**Status:** ✅ Completed
**Date Started:** October 25, 2025
**Date Completed:** October 25, 2025
**Time Spent:** ~45 minutes

---

## Summary

Successfully configured PostgreSQL database with SQLAlchemy ORM, created 3-table schema for Instagram post analyses, community feedback, and source credibility tracking. Implemented Alembic for database migrations and integrated database connectivity into FastAPI application.

---

## What Was Done

### A. Database Schema Design

**Three Main Tables Created:**

1. **`analyses`** - Core table for Instagram post analysis results
   - Primary key: UUID
   - Fields: instagram_url, post_id, content (JSONB), results (JSONB), trust_score, processing_time, status, error_message
   - Indexes: instagram_url, post_id (unique)
   - Timestamps: created_at, updated_at

2. **`source_credibility`** - Reference data for publisher reliability
   - Primary key: domain (string)
   - Fields: bias_rating, reliability_rating, description, last_updated

3. **`community_feedback`** - Anonymous user feedback on analyses
   - Primary key: UUID
   - Foreign key: analysis_id → analyses.id (CASCADE delete)
   - Fields: vote_type (enum), comment, ip_hash
   - Timestamps: created_at, updated_at

**Key Design Decisions:**
- ✅ JSONB for flexible Instagram data storage (varying post types)
- ✅ JSONB for ML results (different models return different structures)
- ✅ UUID primary keys (better for distributed systems, no enumeration attacks)
- ✅ Enum for vote types (data integrity)
- ✅ IP hash instead of IP (spam prevention without storing PII)
- ✅ CASCADE delete on foreign keys (cleanup when analysis is deleted)

### B. SQLAlchemy Models Created

**Base Infrastructure:**
- ✅ `app/models/base.py` - Declarative base and TimestampMixin
- ✅ `app/models/__init__.py` - Model exports

**Model Classes:**
- ✅ `app/models/analysis.py` - Analysis model with relationships
- ✅ `app/models/source_credibility.py` - SourceCredibility model
- ✅ `app/models/community_feedback.py` - CommunityFeedback model with VoteType enum

**Relationships Configured:**
- One-to-many: Analysis → CommunityFeedback
- Cascade delete enabled
- Back-populates for bidirectional access

### C. Database Connection Module

**Created `app/database.py`:**
- ✅ Engine creation with connection pooling
- ✅ Session factory (SessionLocal)
- ✅ `get_db()` dependency for FastAPI
- ✅ `get_db_context()` context manager for standalone scripts
- ✅ `init_db()` and `drop_db()` utility functions
- ✅ Debug mode SQL logging

### D. Alembic Migration System

**Initialized Alembic:**
```bash
docker exec trustcard-api alembic init alembic
```

**Configured Alembic:**
- ✅ Updated `alembic.ini` - commented out hardcoded URL
- ✅ Updated `alembic/env.py`:
  - Imported models and settings
  - Set DATABASE_URL from config
  - Set target_metadata = Base.metadata

**Created Initial Migration:**
```bash
Migration ID: 6b526df0458b
Message: Initial schema - analyses, source_credibility, community_feedback
```

**Migration detected:**
- 3 tables: analyses, source_credibility, community_feedback
- 4 indexes
- 1 foreign key constraint
- 1 enum type (VoteType)

**Applied Migration:**
```bash
alembic upgrade head
```

**Verification:**
```
\dt
 analyses
 community_feedback
 source_credibility
 alembic_version
```

### E. CRUD Operations

**Created `app/services/crud_analysis.py`:**
- ✅ `get_by_id()` - Retrieve by UUID
- ✅ `get_by_post_id()` - Retrieve by Instagram post ID
- ✅ `get_by_url()` - Retrieve by Instagram URL
- ✅ `get_all()` - List with pagination
- ✅ `create()` - Create new analysis
- ✅ `update_results()` - Update with ML results
- ✅ `update_status()` - Update processing status
- ✅ `delete()` - Remove analysis

**Service Layer:**
- ✅ Updated `app/services/__init__.py` to export crud_analysis

### F. FastAPI Integration

**Updated `app/main.py`:**
- ✅ Added database imports (get_db, Session, text)
- ✅ Added startup event handler
- ✅ Updated `/health` endpoint to test database connection
- ✅ Using SQLAlchemy 2.0 syntax (`text()` for raw SQL)

**Health Check Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "not configured yet",
  "celery": "not configured yet"
}
```

### G. Configuration Updates

**Updated `app/config.py`:**
- ✅ Set DATABASE_URL with default value
- ✅ Using Docker service name `db` as host
- ✅ Credentials: trustcard/trustcard

**Created `.env` file:**
```env
DEBUG=True
DATABASE_URL=postgresql://trustcard:trustcard@db:5432/trustcard
REDIS_URL=redis://redis:6379/0
SECRET_KEY=dev-secret-key-change-in-production
```

**Updated `requirements.txt`:**
- ✅ Added psycopg2-binary==2.9.9 (for Docker/Python 3.11)
- ✅ Kept psycopg[binary]==3.1.18 (for future Python 3.13)

---

## Files Created

### New Files (11)
1. `app/database.py` - Database connection and session management
2. `app/models/base.py` - SQLAlchemy base and mixins
3. `app/models/analysis.py` - Analysis model
4. `app/models/source_credibility.py` - SourceCredibility model
5. `app/models/community_feedback.py` - CommunityFeedback model
6. `app/services/crud_analysis.py` - CRUD operations for analyses
7. `alembic.ini` - Alembic configuration
8. `alembic/env.py` - Alembic environment setup
9. `alembic/versions/6b526df0458b_*.py` - Initial migration
10. `.env` - Environment variables
11. `docs/progress/step-02-database-setup.md` - This file

### Modified Files (6)
1. `app/config.py` - Added DATABASE_URL default
2. `app/main.py` - Added database integration and health check
3. `app/models/__init__.py` - Export all models
4. `app/services/__init__.py` - Export CRUD operations
5. `requirements.txt` - Added psycopg2-binary
6. `docs/progress/step-01-environment-setup.md` - Updated with Step 2 reference

---

## Technical Decisions

### 1. Why JSONB Instead of Structured Columns?

**For `content` field:**
- Instagram posts vary: photos, videos, carousels, stories, reels
- Each type has different metadata
- Avoids complex table structure with nullable columns
- PostgreSQL JSONB is queryable and indexed

**For `results` field:**
- Different ML models return different outputs
- AI detection: confidence scores, model version
- Deepfake detection: face analysis, manipulation probability
- OCR results: text blocks, confidence, language
- Easy to add new models without schema changes

### 2. Why UUID Primary Keys?

- Better for distributed systems
- No ID enumeration attacks
- Globally unique across databases
- Standard in microservices architecture
- Slightly larger than integers but worth the trade-off

### 3. Why Separate SourceCredibility Table?

- Reference data for fact-checking
- Pre-populated with known publishers
- Can be updated independently
- Shared across all analyses
- Foundation for credibility scoring

### 4. Why Enum for Vote Types?

- Ensures data integrity (only valid values)
- Database-level constraint
- Type safety in Python
- Easy to extend (add new vote types)
- Better than storing arbitrary strings

### 5. Why psycopg2-binary AND psycopg3?

- psycopg2-binary: Works in Docker with Python 3.11
- psycopg3: Future compatibility with Python 3.13
- SQLAlchemy 2.0 defaults to psycopg2 driver
- Will migrate to psycopg3 when full support available

---

## Issues Encountered & Solutions

### Issue 1: psycopg2 vs psycopg3 Confusion
**Problem:** SQLAlchemy tried to use psycopg2 but only psycopg3 was installed
**Solution:**
- Added psycopg2-binary to requirements.txt
- Installed in Docker container (works fine with Python 3.11)
- Kept psycopg3 for future Python 3.13 compatibility

### Issue 2: SQLAlchemy 2.0 Raw SQL Syntax
**Problem:** `db.execute("SELECT 1")` threw deprecation error
**Solution:**
- Wrapped in `text()`: `db.execute(text("SELECT 1"))`
- SQLAlchemy 2.0 requires explicit text declaration
- Added `from sqlalchemy import text` import

### Issue 3: Alembic Configuration
**Problem:** Alembic needed to find models and DATABASE_URL
**Solution:**
- Updated `alembic/env.py` to import all models
- Set `target_metadata = Base.metadata`
- Read DATABASE_URL from app.config.settings
- Commented out hardcoded URL in alembic.ini

---

## Verification Results

### Database Tables ✅
```sql
\dt
 alembic_version
 analyses
 community_feedback
 source_credibility
```

### Table Structure ✅
```sql
\d analyses
Columns: id (uuid), instagram_url, post_id, content (jsonb),
         results (jsonb), trust_score (numeric), processing_time (int),
         status, error_message, created_at, updated_at
Indexes: PK, ix_instagram_url, ix_post_id (unique)
```

### API Health Check ✅
```bash
curl http://localhost:8000/health
{"status":"healthy","database":"connected",...}
```

### Database Connection ✅
```bash
docker exec trustcard-db psql -U trustcard -d trustcard -c "SELECT version();"
PostgreSQL 15.14
```

### Alembic Status ✅
```bash
docker exec trustcard-api alembic current
6b526df0458b (head)
```

---

## Commands Reference

### Alembic Commands
```bash
# Create new migration
docker exec trustcard-api alembic revision --autogenerate -m "description"

# Apply migrations
docker exec trustcard-api alembic upgrade head

# Rollback one migration
docker exec trustcard-api alembic downgrade -1

# Show current version
docker exec trustcard-api alembic current

# Show migration history
docker exec trustcard-api alembic history
```

### Database Commands
```bash
# Connect to database
docker exec trustcard-db psql -U trustcard -d trustcard

# List tables
docker exec trustcard-db psql -U trustcard -d trustcard -c "\dt"

# Describe table
docker exec trustcard-db psql -U trustcard -d trustcard -c "\d analyses"

# Run SQL query
docker exec trustcard-db psql -U trustcard -d trustcard -c "SELECT COUNT(*) FROM analyses;"
```

### Testing CRUD Operations
```python
from app.database import get_db_context
from app.services import crud_analysis

with get_db_context() as db:
    analysis = crud_analysis.create(
        db=db,
        instagram_url="https://instagram.com/p/test123",
        post_id="test123"
    )
    print(f"Created: {analysis.id}")
```

---

## Database Schema Diagram

```
┌─────────────────────────────────────┐
│          analyses                   │
├─────────────────────────────────────┤
│ id (PK, UUID)                       │
│ instagram_url (indexed)             │
│ post_id (unique, indexed)           │
│ content (JSONB)                     │
│ results (JSONB)                     │
│ trust_score (0-100)                 │
│ processing_time (seconds)           │
│ status (pending/processing/...)     │
│ error_message                       │
│ created_at                          │
│ updated_at                          │
└──────────┬──────────────────────────┘
           │
           │ 1:N (CASCADE)
           │
           ▼
┌─────────────────────────────────────┐
│     community_feedback              │
├─────────────────────────────────────┤
│ id (PK, UUID)                       │
│ analysis_id (FK → analyses.id)      │
│ vote_type (ENUM)                    │
│ comment                             │
│ ip_hash (indexed)                   │
│ created_at                          │
│ updated_at                          │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│      source_credibility             │
├─────────────────────────────────────┤
│ domain (PK)                         │
│ bias_rating                         │
│ reliability_rating                  │
│ description                         │
│ last_updated                        │
└─────────────────────────────────────┘
```

---

## Next Steps (Step 3)

1. Configure Redis for caching and session storage
2. Set up Celery for async task processing
3. Create Celery tasks for long-running analyses
4. Implement task queue for Instagram scraping
5. Test end-to-end async workflow

---

## Success Criteria Met ✅

- ✅ PostgreSQL running and accessible
- ✅ Three database tables created with proper schema
- ✅ SQLAlchemy models defined with relationships
- ✅ Alembic configured and initial migration applied
- ✅ Database connection working in FastAPI
- ✅ CRUD operations implemented for analyses
- ✅ `/health` endpoint shows "database: connected"
- ✅ All tables verified with correct structure
- ✅ Foreign key constraints working
- ✅ Indexes created on frequently queried fields

---

**Commit:** `63a01d8` - Complete Step 2: Database Setup
**Tables:** 4 (analyses, source_credibility, community_feedback, alembic_version)
**Models:** 3 (Analysis, SourceCredibility, CommunityFeedback)
**Database:** PostgreSQL 15.14 ✓ Connected
**Next Session:** Step 3 - Redis & Celery Configuration
