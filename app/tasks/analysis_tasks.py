"""
Analysis Orchestration Tasks for Processing Instagram Posts

Uses Celery group() for parallel processing of independent analyses.
"""

from celery import shared_task, group
from sqlalchemy.orm import Session
from uuid import UUID
import time
import logging

from app.database import get_db_context
from app.services.crud_analysis import crud_analysis
from app.services.instagram_service import instagram_service
from app.services.trust_score_calculator import calculate_trust_score
from app.services.cache_manager import cache_manager

# Import individual task modules
from app.tasks.ai_detection_task import run_ai_detection
from app.tasks.ocr_task import run_ocr_extraction
from app.tasks.deepfake_task import run_deepfake_detection
from app.tasks.fact_checking_task import run_fact_checking
from app.tasks.source_evaluation_task import run_source_evaluation

logger = logging.getLogger(__name__)


@shared_task(name="analysis.process_post", bind=True)
def process_instagram_post(self, analysis_id: str) -> dict:
    """
    Main orchestrator task - coordinates parallel analysis.

    Execution Strategy:
    1. Instagram extraction (sequential - required first)
    2. Parallel batch: AI Detection, OCR, Deepfake (run simultaneously)
    3. Fact-checking (sequential - needs OCR text)
    4. Source evaluation (sequential - needs text)
    5. Calculate trust score (sequential - needs all results)

    Args:
        analysis_id: UUID of the analysis record

    Returns:
        dict: Results of the analysis
    """
    with get_db_context() as db:
        analysis = crud_analysis.get_by_id(db, UUID(analysis_id))

        if not analysis:
            return {"error": "Analysis not found"}

        analysis.status = "processing"
        db.commit()

        try:
            instagram_url = analysis.instagram_url

            # ==========================================
            # CACHE CHECK: See if we already analyzed this URL
            # ==========================================
            cached_result = cache_manager.get_cached_analysis(instagram_url)

            if cached_result:
                logger.info(f"🚀 [Orchestrator] Using cached results for {instagram_url}")

                # Update database with cached results
                crud_analysis.update_results(
                    db=db,
                    analysis_id=UUID(analysis_id),
                    results=cached_result.get("results", {}),
                    trust_score=cached_result.get("trust_score", 0),
                    processing_time=1  # Instant from cache
                )

                return {
                    "status": "success",
                    "analysis_id": analysis_id,
                    "trust_score": cached_result.get("trust_score", 0),
                    "grade": cached_result.get("grade", "N/A"),
                    "cached": True,
                    "processing_time": 1
                }

            # ==========================================
            # STEP 1: Extract Instagram Content (Sequential)
            # ==========================================
            logger.info(f"📸 [Orchestrator] Extracting Instagram post: {instagram_url}")

            if not instagram_service._authenticated:
                instagram_service.authenticate()

            # Extract post ID for caching
            post_id = instagram_service.extract_post_id(instagram_url)

            # Check Instagram content cache
            post_info = cache_manager.get_cached_instagram_content(post_id)

            if not post_info:
                # Cache miss - scrape Instagram
                post_info = instagram_service.get_post_info(instagram_url)

                if not post_info or "error" in post_info:
                    raise Exception(f"Failed to extract: {post_info.get('error', 'Unknown error')}")

                # Cache the scraped content
                cache_manager.cache_instagram_content(post_id, post_info)
            else:
                logger.info(f"🚀 [Orchestrator] Using cached Instagram content for {post_id}")

            analysis.content = post_info
            db.commit()

            logger.info(f"✅ [Orchestrator] Instagram content extracted")

            # Extract data for parallel tasks
            image_urls = post_info.get("images", [])
            video_urls = post_info.get("videos", [])
            caption = post_info.get("caption", "")
            post_type = post_info.get("type", "")
            instagram_user = post_info.get("user", {})

            # ==========================================
            # STEP 2: Run Parallel Analyses
            # ==========================================
            logger.info(f"⚡ [Orchestrator] Starting parallel analysis tasks")
            logger.info(f"   Images: {len(image_urls)}, Videos: {len(video_urls)}")

            # Create parallel task group - these run SIMULTANEOUSLY
            parallel_tasks = group([
                run_ai_detection.s(image_urls),
                run_ocr_extraction.s(image_urls, caption),
                run_deepfake_detection.s(video_urls, image_urls, post_type)
            ])

            # Execute parallel tasks
            parallel_job = parallel_tasks.apply_async()

            # Wait for all parallel tasks to complete (max 2 minutes)
            parallel_results = parallel_job.get(timeout=120)

            # Unpack results
            ai_result = parallel_results[0]
            ocr_result = parallel_results[1]
            deepfake_result = parallel_results[2]

            logger.info(f"✅ [Orchestrator] Parallel tasks complete!")
            logger.info(f"   AI Detection: {ai_result.get('status')}")
            logger.info(f"   OCR Extraction: {ocr_result.get('status')}")
            logger.info(f"   Deepfake Detection: {deepfake_result.get('status')}")

            # ==========================================
            # STEP 3: Run Fact-Checking (Sequential)
            # ==========================================
            logger.info(f"🔍 [Orchestrator] Running fact-checking")

            # Get combined text from OCR result
            combined_text = ocr_result.get("combined", {}).get("combined_text", caption)

            # Run fact-checking
            fact_check_result = run_fact_checking(combined_text)

            logger.info(f"✅ [Orchestrator] Fact-checking: {fact_check_result.get('status')}")

            # ==========================================
            # STEP 4: Run Source Evaluation (Sequential)
            # ==========================================
            logger.info(f"📰 [Orchestrator] Running source evaluation")

            # Run source evaluation
            source_eval_result = run_source_evaluation(combined_text, instagram_user)

            logger.info(f"✅ [Orchestrator] Source evaluation: {source_eval_result.get('status')}")

            # ==========================================
            # STEP 5: Aggregate Results
            # ==========================================
            results = {
                "instagram_extraction": {
                    "status": "success",
                    "post_type": post_type,
                    "media_count": len(image_urls) + len(video_urls)
                },
                "ai_detection": ai_result,
                "ocr": ocr_result,
                "deepfake": deepfake_result,
                "fact_check": fact_check_result,
                "source_credibility": source_eval_result
            }

            # ==========================================
            # STEP 6: Calculate Trust Score
            # ==========================================
            logger.info(f"🎯 [Orchestrator] Calculating trust score")

            # Use centralized calculator
            score_result = calculate_trust_score(results)

            # Extract trust score and grade
            trust_score = score_result.final_score
            grade = score_result.grade

            # Add score breakdown to results
            results["trust_score_breakdown"] = {
                "final_score": score_result.final_score,
                "grade": score_result.grade,
                "grade_info": score_result.grade_info,
                "adjustments": [
                    {
                        "component": adj.component,
                        "category": adj.category,
                        "impact": adj.impact,
                        "reason": adj.reason,
                        "metadata": adj.metadata
                    }
                    for adj in score_result.adjustments
                ],
                "component_scores": score_result.component_scores,
                "total_penalties": score_result.total_penalties,
                "total_bonuses": score_result.total_bonuses,
                "flags": score_result.flags,
                "requires_review": score_result.requires_review
            }

            # Calculate processing time
            processing_time = int(time.time() - analysis.created_at.timestamp())

            # ==========================================
            # STEP 7: Update Database
            # ==========================================
            crud_analysis.update_results(
                db=db,
                analysis_id=UUID(analysis_id),
                results=results,
                trust_score=trust_score,
                processing_time=processing_time
            )

            # ==========================================
            # CACHE THE RESULTS
            # ==========================================
            cache_data = {
                "results": results,
                "trust_score": trust_score,
                "grade": grade,
                "post_info": post_info
            }
            cache_manager.cache_analysis_result(instagram_url, cache_data)

            logger.info(f"✅ [Orchestrator] Analysis complete!")
            logger.info(f"   Trust Score: {trust_score}/100 ({grade})")
            logger.info(f"   Processing Time: {processing_time}s")

            return {
                "status": "success",
                "analysis_id": analysis_id,
                "trust_score": trust_score,
                "grade": grade,
                "post_type": post_type,
                "processing_time": processing_time,
                "cached": False
            }

        except Exception as e:
            logger.error(f"❌ [Orchestrator] Analysis failed: {e}")

            analysis.status = "failed"
            analysis.error_message = str(e)
            db.commit()

            return {
                "status": "error",
                "error": str(e)
            }


@shared_task(name="analysis.retry_failed")
def retry_failed_analyses():
    """Periodic task to retry failed analyses"""
    # Will implement in Step 15
    pass
