from ..config import settings

try:
	import praw
except ImportError:  # pragma: no cover
	praw = None


class RedditService:
	def discover_topics(self, subreddit: str, query: str, limit: int = 25) -> dict[str, object]:
		if (
			praw is None
			or not settings.reddit_client_id
			or not settings.reddit_client_secret
		):
			return self._fallback(subreddit=subreddit, query=query, limit=limit)

		try:
			client = praw.Reddit(
				client_id=settings.reddit_client_id,
				client_secret=settings.reddit_client_secret,
				user_agent=settings.reddit_user_agent,
			)
			target = client.subreddit(subreddit)
			topics = []
			for post in target.search(query, sort="relevance", limit=limit):
				topics.append(
					{
						"thread_id": post.id,
						"title": post.title,
						"pain_point": query,
					}
				)
			return {"subreddit": subreddit, "limit": limit, "topics": topics}
		except Exception:
			return self._fallback(subreddit=subreddit, query=query, limit=limit)

	def _fallback(self, subreddit: str, query: str, limit: int) -> dict[str, object]:
		topics = [
			{
				"thread_id": f"{subreddit}-demo-{idx}",
				"title": f"[{query}] advice request #{idx}",
				"pain_point": query,
			}
			for idx in range(1, limit + 1)
		]
		return {"subreddit": subreddit, "limit": limit, "topics": topics}
