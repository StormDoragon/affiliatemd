class AIService:
	def generate_article_outline(self, keyword: str) -> dict[str, list[str]]:
		return {
			"keyword": keyword,
			"sections": [
				f"What is {keyword}?",
				f"Best {keyword} options in 2026",
				"How to choose the right option",
			],
		}
