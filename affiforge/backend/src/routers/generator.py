from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..dependencies import get_current_user, get_db
from ..models.content_item import ContentItem
from ..models.site import Site
from ..models.user import User
from ..schemas.generator import GeneratePostRequest, RedditScanRequest, RedditScanResponse
from ..services.ai_service import AIService
from ..services.reddit_service import RedditService

router = APIRouter(prefix="/generator", tags=["generator"])


@router.post("/reddit-scan", response_model=RedditScanResponse)
def reddit_scan(
    payload: RedditScanRequest,
    _: User = Depends(get_current_user),
) -> RedditScanResponse:
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, str | int]:
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
