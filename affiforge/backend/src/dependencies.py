from collections.abc import Generator
from hmac import compare_digest

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .crud.users import get_user_by_email
from .db import SessionLocal
from .models.user import User
from .security import decode_access_token, password_version
from .services.usage_guardrails import limit_requests

bearer = HTTPBearer(auto_error=False)


def get_db() -> Generator[Session, None, None]:
    with SessionLocal() as db:
        yield db


def get_current_user(
    authorization: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    credentials_error = HTTPException(
        401,
        "Sign in to continue",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not authorization:
        raise credentials_error
    try:
        email, version = decode_access_token(authorization.credentials)
    except ValueError as exc:
        raise credentials_error from exc

    user = get_user_by_email(db, email)
    if (
        user is None
        or not user.is_active
        or not compare_digest(version, password_version(user.hashed_password))
    ):
        raise credentials_error
    return user


def enforce_provider_use(owner_id: int) -> None:
    limit_requests(f"provider:{owner_id}", 15)
    limit_requests("provider:all", 120)
