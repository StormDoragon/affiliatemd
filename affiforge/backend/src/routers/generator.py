from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from ..dependencies import enforce_api_guardrails, get_current_user, get_db
from ..models.content_item import ContentItem
from ..models.site import Site
from ..models.user import User
from ..schemas.generator import (
    ClusterGenerateRequest,
    ClusterGenerateResponse,
    GeneratePostRequest,
    RedditScanRequest,
    RedditScanResponse,
)
from ..services.ai_service import AIService
from ..services.reddit_service import RedditService

router = APIRouter(prefix="/generator", tags=["generator"])


@router.post("/cluster", response_model=ClusterGenerateResponse)
def generate_cluster(
    payload: ClusterGenerateRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
) -> ClusterGenerateResponse:
    # Rough estimated cost scales with cluster size; blocked if it exceeds configured cap.
    enforce_api_guardrails(
        request,
        current_user,
        estimated_cost=round(0.01 * payload.cluster_size, 4),
        endpoint="generator.cluster",
    )

    ai = AIService()
    items = ai.generate_content_cluster(
        seed_keyword=payload.seed_keyword,
        audience=payload.audience,
        cluster_size=payload.cluster_size,
    )
    return ClusterGenerateResponse(seed_keyword=payload.seed_keyword, items=items)


@router.post("/reddit-scan", response_model=RedditScanResponse)
def reddit_scan(
    payload: RedditScanRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
) -> RedditScanResponse:
    # Reddit scan is low LLM-cost but still rate-limited and usage-logged.
    enforce_api_guardrails(
        request,
        current_user,
        estimated_cost=0.002,
        endpoint="generator.reddit_scan",
    )

    scanner = RedditService()
    result = scanner.discover_topics(subreddit=payload.subreddit, query=payload.query, limit=payload.limit)
    topics = [
        {
            "thread_id": str(topic["thread_id"]),
            "title": str(topic["title"]),
            "pain_point": str(topic["pain_point"]),
        }
        for topic in list(result["topics"])
    ]
    return RedditScanResponse(query=payload.query, subreddit=payload.subreddit, topics=topics)


@router.post("/generate", status_code=status.HTTP_201_CREATED)
def generate_post(
    payload: GeneratePostRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, str | int]:
    enforce_api_guardrails(
        request,
        current_user,
        estimated_cost=0.02,
        endpoint="generator.generate_post",
    )

    site = db.query(Site).filter(Site.id == payload.site_id, Site.user_id == current_user.id).first()
    if site is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")

    ai = AIService()
    generated = ai.generate_basic_post(keyword=payload.primary_keyword, pain_point=payload.pain_point)
    slug = generated["title"].lower().replace(" ", "-")[:80]

    post = ContentItem(
        title=generated["title"],
        slug=slug,
        body=generated["body"],
        keyword=payload.primary_keyword,
        reddit_thread_id=payload.reddit_thread_id,
        status="draft",
        site_id=site.id,
        owner_id=current_user.id,
    )
    db.add(post)
    db.commit()
    db.refresh(post)

    return {"post_id": post.id, "status": post.status, "title": post.title}
