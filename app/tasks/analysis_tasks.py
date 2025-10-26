"""
Analysis Orchestration Tasks for Processing Instagram Posts

Uses Celery group() for parallel processing of independent analyses.
"""

from celery import shared_task, group, chord
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


@shared_task(name="analysis.complete_analysis", bind=True)
def complete_analysis(self, parallel_results: list, analysis_id: str, post_info: dict,
                      caption: str, instagram_user: dict, instagram_url: str,
                      created_timestamp: float) -> dict:
    """
    Callback task that runs after parallel analyses complete.

    Handles sequential tasks (fact-checking, source evaluation, scoring)
    and final database update.

    Args:
        parallel_results: List of [ai_result, ocr_result, deepfake_result]
        analysis_id: UUID of the analysis
        post_info: Instagram post metadata
        caption: Post caption text
        instagram_user: User information
        instagram_url: Original Instagram URL
        created_timestamp: Analysis start timestamp

    Returns:
        dict: Final analysis results
    """
    with get_db_context() as db:
        try:
            # Unpack parallel results
            ai_result = parallel_results[0]
            ocr_result = parallel_results[1]
            deepfake_result = parallel_results[2]

            logger.info(f"✅ [Callback] Parallel tasks complete for {analysis_id}")
            logger.info(f"   AI Detection: {ai_result.get('status')}")
            logger.info(f"   OCR Extraction: {ocr_result.get('status')}")
            logger.info(f"   Deepfake Detection: {deepfake_result.get('status')}")

            # ==========================================
            # STEP 3: Run Fact-Checking (Sequential)
            # ==========================================
            logger.info(f"🔍 [Callback] Running fact-checking")
            logger.info(f"📊 [Callback] OCR result keys: {list(ocr_result.keys()) if ocr_result else 'None'}")

            # Get combined text from OCR result
            combined_text = None
            if ocr_result and isinstance(ocr_result, dict):
                if "combined" in ocr_result and isinstance(ocr_result["combined"], dict):
                    combined_text = ocr_result["combined"].get("combined_text")

            # Fallback to caption if no OCR text
            if not combined_text:
                combined_text = caption
                logger.warning(f"⚠️ [Callback] No OCR combined text found, using caption only")

            logger.info(f"📝 [Callback] Combined text length: {len(combined_text) if combined_text else 0}")

            # Import and call as regular function (not Celery task)
            from app.services.claim_extractor import claim_extractor
            from app.services.fact_checking_service import fact_checking_service

            try:
                # Extract claims
                claim_extractor.initialize()
                claim_data = claim_extractor.extract_claims(combined_text)

                # Analyze credibility
                fact_check_analysis = fact_checking_service.analyze_claims(claim_data, combined_text)

                fact_check_result = {
                    "status": "completed",
                    "claim_extraction": {
                        "total_claims": claim_data.get("total_claims", 0),
                        "claim_types": claim_data.get("claim_types", {}),
                        "has_claims": claim_data.get("has_claims", False),
                        "sentiment": claim_data.get("sentiment", "neutral")
                    },
                    "credibility_analysis": {
                        "score": fact_check_analysis.get("credibility_score", {}).get("score", 50),
                        "interpretation": fact_check_analysis.get("credibility_score", {}).get("interpretation", "Unknown"),
                        "penalties": fact_check_analysis.get("credibility_score", {}).get("penalties", 0),
                        "bonuses": fact_check_analysis.get("credibility_score", {}).get("bonuses", 0)
                    },
                    "flags": fact_check_analysis.get("flags", []),
                    "risk_level": fact_check_analysis.get("risk_level", "unknown"),
                    "requires_manual_review": fact_check_analysis.get("requires_manual_review", False),
                    "summary": fact_check_analysis.get("summary", ""),
                    "analyzed_claims": fact_check_analysis.get("analyzed_claims", [])
                }
            except Exception as fc_error:
                logger.error(f"❌ [Callback] Fact-checking failed: {fc_error}")
                fact_check_result = {
                    "status": "failed",
                    "error": str(fc_error)
                }

            logger.info(f"✅ [Callback] Fact-checking: {fact_check_result.get('status')}")

            # ==========================================
            # STEP 4: Run Source Evaluation (Sequential)
            # ==========================================
            logger.info(f"📰 [Callback] Running source evaluation")

            # Import and call as regular function
            from app.services.source_evaluation_service import source_evaluation_service

            try:
                source_eval_result = source_evaluation_service.evaluate_instagram_user(instagram_user)
            except Exception as se_error:
                logger.error(f"❌ [Callback] Source evaluation failed: {se_error}")
                source_eval_result = {
                    "status": "failed",
                    "error": str(se_error)
                }

            logger.info(f"✅ [Callback] Source evaluation: {source_eval_result.get('status')}")

            # ==========================================
            # STEP 4.5: Verify Claims with Web Search (Sequential)
            # ==========================================
            logger.info(f"🔍 [Callback] Verifying claims with web search")

            claim_verification_result = {"status": "skipped"}

            # Only verify if we have claims and fact-checking succeeded
            if (fact_check_result.get("status") == "completed" and
                fact_check_result.get("claim_extraction", {}).get("has_claims")):

                try:
                    from app.services.claude_claim_verifier import claude_claim_verifier

                    # Get analyzed claims
                    claims_to_verify = fact_check_result.get("analyzed_claims", [])

                    if claims_to_verify:
                        # Verify claims
                        claim_verification_result = claude_claim_verifier.verify_claims(
                            claims=claims_to_verify,
                            post_context=f"Instagram post by @{instagram_user.get('username', 'unknown')}: {caption[:200]}"
                        )
                        logger.info(f"✅ [Callback] Verified {claim_verification_result.get('total_verified', 0)} claims")
                    else:
                        logger.info(f"ℹ️ [Callback] No claims to verify")

                except Exception as cv_error:
                    logger.error(f"❌ [Callback] Claim verification failed: {cv_error}")
                    claim_verification_result = {
                        "status": "error",
                        "error": str(cv_error)
                    }
            else:
                logger.info(f"ℹ️ [Callback] Skipping claim verification (no claims or fact-check failed)")

            # ==========================================
            # STEP 5: Aggregate Results
            # ==========================================
            post_type = post_info.get("type", "")
            image_urls = post_info.get("images", [])
            video_urls = post_info.get("videos", [])

            # Extract OCR text for display
            ocr_text = None
            if ocr_result and "combined" in ocr_result:
                ocr_text = ocr_result.get("combined", {}).get("combined_text")

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
                "claim_verification": claim_verification_result,
                "source_credibility": source_eval_result,
                "ocr_text": ocr_text  # Add extracted text for report display
            }

            # ==========================================
            # STEP 6: Calculate Trust Score & Generate Card
            # ==========================================
            logger.info(f"🎯 [Callback] Calculating trust score and generating TrustCard")

            # Use centralized calculator with card generation
            score_result = calculate_trust_score(
                results=results,
                analysis_id=analysis_id,
                post_info=post_info,
                generate_card=True
            )

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

            # Add TrustCard to results if generated
            if score_result.trust_card:
                results["trust_card"] = score_result.trust_card.model_dump()
                logger.info(f"✅ [Callback] TrustCard included in results")
            else:
                logger.warning(f"⚠️ [Callback] No TrustCard generated")

            # Calculate processing time
            processing_time = int(time.time() - created_timestamp)

            # ==========================================
            # STEP 7: Update Database
            # ==========================================
            crud_analysis.update_results(
                db=db,
                analysis_id=UUID(analysis_id),
                results=results,
                trust_score=trust_score,
                processing_time=processing_time,
                content=post_info  # Save Instagram post metadata
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

            logger.info(f"✅ [Callback] Analysis complete!")
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
            logger.error(f"❌ [Callback] Analysis failed: {e}")

            # Update analysis status to failed
            analysis = crud_analysis.get_by_id(db, UUID(analysis_id))
            if analysis:
                analysis.status = "failed"
                analysis.error_message = str(e)
                db.commit()

            return {
                "status": "error",
                "error": str(e)
            }


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
            # STEP 2: Run Parallel Analyses with Chord Pattern
            # ==========================================
            logger.info(f"⚡ [Orchestrator] Starting parallel analysis tasks")
            logger.info(f"   Images: {len(image_urls)}, Videos: {len(video_urls)}")

            # Store timestamp for processing time calculation
            created_timestamp = analysis.created_at.timestamp()

            # Create parallel task group - these run SIMULTANEOUSLY
            parallel_tasks = group([
                run_ai_detection.s(image_urls),
                run_ocr_extraction.s(image_urls, caption),
                run_deepfake_detection.s(video_urls, image_urls, post_type)
            ])

            # Use chord: parallel_tasks | callback
            # The callback receives the list of results from parallel tasks
            workflow = chord(parallel_tasks)(
                complete_analysis.s(
                    analysis_id=analysis_id,
                    post_info=post_info,
                    caption=caption,
                    instagram_user=instagram_user,
                    instagram_url=instagram_url,
                    created_timestamp=created_timestamp
                )
            )

            logger.info(f"✅ [Orchestrator] Parallel tasks launched with callback")
            logger.info(f"   Workflow will complete asynchronously")

            # Return immediately - callback will handle the rest
            return {
                "status": "processing",
                "analysis_id": analysis_id,
                "message": "Parallel analysis in progress"
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
