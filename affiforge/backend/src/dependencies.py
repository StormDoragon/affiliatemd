from typing import Generator

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from .crud.users import get_user_by_email
from .db import SessionLocal
from .models.user import User
from .security import decode_access_token
from .services.usage_guardrails import usage_guardrails

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/token")


def get_db() -> Generator[Session, None, None]:
	db = SessionLocal()
	try:
		yield db
	finally:
		db.close()


def get_current_user(
	token: str = Depends(oauth2_scheme),
	db: Session = Depends(get_db),
) -> User:
	credentials_error = HTTPException(
		status_code=status.HTTP_401_UNAUTHORIZED,
		detail="Could not validate credentials",
		headers={"WWW-Authenticate": "Bearer"},
	)
	try:
		email = decode_access_token(token)
	except ValueError as exc:
		raise credentials_error from exc

	user = get_user_by_email(db, email)
	if user is None:
		raise credentials_error
	return user


def _client_ip(request: Request) -> str:
	x_forwarded_for = request.headers.get("x-forwarded-for")
	if x_forwarded_for:
		return x_forwarded_for.split(",", maxsplit=1)[0].strip()
	if request.client:
		return request.client.host
	return "unknown"


def enforce_api_guardrails(
	request: Request,
	current_user: User,
	*,
	estimated_cost: float,
	endpoint: str,
) -> dict[str, float | int]:
	"""Enforce per-user API guardrails and emit usage logs/alerts."""

	subject = f"user:{current_user.id}"
	return usage_guardrails.enforce(
		subject=subject,
		endpoint=endpoint,
		estimated_cost=estimated_cost,
		client_ip=_client_ip(request),
	)
