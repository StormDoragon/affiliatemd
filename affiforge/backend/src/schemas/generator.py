from pydantic import BaseModel, Field


class RedditScanRequest(BaseModel):
    query: str
    subreddit: str = "all"
    limit: int = Field(default=10, ge=1, le=50)


class RedditScanResponse(BaseModel):
    query: str
    subreddit: str
    topics: list[dict[str, str]]


class GeneratePostRequest(BaseModel):
    site_id: int
    primary_keyword: str
    reddit_thread_id: str
    pain_point: str


class PublishPostRequest(BaseModel):
    site_id: int


class ClusterGenerateRequest(BaseModel):
    seed_keyword: str
    audience: str
    cluster_size: int = Field(default=8, ge=3, le=25)


class ClusterItem(BaseModel):
    keyword: str
    title: str
    search_intent: str
    brief: str


class ClusterGenerateResponse(BaseModel):
    seed_keyword: str
    items: list[ClusterItem]
