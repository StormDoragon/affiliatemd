from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..dependencies import get_current_user, get_db
from ..models.content_item import ContentItem
from ..models.site import Site
from ..models.user import User
from ..schemas.content import ContentCreate, ContentRead
from ..schemas.generator import PublishPostRequest
from ..services.wordpress_service import WordpressService

router = APIRouter(prefix="/content", tags=["content"])


@router.post("/", response_model=ContentRead, status_code=status.HTTP_201_CREATED)
def create_content(
    payload: ContentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ContentItem:
    content = ContentItem(
        title=payload.title,
        slug=payload.slug,
        body=payload.body,
        status="draft",
        owner_id=current_user.id,
    )
    db.add(content)
    db.commit()
    db.refresh(content)
    return content


@router.get("/", response_model=list[ContentRead])
def list_content(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ContentItem]:
    return db.query(ContentItem).filter(ContentItem.owner_id == current_user.id).all()


@router.get("/{content_id}", response_model=ContentRead)
def get_content(
    content_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ContentItem:
    content = (
        db.query(ContentItem)
        .filter(ContentItem.id == content_id, ContentItem.owner_id == current_user.id)
        .first()
    )
    if content is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content not found")
    return content


@router.post("/{content_id}/publish")
def publish_content(
    content_id: int,
    payload: PublishPostRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, str | int]:
    content = (
        db.query(ContentItem)
        .filter(ContentItem.id == content_id, ContentItem.owner_id == current_user.id)
        .first()
    )
    if content is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content not found")

    site = db.query(Site).filter(Site.id == payload.site_id, Site.user_id == current_user.id).first()
    if site is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")

    publisher = WordpressService()
    publish_result = publisher.publish_post(
        wp_url=site.wp_url,
        wp_username=site.wp_username,
        wp_app_password=site.wp_app_password,
        title=content.title,
        content=content.body,
    )

    content.status = "published"
    content.site_id = site.id
    db.add(content)
    db.commit()

    return {
        "post_id": content.id,
        "status": content.status,
        "url": str(publish_result["url"]),
    }
