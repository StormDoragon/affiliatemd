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
    status: str
    owner_id: int

    model_config = ConfigDict(from_attributes=True)
