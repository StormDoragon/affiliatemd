class RedditService:
	def discover_topics(self, subreddit: str, limit: int = 25) -> dict[str, object]:
		return {"subreddit": subreddit, "limit": limit, "topics": []}
