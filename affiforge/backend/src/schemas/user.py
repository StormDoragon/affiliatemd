from pydantic import BaseModel, ConfigDict, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str


class UserRead(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    stripe_customer_id: str | None
    profitshare_enabled: bool
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
