import re
from uuid import uuid4

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from ..config import settings
from ..dependencies import get_current_user, get_db
from ..models.content_item import ContentItem
from ..models.user import User
from ..schemas.generator import (
    ClusterGenerateRequest,
    ClusterGenerateResponse,
    GeneratePostRequest,
    RedditScanRequest,
    RedditScanResponse,
)
from ..services.draft_generation import create_cluster, create_draft
from ..services.reddit_service import RedditService
from ..services.usage_guardrails import check_generation
from .sites import get_owned_site

router = APIRouter(prefix="/generator", tags=["generator"])


@router.post("/cluster", response_model=ClusterGenerateResponse)
def generate_cluster(
    payload: ClusterGenerateRequest,
    current_user: User = Depends(get_current_user),
) -> ClusterGenerateResponse:
    check_generation(current_user.id, "cluster", 0.02)
    items = create_cluster(payload.seed_keyword, payload.audience, payload.cluster_size)
    return ClusterGenerateResponse(
        seed_keyword=payload.seed_keyword, items=items, demo=settings.demo_mode
    )


@router.post("/reddit-scan", response_model=RedditScanResponse)
def reddit_scan(
    payload: RedditScanRequest, current_user: User = Depends(get_current_user)
) -> RedditScanResponse:
    check_generation(current_user.id, "reddit", 0)
    result = RedditService().discover_topics(payload.subreddit, payload.query, payload.limit)
    return RedditScanResponse(
        query=payload.query,
        subreddit=payload.subreddit,
        topics=result["topics"],
        demo=settings.demo_mode,
    )


@router.post("/generate", status_code=status.HTTP_201_CREATED)
def generate_post(
    payload: GeneratePostRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    get_owned_site(db, payload.site_id, current_user.id)
    owner_id = current_user.id
    db.rollback()
    check_generation(owner_id, "draft", 0.02)
    draft = create_draft(payload.primary_keyword, payload.pain_point)
    slug = re.sub(r"[^a-z0-9]+", "-", draft.title.lower()).strip("-")[:80].rstrip("-") or "post"
    post = ContentItem(
        **draft.model_dump(),
        slug=f"{slug}-{uuid4().hex[:12]}",
        keyword=payload.primary_keyword,
        reddit_thread_id=payload.reddit_thread_id or None,
        status="draft",
        site_id=payload.site_id,
        owner_id=owner_id,
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return {
        "post_id": post.id,
        "status": post.status,
        "title": post.title,
        "demo": settings.demo_mode,
    }
