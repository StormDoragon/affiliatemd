"""
Generator router: Create content clusters from Reddit opportunities.
Handles cost limits, async task queuing, and revenue attribution setup.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.orm import Session
import uuid

from ..dependencies import get_current_user, get_db
from ..models.user import User
from ..models.site import Site
from ..models.cluster import Cluster
from ..schemas.generator import (
    ClusterGenerateRequest,
    ClusterGenerateResponse,
    RedditScanRequest,
    RedditScanResponse,
)
from ..services.ai_service import AIService, CostExceededError
from ..services.reddit_service import RedditService
from ..tasks.celery_app import generate_cluster_task, publish_to_wordpress_task

router = APIRouter(prefix="/api/v1/generator", tags=["generator"])


@router.post("/cluster-generate", response_model=dict, status_code=status.HTTP_202_ACCEPTED)
async def generate_cluster(
    payload: ClusterGenerateRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Queue cluster generation task (async).
    
    Request:
    {
        "site_id": "uuid",
        "reddit_data": {"title": "...", "selftext": "...", "id": "..."},
        "niche": "espresso_machines",
        "audience": "coffee enthusiasts"
    }
    
    Response: {
        "status": "queued",
        "task_id": "...",
        "estimate_cost": "$0.08"
    }
    """
    
    # Validate user owns the site
    site = db.query(Site).filter_by(
        id=payload.site_id,
        user_id=current_user.id
    ).first()
    
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    
    # Check user tier has access to clustering
    if current_user.tier == "starter":
        raise HTTPException(
            status_code=403,
            detail="Cluster generation requires Pro or Elite tier"
        )
    
    # Estimate cost before queuing
    estimated_tokens = len(str(payload.reddit_data).split()) * 3  # rough est
    estimated_cost = (estimated_tokens * 0.00008) / 1000  # GPT-4o pricing
    
    if estimated_cost > float(current_user.max_cost_per_task or 0.12):
        raise HTTPException(
            status_code=400,
            detail=f"Estimated cost ${estimated_cost:.4f} exceeds limit ${current_user.max_cost_per_task}"
        )
    
    # Queue async task
    task = generate_cluster_task.delay(
        user_id=str(current_user.id),
        site_id=str(payload.site_id),
        reddit_data=payload.reddit_data,
        niche=payload.niche,
        audience=payload.audience,
    )
    
    return {
        "status": "queued",
        "task_id": task.id,
        "estimated_cost": f"${estimated_cost:.4f}",
        "message": "Cluster generation in progress. Check task status for updates.",
    }


@router.get("/cluster-status/{task_id}", response_model=dict)
async def cluster_generation_status(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get status of cluster generation task."""
    from ..tasks.celery_app import celery_app
    
    task = celery_app.AsyncResult(task_id)
    
    if task.state == "PENDING":
        return {"status": "pending", "message": "Task queued, waiting to start..."}
    elif task.state == "STARTED":
        return {"status": "in_progress", "message": "Generating cluster..."}
    elif task.state == "SUCCESS":
        result = task.result
        return {
            "status": "success",
            "cluster_id": result.get("cluster_id"),
            "cost": result.get("cost"),
            "message": "Cluster ready for publishing",
        }
    elif task.state == "FAILURE":
        return {
            "status": "failed",
            "error": str(task.info),
        }
    else:
        return {"status": task.state}


@router.post("/cluster-publish/{cluster_id}", status_code=status.HTTP_202_ACCEPTED)
async def publish_cluster(
    cluster_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Queue cluster publishing to WordPress.
    Each post gets utm_source for affiliate attribution.
    
    Response: {
        "status": "queued",
        "task_id": "...",
        "message": "Publishing in progress..."
    }
    """
    
    cluster = db.query(Cluster).filter_by(cluster_id=cluster_id).first()
    
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")
    
    # Verify user owns site
    site = db.query(Site).filter_by(id=cluster.site_id, user_id=current_user.id).first()
    
    if not site:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    # Queue publish task
    task = publish_to_wordpress_task.delay(
        site_id=str(site.id),
        cluster_id=cluster_id,
    )
    
    return {
        "status": "queued",
        "task_id": task.id,
        "cluster_id": cluster_id,
        "message": "Publishing to WordPress...",
    }


@router.post("/reddit-scan", response_model=RedditScanResponse)
async def reddit_scan(
    payload: RedditScanRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Scan Reddit for pain points in a subreddit.
    Returns top threads matching query with opportunity scores.
    
    Example:
    {
        "subreddit": "Coffee",
        "query": "espresso machine under 500",
        "limit": 10
    }
    """
    
    if current_user.tier == "starter":
        raise HTTPException(
            status_code=403,
            detail="Reddit scanning requires Pro or Elite tier"
        )
    
    scanner = RedditService()
    
    try:
        result = scanner.discover_topics(
            subreddit=payload.subreddit,
            query=payload.query,
            limit=payload.limit,
        )
        
        return RedditScanResponse(
            query=payload.query,
            subreddit=payload.subreddit,
            count=len(result.get("topics", [])),
            topics=result.get("topics", []),
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/optimize-post", response_model=dict)
async def optimize_post(
    post_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get optimization recommendation for existing affiliate post.
    Returns ONE high-impact change (video, table, urgency, etc).
    
    Example response:
    {
        "optimization_type": "video_embed",
        "recommendation": "Add YouTube review video above fold to increase dwell time",
        "estimated_lift": "25-30%",
        "implementation_time_minutes": 15
    }
    """
    
    from ..models.content_item import ContentItem
    
    content = db.query(ContentItem).filter_by(id=post_id).first()
    
    if not content:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Verify access
    site = db.query(Site).filter_by(id=content.site_id, user_id=current_user.id).first()
    if not site:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    ai_service = AIService()
    
    try:
        result = ai_service.optimize_post(
            post_title=content.title,
            conversion_rate=2.5,  # default
            monthly_traffic=max(100, content.monthly_traffic or 100),
        )
        
        if result["status"] != "success":
            raise HTTPException(status_code=500, detail=result.get("error"))
        
        return {
            "status": "success",
            "post_id": post_id,
            "optimization": result.get("optimization", {}),
            "cost": result.get("cost", 0),
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cluster/{site_id}", response_model=list)
async def list_site_clusters(
    site_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List all clusters for a site.
    Includes status, publish status, and estimated earnings.
    """
    
    site = db.query(Site).filter_by(id=site_id, user_id=current_user.id).first()
    
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    
    clusters = db.query(Cluster).filter_by(site_id=site_id).all()
    
    return [
        {
            "cluster_id": c.cluster_id,
            "pillar_title": c.pillar_title,
            "post_count": c.supporting_post_count,
            "status": c.status,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "published_at": c.published_at.isoformat() if c.published_at else None,
        }
        for c in clusters
    ]
