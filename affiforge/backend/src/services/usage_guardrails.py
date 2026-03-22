"""API usage guardrails: per-minute rate limit, cost cap, and usage alert logging."""

from __future__ import annotations

import logging
import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException, status

from ..config import settings

logger = logging.getLogger("affiforge.guardrails")


class UsageGuardrails:
    """In-memory usage tracker for API guardrails.

    This is intentionally simple for MVP use. In multi-worker production,
    replace this with Redis-backed counters for cross-process consistency.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._events: dict[str, deque[tuple[float, float, str]]] = defaultdict(deque)

    def enforce(
        self,
        *,
        subject: str,
        endpoint: str,
        estimated_cost: float,
        client_ip: str,
    ) -> dict[str, float | int]:
        if not settings.enable_api_guardrails:
            return {
                "requests_in_window": 0,
                "rate_limit": 0,
                "remaining": 0,
                "window_cost": 0.0,
            }

        max_cost = float(settings.max_cost_per_task)
        if estimated_cost > max_cost:
            logger.warning(
                "guardrail.block.cost subject=%s ip=%s endpoint=%s estimated_cost=%.6f max_cost=%.6f",
                subject,
                client_ip,
                endpoint,
                estimated_cost,
                max_cost,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Estimated cost ${estimated_cost:.4f} exceeds max ${max_cost:.4f}",
            )

        now = time.time()
        threshold = float(settings.api_usage_alert_ratio)
        rate_limit = int(settings.api_rate_limit_per_minute)

        with self._lock:
            window = self._events[subject]
            while window and (now - window[0][0]) > 60:
                window.popleft()

            if len(window) >= rate_limit:
                logger.warning(
                    "guardrail.block.rate_limit subject=%s ip=%s endpoint=%s limit=%d window_size=%d",
                    subject,
                    client_ip,
                    endpoint,
                    rate_limit,
                    len(window),
                )
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded. Please retry in a minute.",
                )

            window.append((now, estimated_cost, endpoint))
            requests_in_window = len(window)
            window_cost = round(sum(item[1] for item in window), 6)
            remaining = max(rate_limit - requests_in_window, 0)

        logger.info(
            "guardrail.allow subject=%s ip=%s endpoint=%s estimated_cost=%.6f requests=%d/%d window_cost=%.6f",
            subject,
            client_ip,
            endpoint,
            estimated_cost,
            requests_in_window,
            rate_limit,
            window_cost,
        )

        if requests_in_window >= max(1, int(rate_limit * threshold)):
            logger.warning(
                "guardrail.alert.near_rate_limit subject=%s ip=%s endpoint=%s requests=%d/%d",
                subject,
                client_ip,
                endpoint,
                requests_in_window,
                rate_limit,
            )

        if estimated_cost >= (max_cost * threshold):
            logger.warning(
                "guardrail.alert.near_cost_cap subject=%s ip=%s endpoint=%s estimated_cost=%.6f max_cost=%.6f",
                subject,
                client_ip,
                endpoint,
                estimated_cost,
                max_cost,
            )

        return {
            "requests_in_window": requests_in_window,
            "rate_limit": rate_limit,
            "remaining": remaining,
            "window_cost": window_cost,
        }


usage_guardrails = UsageGuardrails()
