from pydantic import BaseModel, ConfigDict, Field


class ContentEdit(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=255)
    body: str = Field(min_length=1, max_length=40_000)


class ContentCreate(ContentEdit):
    slug: str = Field(min_length=1, max_length=120, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class ContentSummary(BaseModel):
    id: int
    title: str
    slug: str
    keyword: str | None
    status: str
    site_id: int | None
    published_url: str | None

    model_config = ConfigDict(from_attributes=True)


class ContentRead(ContentSummary):
    body: str
    reddit_thread_id: str | None
    owner_id: int
