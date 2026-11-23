from hashlib import sha256

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..config import settings
from ..crud.users import create_user, get_user_by_email
from ..dependencies import get_current_user, get_db
from ..models.user import User
from ..schemas.auth import LoginRequest, TokenResponse
from ..schemas.user import UserCreate, UserRead
from ..security import create_access_token, get_password_hash, verify_password
from ..services.usage_guardrails import limit_requests

router = APIRouter(prefix="/users", tags=["users"])
_dummy_hash = get_password_hash("placeholder for rejected credentials")


@router.get("/registration")
def registration_settings() -> dict[str, bool]:
    return {"enabled": settings.allow_registration}


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register_user(payload: UserCreate, db: Session = Depends(get_db)) -> User:
    if not settings.allow_registration:
        raise HTTPException(403, "Public registration is closed")
    limit_requests("register:all", 20)
    if get_user_by_email(db, str(payload.email)):
        raise HTTPException(409, "This email already has an account")
    try:
        return create_user(db, payload)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "This email already has an account") from exc


@router.post("/token", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    limit_requests("login:all", 300)
    identity = sha256(str(payload.email).lower().encode()).hexdigest()
    limit_requests(f"login:{identity}", 10)
    user = get_user_by_email(db, str(payload.email))
    verified = verify_password(payload.password, user.hashed_password if user else _dummy_hash)
    if not verified or user is None or not user.is_active:
        raise HTTPException(401, "Invalid credentials")
    return TokenResponse(
        access_token=create_access_token(subject=user.email, hashed_password=user.hashed_password),
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.get("/", response_model=list[UserRead])
def list_users(current_user: User = Depends(get_current_user)) -> list[User]:
    return [current_user]
