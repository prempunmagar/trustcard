"""
Core API endpoints for analysis
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
import logging

from app.database import get_db
from app.services.crud_analysis import crud_analysis
from app.services.instagram_service import instagram_service
from app.tasks.analysis_tasks import process_instagram_post
from app.api.schemas.analysis import (
    AnalyzeRequest,
    AnalyzeResponse,
    ResultsResponse,
    AnalysisListResponse
)
from app.api.utils.response_helpers import (
    calculate_grade,
    get_status_message,
    build_post_info_response,
    calculate_progress
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["analysis"])

@router.post("/analyze", response_model=AnalyzeResponse, status_code=202)
async def analyze_instagram_post(
    request: AnalyzeRequest,
    db: Session = Depends(get_db)
):
    """
    Submit Instagram post URL for analysis

    This endpoint:
    1. Validates the Instagram URL
    2. Checks if post was already analyzed (returns existing analysis)
    3. Creates new analysis record in database
    4. Submits task to Celery queue
    5. Returns immediately with analysis_id

    Users should poll GET /api/results/{analysis_id} to get results.

    **Estimated time:** 20-40 seconds for complete analysis
    """
    url = str(request.url)

    # Extract post ID
    post_id = instagram_service.extract_post_id(url)
    if not post_id:
        raise HTTPException(
            status_code=400,
            detail="Invalid Instagram URL format"
        )

    logger.info(f"Received analysis request for post: {post_id}")

    # Check if post already analyzed
    existing = crud_analysis.get_by_post_id(db, post_id)
    if existing:
        logger.info(f"Post {post_id} already analyzed, returning existing analysis")

        # If completed, return existing
        if existing.status == "completed":
            return AnalyzeResponse(
                analysis_id=existing.id,
                post_id=post_id,
                status="completed",
                message="This post was already analyzed. Use /api/results/{analysis_id} to view results.",
                estimated_time=0
            )

        # If processing, return existing task
        if existing.status in ["pending", "processing"]:
            return AnalyzeResponse(
                analysis_id=existing.id,
                post_id=post_id,
                status=existing.status,
                message="Analysis already in progress. Use /api/results/{analysis_id} to check status.",
                estimated_time=30
            )

        # If failed, allow re-analysis
        logger.info(f"Previous analysis failed, creating new analysis for {post_id}")

    # Create new analysis record
    try:
        analysis = crud_analysis.create(
            db=db,
            instagram_url=url,
            post_id=post_id
        )
        logger.info(f"Created analysis record: {analysis.id}")
    except Exception as e:
        logger.error(f"Failed to create analysis record: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create analysis: {str(e)}"
        )

    # Submit to Celery
    try:
        task = process_instagram_post.delay(str(analysis.id))
        logger.info(f"Submitted task {task.id} for analysis {analysis.id}")
    except Exception as e:
        logger.error(f"Failed to submit Celery task: {e}")
        # Mark analysis as failed
        analysis.status = "failed"
        analysis.error_message = f"Failed to submit task: {str(e)}"
        db.commit()
        raise HTTPException(
            status_code=500,
            detail="Failed to submit analysis task"
        )

    return AnalyzeResponse(
        analysis_id=analysis.id,
        post_id=post_id,
        status="pending",
        message="Analysis started successfully. Poll /api/results/{analysis_id} for status.",
        estimated_time=30
    )

@router.get("/results/{analysis_id}", response_model=ResultsResponse)
async def get_analysis_results(
    analysis_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get analysis results by ID

    Poll this endpoint to check status and get results when completed.

    **Status values:**
    - `pending` - Analysis queued, not started yet
    - `processing` - Analysis in progress
    - `completed` - Analysis finished, results available
    - `failed` - Analysis failed, see error field

    **Recommended polling:** Every 2-3 seconds until status is `completed` or `failed`
    """
    # Get analysis from database
    analysis = crud_analysis.get_by_id(db, analysis_id)

    if not analysis:
        raise HTTPException(
            status_code=404,
            detail=f"Analysis {analysis_id} not found"
        )

    # Calculate progress
    progress = calculate_progress(analysis.status, analysis.results)

    # Check if from cache (instant processing time = cached)
    is_cached = False
    if analysis.processing_time is not None and analysis.processing_time <= 2:
        is_cached = True

    # Get status message
    message = get_status_message(analysis.status, progress)
    if is_cached and analysis.status == "completed":
        message = "Results retrieved from cache (instant)"

    # Build response
    response = {
        "analysis_id": analysis.id,
        "post_id": analysis.post_id,
        "status": analysis.status,
        "progress": progress,
        "message": message,
        "created_at": analysis.created_at,
        "cached": is_cached
    }

    # Add trust score and grade if completed
    if analysis.trust_score is not None:
        response["trust_score"] = float(analysis.trust_score)

        # Extract grade from breakdown if available, otherwise calculate
        if analysis.results and "trust_score_breakdown" in analysis.results:
            breakdown = analysis.results["trust_score_breakdown"]
            response["grade"] = breakdown.get("grade")
            response["grade_info"] = breakdown.get("grade_info")

            # Add detailed breakdown
            response["trust_score_breakdown"] = {
                "adjustments": breakdown.get("adjustments", []),
                "component_scores": breakdown.get("component_scores", {}),
                "total_penalties": breakdown.get("total_penalties", 0),
                "total_bonuses": breakdown.get("total_bonuses", 0),
                "flags": breakdown.get("flags", []),
                "requires_review": breakdown.get("requires_review", False)
            }
        else:
            # Fallback to old grade calculation
            response["grade"] = calculate_grade(float(analysis.trust_score))

    # Add post info if available
    if analysis.content:
        response["post_info"] = build_post_info_response(analysis.content)

    # Add analysis results if available (without breakdown, already added above)
    if analysis.results:
        # Copy results but exclude breakdown (already at top level)
        filtered_results = {
            k: v for k, v in analysis.results.items()
            if k != "trust_score_breakdown"
        }
        response["analysis_results"] = filtered_results

    # Add processing time if completed
    if analysis.processing_time:
        response["processing_time"] = analysis.processing_time

    if analysis.status == "completed":
        response["completed_at"] = analysis.updated_at

    # Add error if failed
    if analysis.status == "failed" and analysis.error_message:
        response["error"] = analysis.error_message

    return response

