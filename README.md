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
Currently in development - Step 1 of 17 completed.

## Architecture
[Detailed architecture documentation coming soon]

## License
MIT License
