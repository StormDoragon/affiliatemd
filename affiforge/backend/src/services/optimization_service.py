"""
Content optimization service: Improve affiliate post performance.
AI-powered suggestions for video embeds, comparison tables, urgency copy, and more.
"""

from datetime import datetime, timedelta
from .ai_service import AIService


class OptimizationService:
    """AI-powered content optimization for affiliate posts."""
    
    def __init__(self):
        self.ai = AIService(model="gpt-4o")
    
    def analyze_post(self, post_title: str, content: str, conversion_rate: float = 2.5) -> dict:
        """
        Analyze post performance and suggest optimizations.
        Returns prioritized list of improvements based on content gaps.
        """
        optimizations = []
        
        # Check 1: Content length
        word_count = len(content.split())
        if word_count < 1000:
            optimizations.append({
                "priority": "high",
                "type": "content_length",
                "issue": f"Post is {word_count} words (target 1200+)",
                "action": "Expand with more product details, comparisons, and FAQs",
                "estimated_impact": "15-20%",
                "time_estimate_mins": 30,
            })
        
        # Check 2: Amazon product links
        amazon_count = content.count("amazon.com") + content.count("amazon link")
        if amazon_count < 3:
            optimizations.append({
                "priority": "high",
                "type": "affiliate_links",
                "issue": f"Only {amazon_count} Amazon links (recommend 3-5 natural placements)",
                "action": "Add product recommendations in comparison sections and CTAs",
                "estimated_impact": "25-30%",
                "time_estimate_mins": 15,
            })
        
        # Check 3: Comparison table
        has_table = "table" in content.lower() or "|" in content
        if not has_table:
            optimizations.append({
                "priority": "high",
                "type": "comparison_table",
                "issue": "No side-by-side product comparison",
                "action": "Create comparison table with 3-5 top products (price, features, ratings)",
                "estimated_impact": "20-28%",
                "time_estimate_mins": 20,
            })
        
        # Check 4: Video embed
        has_video = "youtube" in content.lower() or "video" in content.lower()
        if not has_video:
            optimizations.append({
                "priority": "high",
                "type": "video_embed",
                "issue": "No embedded video (YouTube, demo, tutorial)",
                "action": "Add YouTube review/demo video above fold",
                "estimated_impact": "30-45%",
                "time_estimate_mins": 10,
            })
        
        # Check 5: Clear CTAs
        cta_count = sum(content.lower().count(phrase) for phrase in ["click here", "buy now", "check price", "see on amazon"])
        if cta_count < 3:
            optimizations.append({
                "priority": "medium",
                "type": "call_to_action",
                "issue": f"Only {cta_count} clear CTAs",
                "action": "Add 3-5 compelling CTAs with urgency/scarcity triggers",
                "estimated_impact": "15-22%",
                "time_estimate_mins": 10,
            })
        
        # Check 6: FAQ section with Schema
        has_faq = "faq" in content.lower() or "frequently asked" in content.lower()
        if not has_faq:
            optimizations.append({
                "priority": "medium",
                "type": "faq_schema",
                "issue": "No FAQ section or Schema markup",
                "action": "Add FAQ with JSON-LD FAQPage schema for rich snippets",
                "estimated_impact": "10-15%",
                "time_estimate_mins": 20,
            })
        
        # Check 7: Author credibility
        has_author_bio = "i tested" in content.lower() or "personal experience" in content.lower()
        if not has_author_bio:
            optimizations.append({
                "priority": "low",
                "type": "author_credibility",
                "issue": "Weak author authority signals",
                "action": "Add \"I tested these for 6 months\" + credentials section",
                "estimated_impact": "5-10%",
                "time_estimate_mins": 5,
            })
        
        return {
            "post_title": post_title,
            "word_count": word_count,
            "current_conversion_rate": conversion_rate,
            "total_optimizations": len(optimizations),
            "high_priority": [o for o in optimizations if o["priority"] == "high"],
            "all_optimizations": optimizations,
            "quick_wins_time_total": sum(o.get("time_estimate_mins", 0) for o in optimizations if o["priority"] == "high"),
        }
    
    def get_ai_recommendation(self, post_title: str, conversion_rate: float = 2.5) -> dict:
        """
        Get LangChain AI recommendation for ONE highest-impact optimization.
        """
        result = self.ai.optimize_post(
            post_title=post_title,
            conversion_rate=conversion_rate,
        )
        return result
    
    def suggest(self, *, posts_count: int, total_revenue: float, epc: float) -> list[str]:
        """Legacy method: Strategic suggestions based on account metrics."""
        suggestions: list[str] = []

        if posts_count < 3:
            suggestions.append("✓ Publish at least 3 pillar posts to diversify affiliate entry points and build cluster authority.")

        if total_revenue <= 0:
            suggestions.append("✓ Run Reddit scan + generate cluster for a tight pain-point keyword (e.g., 'budget espresso machine').")

        if epc < 0.25:
            suggestions.append("✓ Improve product CTAs: Add comparison tables, video embeds, and urgency-driven language.")

        if not suggestions:
            suggestions.append("✓ Keep current strategy + A/B test: headlines, product order, CTA placement (expect 10-20% lift).")

        return suggestions
