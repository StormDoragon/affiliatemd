from decimal import Decimal, ROUND_HALF_UP


class ProfitShareEngine:
    def __init__(self, split_ratio: Decimal = Decimal("0.30")) -> None:
        self.split_ratio = split_ratio

    def calculate(self, revenue: float, enabled: bool) -> dict[str, bool | float]:
        revenue_decimal = Decimal(str(revenue))
        if not enabled:
            return {
                "enabled": False,
                "total_revenue": float(revenue_decimal),
                "platform_share": 0.0,
                "user_share": float(revenue_decimal),
                "ratio": float(self.split_ratio),
            }

        platform_share = (revenue_decimal * self.split_ratio).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        user_share = (revenue_decimal - platform_share).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return {
            "enabled": True,
            "total_revenue": float(revenue_decimal),
            "platform_share": float(platform_share),
            "user_share": float(user_share),
            "ratio": float(self.split_ratio),
        }
