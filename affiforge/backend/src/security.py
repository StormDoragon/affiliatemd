from datetime import UTC, datetime, timedelta
from hashlib import sha256

import jwt
from passlib.context import CryptContext

from .config import settings

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], pbkdf2_sha256__default_rounds=600_000)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except ValueError:
        return False


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def password_version(hashed_password: str) -> str:
    return sha256(hashed_password.encode()).hexdigest()


def create_access_token(
    subject: str, hashed_password: str, expires_minutes: int | None = None
) -> str:
    expire_delta = timedelta(minutes=expires_minutes or settings.access_token_expire_minutes)
    expire = datetime.now(UTC) + expire_delta
    payload = {"sub": subject, "exp": expire, "pwd": password_version(hashed_password)}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> tuple[str, str]:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            options={"require": ["exp", "sub", "pwd"]},
        )
        subject = payload.get("sub")
        if not subject:
            raise ValueError("Token subject missing")
        return str(subject), str(payload.get("pwd", ""))
    except (jwt.InvalidTokenError, ValueError) as exc:
        raise ValueError("Invalid token") from exc
