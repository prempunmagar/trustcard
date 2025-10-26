"""
Report Generation Service

Creates HTML and text reports from analysis results.
"""

from jinja2 import Environment, FileSystemLoader, select_autoescape
from datetime import datetime
import os
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generate TrustCard reports"""

    def __init__(self):
        # Setup Jinja2 environment
        template_dir = os.path.join(os.path.dirname(__file__), '..', 'templates')
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(['html', 'xml'])
        )

    def generate_html_report(
        self,
        analysis_id: str,
        post_info: Dict,
        score_data: Dict,
        results: Dict,
        community_feedback: Dict = None
    ) -> str:
        """
        Generate HTML report card.

        Args:
            analysis_id: Analysis ID
            post_info: Instagram post information
            score_data: Trust score breakdown
            results: Full analysis results
            community_feedback: Community votes and comments

        Returns:
            str: HTML report
        """
        try:
            template = self.env.get_template('report_card.html')

            # Extract score data
            score = score_data.get("final_score", score_data.get("score", 0))
            grade = score_data.get("grade", "F")
            grade_info = score_data.get("grade_info", {})
            assessment = grade_info.get("description", "Analysis complete")

            # Get grade color
            grade_color = self._get_grade_color(score)

            # Build components list
            components = self._build_components_list(results, score_data)

            # Build findings list
            findings = self._build_findings_list(results, score_data)

            # Get recommendation
            recommendation = self._get_recommendation(score, grade, results)

            # Process community feedback
            if not community_feedback:
                community_feedback = {
                    "total_votes": 0,
                    "accurate": 0,
                    "misleading": 0,
                    "false": 0
                }

            total_votes = community_feedback.get("total_votes", 0)
            accurate_count = community_feedback.get("accurate", 0)
            misleading_count = community_feedback.get("misleading", 0)
            false_count = community_feedback.get("false", 0)

            # Calculate percentages
            if total_votes > 0:
                accurate_percent = round((accurate_count / total_votes) * 100)
                misleading_percent = round((misleading_count / total_votes) * 100)
                false_percent = round((false_count / total_votes) * 100)
            else:
                accurate_percent = 0
                misleading_percent = 0
                false_percent = 0

            # Get user info
            user_info = post_info.get("user", {})
            username = user_info.get("username", "unknown")

            # Render template
            html = template.render(
                analysis_id=analysis_id,
                post_id=post_info.get("post_id", "unknown"),
                username=username,
                analyzed_date=datetime.utcnow().strftime("%B %d, %Y at %I:%M %p UTC"),
                processing_time=results.get("instagram_extraction", {}).get("processing_time", 0),
                score=score,
                grade=grade,
                grade_color=grade_color,
                assessment=assessment,
                components=components,
                findings=findings,
                recommendation=recommendation,
                total_votes=total_votes,
                accurate_count=accurate_count,
                misleading_count=misleading_count,
                false_count=false_count,
                accurate_percent=accurate_percent,
                misleading_percent=misleading_percent,
                false_percent=false_percent,
                current_year=datetime.utcnow().year
            )

            logger.info(f"✅ Generated HTML report for {analysis_id}")
            return html

        except Exception as e:
            logger.error(f"❌ Failed to generate HTML report: {e}")
            return f"<html><body><h1>Error generating report: {e}</h1></body></html>"

    def _get_grade_color(self, score: float) -> str:
        """Get color for grade"""
        if score >= 90:
            return "#28a745"  # Green
        elif score >= 80:
            return "#20c997"  # Teal
        elif score >= 70:
            return "#ffc107"  # Yellow
        elif score >= 60:
            return "#fd7e14"  # Orange
        else:
            return "#dc3545"  # Red

    def _build_components_list(self, results: Dict, score_data: Dict) -> List[Dict]:
        """Build list of analysis components for display"""
        components = []

        # AI Detection
        ai = results.get("ai_detection", {})
        if ai.get("status") == "completed":
            overall = ai.get("overall", {})
            if overall.get("overall_ai_detected"):
                grade = "D"
                status = "AI detected"
            else:
                grade = "A"
                status = "Authentic"
        else:
            grade = "N/A"
            status = "Not analyzed"

        components.append({
            "name": "AI Detection",
            "grade": grade,
            "status": status
        })

        # Deepfake
        deepfake = results.get("deepfake", {})
        if deepfake.get("status") == "completed":
            video = deepfake.get("video_analysis", {})
            image = deepfake.get("image_analysis", {})

            if video.get("is_deepfake") or image.get("is_manipulated"):
                grade = "F"
                status = "Manipulation detected"
            else:
                grade = "A"
                status = "No manipulation"
        else:
            grade = "N/A"
            status = "Not analyzed"

        components.append({
            "name": "Deepfake Check",
            "grade": grade,
            "status": status
        })

        # Fact-checking
        fact_check = results.get("fact_check", {})
        if fact_check.get("status") == "completed":
            overall = fact_check.get("overall_assessment", {})
            credibility = overall.get("overall_credibility")

            if credibility == "HIGH_CREDIBILITY":
                grade = "A"
                status = "Claims verified"
            elif credibility == "MIXED_CREDIBILITY":
                grade = "C"
                status = "Some concerns"
            elif credibility == "LOW_CREDIBILITY":
                grade = "F"
                status = "False claims"
            else:
                grade = "B"
                status = "Inconclusive"
        else:
            grade = "N/A"
            status = "Not analyzed"

        components.append({
            "name": "Fact Verification",
            "grade": grade,
            "status": status
        })

        # Source Credibility
        source = results.get("source_credibility", {})
        if source.get("status") == "completed":
            assessment = source.get("assessment", {})
            avg_rel = assessment.get("avg_reliability_score", 0.5)

            if avg_rel > 0.8:
                grade = "A"
                status = "Highly credible"
            elif avg_rel > 0.6:
                grade = "B"
                status = "Generally good"
            elif avg_rel > 0.4:
                grade = "C"
                status = "Mixed quality"
            else:
                grade = "D"
                status = "Questionable"
        else:
            grade = "N/A"
            status = "Not analyzed"

        components.append({
            "name": "Source Credibility",
            "grade": grade,
            "status": status
        })

        return components

    def _build_findings_list(self, results: Dict, score_data: Dict) -> List[str]:
        """Build list of key findings"""
        findings = []

        # AI Detection finding
        ai = results.get("ai_detection", {})
        if ai.get("status") == "completed":
            overall = ai.get("overall", {})
            if overall.get("overall_ai_detected"):
                findings.append("AI-generated images detected - content may be synthetic")
            else:
                findings.append("Images appear authentic (no AI generation detected)")

        # Fact-checking finding
        fact_check = results.get("fact_check", {})
        if fact_check.get("status") == "completed":
            claims_count = fact_check.get("claims_extracted", 0)
            if claims_count > 0:
                overall = fact_check.get("overall_assessment", {})
                likely_false = overall.get("likely_false", 0)
                questionable = overall.get("questionable", 0)
                likely_true = overall.get("likely_true", 0)

                if likely_false > 0:
                    findings.append(f"{likely_false} claims appear false, requires verification")
                elif questionable > 0:
                    findings.append(f"{questionable} questionable claims need more evidence")
                elif likely_true > 0:
                    findings.append(f"{likely_true} claims verified as credible")

        # Source finding
        source = results.get("source_credibility", {})
        if source.get("status") == "completed":
            assessment = source.get("assessment", {})

            if assessment.get("has_conspiracy"):
                findings.append("Links to conspiracy theory websites")
            elif assessment.get("has_unreliable_sources"):
                findings.append("Links to unreliable or low-credibility sources")
            elif assessment.get("has_satire"):
                findings.append("Contains satire content (not intended as factual)")
            else:
                external = assessment.get("external_sources", [])
                if external:
                    findings.append(f"Cites {len(external)} external source(s)")

        # Community finding
        findings.append("Community feedback helps validate AI analysis")

        if not findings:
            findings.append("No significant issues detected in analysis")

        return findings

    def _get_recommendation(self, score: float, grade: str, results: Dict) -> str:
        """Get recommendation based on score"""
        if score >= 85:
            return "Content appears highly credible. Still verify important claims independently."
        elif score >= 70:
            return "Approach with healthy skepticism. Verify key claims before sharing."
        elif score >= 60:
            return "Exercise caution. Multiple concerns detected. Verify before trusting."
        else:
            return "Do not share without thorough verification. Significant credibility concerns detected."


# Singleton instance
report_generator = ReportGenerator()
