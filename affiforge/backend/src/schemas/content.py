from pydantic import BaseModel, ConfigDict


class ContentCreate(BaseModel):
    title: str
    slug: str
    body: str


class ContentRead(BaseModel):
    id: int
    title: str
    slug: str
    body: str
    keyword: str | None
    reddit_thread_id: str | None
    status: str
    site_id: int | None
    owner_id: int

    model_config = ConfigDict(from_attributes=True)
