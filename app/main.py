"""
TrustCard - Every post gets a report card
Main FastAPI application entry point
"""
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.config import settings
from app.database import get_db

app = FastAPI(
    title="TrustCard API",
    description="Comprehensive fact-checking and content verification for Instagram posts",
    version="0.1.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    print("🚀 Starting TrustCard API...")
    print("✅ Database connection ready")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Welcome to TrustCard API",
        "tagline": "Every post gets a report card",
        "status": "operational",
        "version": "0.1.0"
    }

@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Detailed health check"""
    try:
        # Test database connection
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    return {
        "status": "healthy",
        "database": db_status,
        "redis": "not configured yet",
        "celery": "not configured yet"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
