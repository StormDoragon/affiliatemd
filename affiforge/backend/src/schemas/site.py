from pydantic import BaseModel, ConfigDict


class SiteCreate(BaseModel):
    wp_url: str
    wp_username: str
    wp_app_password: str
    amazon_tag: str


class SiteRead(BaseModel):
    id: int
    user_id: int
    wp_url: str
    wp_username: str
    amazon_tag: str

    model_config = ConfigDict(from_attributes=True)
