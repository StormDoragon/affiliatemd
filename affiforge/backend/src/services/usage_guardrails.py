import logging
import threading
import time

from fastapi import HTTPException
from redis import Redis, RedisError

from ..config import settings

logger = logging.getLogger(__name__)
_INCREMENT = """
local count = redis.call('INCR', KEYS[1])
if count == 1 then redis.call('EXPIRE', KEYS[1], ARGV[1]) end
return count
"""
redis = Redis.from_url(settings.redis_url, socket_timeout=2, socket_connect_timeout=2)
_lock = threading.Lock()
_local_counts: dict[str, tuple[int, int]] = {}


def limit_requests(key: str, limit: int, seconds: int = 60) -> None:
    if not settings.enable_api_guardrails:
        return
    if settings.production:
        try:
            count = redis.eval(_INCREMENT, 1, f"affiforge:{key}", seconds)
        except RedisError as exc:
            raise HTTPException(503, "Request limits are temporarily unavailable") from exc
    else:
        now = int(time.monotonic())
        with _lock:
            for name, (_, expiry) in list(_local_counts.items()):
                if expiry <= now:
                    del _local_counts[name]
            previous, expiry = _local_counts.get(key, (0, now + seconds))
            count = previous + 1
            _local_counts[key] = (count, expiry)
    if count > limit:
        raise HTTPException(
            429, "Too many requests. Try again later.", headers={"Retry-After": str(seconds)}
        )


def check_generation(owner_id: int, endpoint: str, estimated_cost: float) -> None:
    if estimated_cost > settings.max_cost_per_task:
        raise HTTPException(400, "This request exceeds the configured per-task cost limit")
    limit_requests(f"generation:{owner_id}", settings.api_rate_limit_per_minute)
    limit_requests("generation:all", 100)
    if estimated_cost:
        limit_requests(f"ai-day:{owner_id}", 60, 86400)
        limit_requests("ai-day:all", 600, 86400)
    logger.info(
        "Generation requested owner=%s operation=%s estimated_cost=%.4f",
        owner_id,
        endpoint,
        estimated_cost,
    )
