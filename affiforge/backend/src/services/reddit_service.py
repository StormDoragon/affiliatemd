import praw
from praw.exceptions import PRAWException
from prawcore import PrawcoreException

from ..config import settings
from .provider_errors import IntegrationFailed, IntegrationUnavailable


class RedditService:
    def discover_topics(self, subreddit: str, query: str, limit: int = 25) -> dict:
        if settings.demo_mode:
            topics = [
                {
                    "thread_id": f"{subreddit}-demo-{idx}",
                    "title": f"{query} example question {idx}",
                    "pain_point": query,
                    "url": "",
                }
                for idx in range(1, limit + 1)
            ]
        else:
            if not settings.reddit_client_id or not settings.reddit_client_secret:
                raise IntegrationUnavailable("Reddit")
            try:
                with praw.Reddit(
                    client_id=settings.reddit_client_id,
                    client_secret=settings.reddit_client_secret,
                    user_agent=settings.reddit_user_agent,
                    timeout=8,
                ) as client:
                    topics = [
                        {
                            "thread_id": post.id,
                            "title": post.title,
                            "pain_point": post.title,
                            "url": f"https://www.reddit.com/comments/{post.id}/",
                        }
                        for post in client.subreddit(subreddit).search(
                            query, sort="relevance", limit=limit
                        )
                    ]
            except (PRAWException, PrawcoreException) as exc:
                raise IntegrationFailed("Reddit") from exc
        return {"subreddit": subreddit, "limit": limit, "topics": topics}
