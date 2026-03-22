from pydantic import BaseModel, ConfigDict


class ScanCreate(BaseModel):
    source: str
    query: str
    summary: str = ""


class ScanRead(BaseModel):
    id: int
    source: str
    query: str
    summary: str
    owner_id: int

    model_config = ConfigDict(from_attributes=True)
