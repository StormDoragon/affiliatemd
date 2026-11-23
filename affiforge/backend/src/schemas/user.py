from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=12, max_length=128)

    @field_validator("full_name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Enter a name")
        return value


class UserRead(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    stripe_customer_id: str | None
    profitshare_enabled: bool
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
