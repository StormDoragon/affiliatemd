class AdRevenueOptimizer:
    def optimize(
        self,
        *,
        ga4_sessions: int,
        pageviews: int,
        adsense_revenue: float,
        adsense_ctr: float,
    ) -> dict[str, float | list[str]]:
        rpm = (adsense_revenue / pageviews * 1000) if pageviews > 0 else 0.0
        session_depth = (pageviews / ga4_sessions) if ga4_sessions > 0 else 0.0

        suggestions: list[str] = []

        if rpm < 8:
            suggestions.append("Test higher-RPM ad placements above the fold on comparison content.")
        if adsense_ctr < 0.01:
            suggestions.append("Increase ad visibility with cleaner spacing around high-intent sections.")
        if session_depth < 1.5:
            suggestions.append("Add internal links between cluster pages to improve page depth per visit.")
        if not suggestions:
            suggestions.append("Ad revenue signals are healthy; run controlled A/B tests on ad density.")

        projected_uplift = round(rpm * 0.15, 2)

        return {
            "rpm": round(rpm, 2),
            "session_depth": round(session_depth, 2),
            "projected_rpm_uplift": projected_uplift,
            "suggestions": suggestions,
        }
