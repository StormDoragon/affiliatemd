"""Celery tasks for cluster generation, publishing, and periodic jobs."""

from __future__ import annotations

import re
import time
from datetime import datetime

from celery import Celery
from celery.schedules import crontab

from ..config import settings
from ..db import SessionLocal
from ..models.content_item import ContentItem
from ..models.site import Site
from ..models.user import User
from ..services.ai_service import AIService
from ..services.wordpress_service import WordpressService


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
    task_time_limit=30 * 60,
)

celery_app.conf.beat_schedule = {
    "sync-earnings-nightly": {
        "task": "sync_earnings_from_amazon",
        "schedule": crontab(hour=2, minute=0),
    },
    "calculate-revenue-share-monthly": {
        "task": "calculate_revenue_share",
        "schedule": crontab(hour=3, minute=0, day_of_month=1),
    },
}


def _slugify(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return slug[:64] or "post"


def _unique_slug(db, base_slug: str) -> str:
    candidate = base_slug
    index = 1
    while db.query(ContentItem).filter(ContentItem.slug == candidate).first() is not None:
        suffix = f"-{index}"
        candidate = f"{base_slug[: max(1, 64 - len(suffix))]}{suffix}"
        index += 1
    return candidate


@celery_app.task(name="generate_cluster_task", bind=True, max_retries=3, default_retry_delay=60)
def generate_cluster_task(self, user_id: str, site_id: str, reddit_data: dict, niche: str, audience: str):
    """Generate a content cluster and persist draft posts."""
    db = SessionLocal()

    try:
        user_id_int = int(user_id)
        site_id_int = int(site_id)
    except ValueError:
        db.close()
        return {"status": "failed", "error": "Invalid user_id or site_id"}

    try:
        site = db.query(Site).filter(Site.id == site_id_int, Site.user_id == user_id_int).first()
        if site is None:
            return {"status": "failed", "error": "Site not found or unauthorized"}

        ai_service = AIService(model="gpt-4o")
        result = ai_service.generate_cluster(
            reddit_data=reddit_data,
            niche=niche,
            audience=audience,
        )

        if result.get("status") != "success":
            return {"status": "failed", "error": result.get("error", "Cluster generation failed")}

        cluster_id = str(result.get("cluster_id") or f"cluster-{int(time.time())}")
        posts_to_create: list[tuple[str, str, str | None]] = []

        pillar_post = result.get("pillar_post", {})
        if isinstance(pillar_post, dict):
            pillar_title = str(pillar_post.get("title") or f"{niche} Guide").strip()
            sections = pillar_post.get("sections", [])
            section_lines = ""
            if isinstance(sections, list):
                section_lines = "\n".join(f"- {str(section)}" for section in sections)
            pillar_body = f"Generated pillar post for {audience}.\n\n{section_lines}".strip()
            posts_to_create.append((pillar_title, pillar_body, niche))

        supporting_posts = result.get("supporting_posts", [])
        if isinstance(supporting_posts, list):
            for post in supporting_posts:
                if not isinstance(post, dict):
                    continue
                title = str(post.get("title") or "").strip()
                if not title:
                    continue
                keyword_value = post.get("keyword")
                keyword = str(keyword_value).strip() if keyword_value else None
                body = f"Generated supporting post draft for {keyword or title}."
                posts_to_create.append((title, body, keyword))

        for index, (title, body, keyword) in enumerate(posts_to_create, start=1):
            slug_base = _slugify(f"{cluster_id}-{index}-{title}")
            content_item = ContentItem(
                title=title,
                slug=_unique_slug(db, slug_base),
                body=body,
                keyword=keyword,
                reddit_thread_id=cluster_id,
                status="draft",
                site_id=site_id_int,
                owner_id=user_id_int,
            )
            db.add(content_item)

        db.commit()
        return {
            "status": "success",
            "cluster_id": cluster_id,
            "posts_created": len(posts_to_create),
            "cost": float(result.get("cost", 0.0)),
            "task_id": self.request.id,
        }

    except Exception as exc:
        db.rollback()
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=60)
        return {"status": "failed", "error": str(exc)}

    finally:
        db.close()


@celery_app.task(name="publish_to_wordpress_task", bind=True, max_retries=2, default_retry_delay=120)
def publish_to_wordpress_task(self, site_id: str, cluster_id: str):
    """Publish all posts in a generated cluster to WordPress."""
    db = SessionLocal()

    try:
        site_id_int = int(site_id)
    except ValueError:
        db.close()
        return {"status": "failed", "error": "Invalid site_id"}

    try:
        site = db.query(Site).filter(Site.id == site_id_int).first()
        if site is None:
            return {"status": "failed", "error": "Site not found"}

        posts = (
            db.query(ContentItem)
            .filter(ContentItem.site_id == site_id_int, ContentItem.reddit_thread_id == cluster_id)
            .all()
        )
        if not posts:
            return {"status": "failed", "error": "No posts found for cluster"}

        publisher = WordpressService()
        published_count = 0

        for post in posts:
            result = publisher.publish_post(
                wp_url=site.wp_url,
                wp_username=site.wp_username,
                wp_app_password=site.wp_app_password,
                title=post.title,
                content=post.body,
            )
            if result.get("status") == "published":
                post.status = "published"
                published_count += 1

        db.commit()
        return {
            "status": "success",
            "cluster_id": cluster_id,
            "posts_published": published_count,
            "task_id": self.request.id,
        }

    except Exception as exc:
        db.rollback()
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=120)
        return {"status": "failed", "error": str(exc)}

    finally:
        db.close()


@celery_app.task(name="sync_earnings_from_amazon")
def sync_earnings_from_amazon():
    """Placeholder nightly earnings sync job for all users."""
    db = SessionLocal()
    try:
        users_synced = db.query(User).count()
        return {
            "status": "success",
            "users_synced": int(users_synced),
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as exc:
        return {"status": "failed", "error": str(exc)}
    finally:
        db.close()


@celery_app.task(name="calculate_revenue_share")
def calculate_revenue_share():
    """Placeholder monthly revenue-share aggregation for opted-in users."""
    db = SessionLocal()
    try:
        eligible_users = db.query(User).filter(User.profitshare_enabled.is_(True)).count()
        return {
            "status": "success",
            "eligible_users_processed": int(eligible_users),
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as exc:
        return {"status": "failed", "error": str(exc)}
    finally:
        db.close()
