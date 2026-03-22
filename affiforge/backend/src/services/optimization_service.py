class OptimizationService:
    def suggest(self, *, posts_count: int, total_revenue: float, epc: float) -> list[str]:
        suggestions: list[str] = []

        if posts_count < 3:
            suggestions.append("Publish at least 3 comparison posts to diversify affiliate entry points.")

        if total_revenue <= 0:
            suggestions.append("Run a fresh Reddit scan and target a tighter pain-point keyword cluster.")

        if epc < 0.25:
            suggestions.append("Improve product-intent CTAs near comparison tables to lift EPC.")

        if not suggestions:
            suggestions.append("Keep current strategy and A/B test headline variants for incremental gains.")

        return suggestions
