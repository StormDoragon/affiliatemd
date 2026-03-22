class EarningsTracker:
	def summarize(self) -> dict[str, float]:
		return {
			"clicks": 0.0,
			"conversions": 0.0,
			"revenue": 0.0,
			"epc": 0.0,
		}
