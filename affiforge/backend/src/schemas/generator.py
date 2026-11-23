from pydantic import BaseModel, ConfigDict, Field


class GeneratorInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)


class RedditScanRequest(GeneratorInput):
    query: str = Field(min_length=2, max_length=255)
    subreddit: str = Field(default="all", min_length=2, max_length=21, pattern=r"^[A-Za-z0-9_]+$")
    limit: int = Field(default=10, ge=1, le=25)


class RedditScanResponse(BaseModel):
    query: str
    subreddit: str
    topics: list[dict[str, str]]
    demo: bool


class GeneratePostRequest(GeneratorInput):
    site_id: int = Field(gt=0)
    primary_keyword: str = Field(min_length=2, max_length=255)
    reddit_thread_id: str = Field(default="", max_length=255)
    pain_point: str = Field(min_length=2, max_length=1000)


class PublishPostRequest(BaseModel):
    site_id: int = Field(gt=0)


class ClusterGenerateRequest(GeneratorInput):
    seed_keyword: str = Field(min_length=2, max_length=255)
    audience: str = Field(min_length=2, max_length=255)
    cluster_size: int = Field(default=8, ge=3, le=25)


class ClusterItem(BaseModel):
    keyword: str = Field(min_length=1, max_length=255)
    title: str = Field(min_length=1, max_length=255)
    search_intent: str = Field(min_length=1, max_length=100)
    brief: str = Field(min_length=1, max_length=1200)


class ClusterGenerateResponse(BaseModel):
    seed_keyword: str
    items: list[ClusterItem]
    demo: bool
