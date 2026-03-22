class SerpService:
	def search_keywords(self, query: str, limit: int = 10) -> dict[str, object]:
		return {"query": query, "limit": limit, "results": []}
