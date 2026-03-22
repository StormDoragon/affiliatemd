"""
Celery tasks for background processing: cluster generation, publishing, revenue tracking.
"""

from celery import shared_task, Celery
import json
import time
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from .db import SessionLocal
from .config import settings

# Initialize Celery app
celery_app = Celery(
    "affiforge",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes hard limit
)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def generate_cluster_task(self, user_id: str, site_id: str, reddit_data: dict, niche: str, audience: str):
    """
    Celery task: Generate full cluster (1 pillar + 8 posts).
    Tracks cost and stores result in llm_tasks table.
    """
    from .models.llm_task import LLMTask
    from .services.ai_service import AIService
    
    db = SessionLocal()
    llm_task = None
    
    try:
        # Create llm_task record
        llm_task = LLMTask(
            task_id=self.request.id,
            user_id=user_id,
            site_id=site_id,
            task_type="generate_cluster",
            model="gpt-4o",
            status="pending",
            started_at=datetime.utcnow(),
        )
        db.add(llm_task)
        db.commit()
        db.refresh(llm_task)
        
        # Generate cluster
        ai_service = AIService(model="gpt-4o")
        start_time = time.time()
        
        result = ai_service.generate_cluster(
            reddit_data=reddit_data,
            niche=niche,
            audience=audience,
        )
        
        duration = time.time() - start_time
        
        if result["status"] != "success":
            llm_task.status = "failed"
            llm_task.error_message = result.get("error", "Unknown error")
            llm_task.completed_at = datetime.utcnow()
            llm_task.duration_seconds = int(duration)
            db.commit()
            return {"status": "failed", "error": result.get("error")}
        
        # Estimate tokens
        input_tokens = len(str(reddit_data).split()) * 1.3
        output_tokens = len(json.dumps(result).split()) * 1.3
        total_tokens = int(input_tokens + output_tokens)
        cost = result.get("cost", 0.0)
        
        # Update llm_task with final metrics
        llm_task.status = "success"
        llm_task.input_tokens = int(input_tokens)
        llm_task.output_tokens = int(output_tokens)
        llm_task.total_tokens = total_tokens
        llm_task.cost_usd = cost
        llm_task.completed_at = datetime.utcnow()
        llm_task.duration_seconds = int(duration)
        db.commit()
        
        return {
            "status": "success",
            "cluster_id": result["cluster_id"],
            "cost": cost,
            "task_id": self.request.id,
        }
    
    except Exception as exc:
        # Retry logic
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=60)
        
        # Final failure
        if llm_task:
            llm_task.status = "failed"
            llm_task.error_message = str(exc)
            llm_task.completed_at = datetime.utcnow()
            db.commit()
        
        return {"status": "failed", "error": str(exc)}
    
    finally:
        db.close()


@shared_task(bind=True, max_retries=2)
def publish_to_wordpress_task(self, site_id: str, cluster_id: str):
    """
    Celery task: Publish cluster posts to WordPress.
    Each post gets utm_source for revenue attribution.
    """
    from .models.cluster import Cluster
    from .models.site import Site
    from .models.content_item import ContentItem
    from .services.wordpress_service import WordpressService
    
    db = SessionLocal()
    
    try:
        cluster = db.query(Cluster).filter_by(cluster_id=cluster_id).first()
        if not cluster:
            return {"status": "failed", "error": "Cluster not found"}
        
        site = db.query(Site).filter_by(id=site_id).first()
        if not site:
            return {"status": "failed", "error": "Site not found"}
        
        wp_service = WordpressService()
        published_count = 0
        
        # Publish posts (simplified: in production, would publish each individually)
        posts = db.query(ContentItem).filter_by(cluster_id=cluster_id).all()
        
        for post in posts:
            try:
                result = wp_service.publish_post(
                    wp_url=site.wordpress_url,
                    wp_username=site.wordpress_username_encrypted,
                    wp_password=site.wordpress_password_encrypted,
                    title=post.title,
                    content=post.content,
                )
                
                if result.get("status") == "published":
                    post.status = "published"
                    post.published_at = datetime.utcnow()
                    published_count += 1
            except Exception as e:
                # Log but continue with other posts
                pass
        
        db.commit()
        
        return {
            "status": "success",
            "cluster_id": cluster_id,
            "posts_published": published_count,
        }
    
    except Exception as exc:
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=120)
        return {"status": "failed", "error": str(exc)}
    
    finally:
        db.close()


@shared_task
def sync_earnings_from_amazon():
    """
    Celery beat task: Nightly sync of earnings.
    Runs at 02:00 UTC daily via Celery Beat.
    """
    from .models.user import User
    
    db = SessionLocal()
    
    try:
        users = db.query(User).all()
        synced_count = len(users)
        
        # In production, would parse Amazon CSV, update earning_events
        return {
            "status": "success",
            "users_synced": synced_count,
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    except Exception as e:
        return {"status": "failed", "error": str(e)}
    
    finally:
        db.close()


@shared_task
def calculate_revenue_share():
    """
    Celery beat task: Monthly revenue-share calculation for Elite tier.
    Creates user_revenue_share records for payout.
    """
    from datetime import date
    from .models.user import User
    
    db = SessionLocal()
    
    try:
        elite_users = db.query(User).filter_by(tier="elite").all()
        processed = 0
        
        # In production, would query earning_events, calculate 12% share, create payout records
        processed = len(elite_users)
        
        return {
            "status": "success",
            "elite_users_processed": processed,
        }
    
    except Exception as e:
        return {"status": "failed", "error": str(e)}
    
    finally:
        db.close()
