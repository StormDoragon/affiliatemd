from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator

from ..services.wordpress_service import site_url


class SiteCredentials(BaseModel):
    wp_username: str = Field(min_length=1, max_length=255, pattern=r"^[^:\r\n]+$")
    wp_app_password: SecretStr = Field(min_length=1, max_length=255)
    amazon_tag: str = Field(default="", max_length=64, pattern=r"^[A-Za-z0-9_-]*$")


class SiteCreate(SiteCredentials):
    wp_url: str = Field(max_length=255)

    @field_validator("wp_url")
    @classmethod
    def normalize_wordpress_url(cls, value: str) -> str:
        return site_url(value)


class SiteRead(BaseModel):
    id: int
    user_id: int
    wp_url: str
    wp_username: str
    amazon_tag: str

    model_config = ConfigDict(from_attributes=True)
