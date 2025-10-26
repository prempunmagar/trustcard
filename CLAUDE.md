# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project: TrustCard

**"Every post gets a report card"**

Comprehensive fact-checking and content verification system for Instagram posts with community feedback.

## Tech Stack

- **Backend:** FastAPI (Python 3.11+)
- **Database:** PostgreSQL 15
- **Cache/Queue:** Redis 7
- **Task Queue:** Celery (configured in Step 3)
- **Containerization:** Docker + Docker Compose
- **ML/AI:** Will integrate open-source models in later steps

## Development Environment Setup

### Using Docker (Recommended)

```bash
# Build and start all services
docker compose up --build

# Run in background
docker compose up -d

# View logs
docker compose logs -f

# Stop all services
docker compose down

# Stop and remove volumes (database data)
docker compose down -v
```

### Local Development (Python 3.11-3.12 only)

Note: Python 3.13 has compatibility issues with some dependencies. Use Docker or Python 3.11-3.12.

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
.\venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the app
uvicorn app.main:app --reload
```

## Project Structure

```
trustcard/
├── app/
│   ├── main.py              # FastAPI entry point
│   ├── config.py            # Settings (uses pydantic-settings)
│   ├── models/              # Database models (SQLAlchemy)
│   ├── api/
│   │   └── routes/          # API endpoints
│   ├── services/            # Business logic
│   ├── tasks/               # Celery background tasks
│   └── utils/               # Helper functions
├── tests/                   # Test files
├── docs/                    # Documentation
├── requirements.txt         # Python dependencies
├── Dockerfile              # API container definition
└── docker-compose.yml      # Multi-container orchestration
```

## Key Files

### app/main.py
- FastAPI application instance
- CORS middleware configuration
- Root and health check endpoints
- Run with: `uvicorn app.main:app --reload`

### app/config.py
- Pydantic Settings for configuration
- Loads from environment variables or .env file
- Access via: `from app.config import settings`

### docker-compose.yml
- Defines 3 services: api, db (PostgreSQL), redis
- Default credentials for local dev (trustcard/trustcard)
- Persistent volumes for database and redis data

## API Endpoints

- `GET /` - Welcome message and API status
- `GET /health` - Health check (shows service status)
- `GET /docs` - Auto-generated Swagger/OpenAPI documentation
- `GET /redoc` - Alternative API documentation

Access locally at: http://localhost:8000

## Database

- PostgreSQL 15 running in Docker on port 5432
- Default credentials (local dev):
  - User: trustcard
  - Password: trustcard
  - Database: trustcard
- Will configure migrations with Alembic in Step 2

## Important Notes

### Python Version Compatibility
- **Production (Docker):** Uses Python 3.11 (defined in Dockerfile)
- **Local Development:** Python 3.11-3.12 recommended
- **Python 3.13:** Has compatibility issues with pydantic-core and other deps

### Database Package
- Using `psycopg[binary]` v3 instead of psycopg2-binary
- Better Python 3.13 support
- SQLAlchemy 2.0 compatible

## Development Workflow

1. Make code changes in `app/` directory
2. Docker automatically reloads on file changes (volume mount)
3. Test endpoints at http://localhost:8000/docs
4. Run tests with: `pytest` (when tests are added)
5. Commit changes to Git

## Next Steps (Development Roadmap)

- **Step 2:** Database schema and models
- **Step 3:** Redis and Celery configuration
- **Step 4:** Instagram integration
- **Steps 5-17:** ML models, fact-checking, community features

## Troubleshooting

### Docker issues
- Make sure Docker Desktop is running
- Check containers: `docker ps`
- View logs: `docker compose logs -f api`
- Restart: `docker compose restart`

### Port conflicts
- Default ports: 8000 (API), 5432 (PostgreSQL), 6379 (Redis)
- Change in docker-compose.yml if needed

### Database connection issues
- Wait for PostgreSQL to fully start (takes ~5 seconds)
- Check: `docker compose logs db`
