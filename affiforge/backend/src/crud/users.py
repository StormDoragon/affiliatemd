from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models.user import User
from ..schemas.user import UserCreate
from ..security import get_password_hash


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(func.lower(User.email) == email.lower()).first()


def create_user(db: Session, payload: UserCreate) -> User:
    user = User(
        email=str(payload.email).lower(),
        full_name=payload.full_name,
        hashed_password=get_password_hash(payload.password),
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
