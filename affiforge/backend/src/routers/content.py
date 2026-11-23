import re
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..config import settings
from ..dependencies import enforce_provider_use, get_current_user, get_db
from ..models.content_item import ContentItem
from ..models.user import User
from ..schemas.content import ContentCreate, ContentEdit, ContentRead, ContentSummary
from ..schemas.generator import PublishPostRequest
from ..services.credentials import decrypt_password
from ..services.wordpress_service import WordpressService
from .sites import get_owned_site

router = APIRouter(prefix="/content", tags=["content"])


def owned_content(
    db: Session, owner_id: int, content_id: int, *, lock: bool = False
) -> ContentItem:
    statement = db.query(ContentItem).filter(
        ContentItem.id == content_id, ContentItem.owner_id == owner_id
    )
    if lock:
        statement = statement.populate_existing().with_for_update()
    content = statement.first()
    if content is None:
        raise HTTPException(404, "Content not found")
    return content


@router.post("/", response_model=ContentRead, status_code=status.HTTP_201_CREATED)
def create_content(
    payload: ContentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ContentItem:
    content = ContentItem(**payload.model_dump(), status="draft", owner_id=current_user.id)
    db.add(content)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "You already have a draft with that slug") from exc
    db.refresh(content)
    return content


@router.get("/", response_model=list[ContentSummary])
def list_content(
    offset: int = Query(0, ge=0),
    limit: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ContentItem]:
    return (
        db.query(ContentItem)
        .filter(ContentItem.owner_id == current_user.id)
        .order_by(ContentItem.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


@router.get("/{content_id}", response_model=ContentRead)
def get_content(
    content_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ContentItem:
    return owned_content(db, current_user.id, content_id)


@router.patch("/{content_id}", response_model=ContentRead)
def update_draft(
    content_id: int,
    payload: ContentEdit,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ContentItem:
    content = owned_content(db, current_user.id, content_id, lock=True)
    if content.status != "draft" or content.publish_key:
        raise HTTPException(
            409, "This draft has a publishing receipt or an unresolved publish attempt"
        )
    content.title = payload.title
    content.body = payload.body
    db.commit()
    db.refresh(content)
    return content


@router.post("/{content_id}/publish")
def publish_content(
    content_id: int,
    payload: PublishPostRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, str | int | None]:
    owner_id = current_user.id
    content = owned_content(db, owner_id, content_id, lock=True)
    if content.status == "published":
        if content.site_id != payload.site_id:
            raise HTTPException(409, "This post was already published to another site")
        return {"post_id": content.id, "status": "published", "url": content.published_url}
    if content.publish_key and content.site_id != payload.site_id:
        raise HTTPException(409, "Retry this publish on its original WordPress site")
    site = get_owned_site(db, payload.site_id, owner_id)
    enforce_provider_use(owner_id)
    if settings.demo_mode:
        return {"post_id": content.id, "status": "demo", "url": None}
    password = decrypt_password(site.wp_app_password)
    if not content.publish_key:
        prefix = (
            re.sub(r"[^a-z0-9]+", "-", content.slug.lower()).strip("-")[:38].rstrip("-") or "post"
        )
        content.publish_key = f"{prefix}-{uuid4().hex[:24]}"
        content.site_id = site.id
        db.commit()
        content = owned_content(db, owner_id, content_id, lock=True)
    if content.status != "published":
        result = WordpressService().publish_post(
            site.wp_url,
            site.wp_username,
            password,
            content.title,
            content.body,
            content.publish_key,
        )
        content.status = result["status"]
        content.published_url = result["url"]
        db.commit()
    return {"post_id": content.id, "status": content.status, "url": content.published_url}