@router.get("/results", response_model=AnalysisListResponse)
async def list_analyses(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of records to return"),
    status: Optional[str] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db)
):
    """
    List all analyses with pagination

    Useful for:
    - Viewing recent analyses
    - Finding analyses by status
    - Building a dashboard
    """
    # Build query
    query = db.query(crud_analysis.model)

    # Filter by status if provided
    if status:
        query = query.filter(crud_analysis.model.status == status)

    # Get total count
    total = query.count()

    # Get paginated results
    analyses = query.order_by(crud_analysis.model.created_at.desc()).offset(skip).limit(limit).all()

    # Build response for each analysis
    results = []
    for analysis in analyses:
        result = {
            "analysis_id": analysis.id,
            "post_id": analysis.post_id,
            "status": analysis.status,
            "progress": calculate_progress(analysis.status, analysis.results),
            "message": get_status_message(analysis.status),
            "created_at": analysis.created_at,
        }

        if analysis.trust_score is not None:
            result["trust_score"] = float(analysis.trust_score)

            # Extract grade from breakdown if available
            if analysis.results and "trust_score_breakdown" in analysis.results:
                breakdown = analysis.results["trust_score_breakdown"]
                result["grade"] = breakdown.get("grade")
                result["grade_info"] = breakdown.get("grade_info")
            else:
                result["grade"] = calculate_grade(float(analysis.trust_score))

        if analysis.content:
            result["post_info"] = build_post_info_response(analysis.content)

        if analysis.status == "completed":
            result["completed_at"] = analysis.updated_at

        results.append(result)

    return {
        "total": total,
        "analyses": results,
        "page": skip // limit + 1 if limit > 0 else 1,
        "page_size": limit
    }

@router.delete("/results/{analysis_id}")
async def delete_analysis(
    analysis_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Delete an analysis record

    ⚠️ This cannot be undone!
    """
    success = crud_analysis.delete(db, analysis_id)

    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Analysis {analysis_id} not found"
        )

    return {
        "message": "Analysis deleted successfully",
        "analysis_id": analysis_id
    }
