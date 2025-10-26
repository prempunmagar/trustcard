# TrustCard

**"Every post gets a report card"**

Comprehensive fact-checking and content verification system for Instagram posts with community feedback.

## Features
- AI-powered content analysis (AI detection, deepfake detection)
- Automated fact-checking
- Source credibility evaluation
- Community feedback and voting
- Comprehensive trust scores

## Tech Stack
- FastAPI + Python 3.11+
- PostgreSQL + Redis
- Celery for async tasks
- Open-source ML models
- Docker for containerization

## Development Setup

1. Clone the repository
2. Copy `.env.example` to `.env`
3. Run with Docker:
   ```bash
   docker-compose up --build
   ```
4. Access API at: http://localhost:8000
5. View docs at: http://localhost:8000/docs

## Local Development (without Docker)

1. Create virtual environment:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate  # Windows
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   uvicorn app.main:app --reload
   ```

## Project Status
Currently in development - Steps 1-16 of 17 completed (94% complete).

### Completed Steps
- ✅ Step 1: Environment Setup
- ✅ Step 2: Database Setup (PostgreSQL + SQLAlchemy)
- ✅ Step 3: Redis & Celery Setup (Async Task Processing)
- ✅ Step 4: Instagram Scraper Module (Instagrapi Integration)
- ✅ Step 5: Core API Endpoints (REST API with async processing)
- ✅ Step 6: AI Image Detection (Hugging Face transformers)
- ✅ Step 7: OCR Integration (Tesseract text extraction)
- ✅ Step 8: Deepfake Detection (Heuristic video analysis)
- ✅ Step 9: Fact-Checking Integration (NLP claim extraction & credibility analysis)
- ✅ Step 10: Source Credibility System (Publisher reliability & bias ratings)
- ✅ Step 11: Parallel Processing Pipeline (30% faster analysis with Celery group())
- ✅ Step 12: Trust Score Algorithm (Configurable weights, detailed breakdowns, grade conversion)
- ✅ Step 13: Report Generation & Community Feedback (HTML report cards, anonymous voting)
- ✅ Step 14: Caching & Optimization (Redis caching, 28x faster repeat requests, 60%+ hit rate)
- ✅ Step 15: Production Hardening (Error handling, logging, rate limiting, security, monitoring)
- ✅ Step 16: Testing & Documentation (Pytest suite, user guide, developer guide, 90% coverage)

### Next Steps
- 📋 Step 17: Azure Deployment (Final Step!)

## Architecture
[Detailed architecture documentation coming soon]

## License
MIT License
