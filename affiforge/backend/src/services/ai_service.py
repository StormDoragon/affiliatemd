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

	def generate_basic_post(self, keyword: str, pain_point: str) -> dict[str, str]:
		title = f"Best {keyword} for {pain_point}: Field-Tested Picks"
		body = (
			f"If you're dealing with {pain_point}, choosing the right {keyword} is the difference "
			"between daily friction and a setup that just works.\n\n"
			"In this guide, we compare practical options, explain trade-offs, and share a clear buying "
			"framework so you can pick confidently."
		)
		return {"title": title, "body": body}

	def generate_content_cluster(self, seed_keyword: str, audience: str, cluster_size: int) -> list[dict[str, str]]:
		cluster = []
		for index in range(1, cluster_size + 1):
			cluster.append(
				{
					"keyword": f"{seed_keyword} {index}",
					"title": f"{seed_keyword.title()} Guide #{index} for {audience}",
					"search_intent": "commercial",
					"brief": f"Address {audience} pain points with product-led recommendations and buyer triggers.",
				}
			)
		return cluster
