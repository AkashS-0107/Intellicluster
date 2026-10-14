"""
Dependency injection utilities for the API layer.
Re-exports the database session dependency and provides rate limiting.
"""

import time
from collections import defaultdict

from fastapi import Request
from fastapi.exceptions import HTTPException

from intellicluster.db.session import get_db  # noqa: F401 — re-exported for API routes


class RateLimiter:
    """
    In-memory sliding-window rate limiter implemented as a FastAPI callable dependency.
    Tracks request timestamps per client IP and enforces a configurable per-minute limit.
    No external dependencies required.
    """

    def __init__(self, requests_per_minute: int = 100, window_seconds: int = 60) -> None:
        self.requests_per_minute = requests_per_minute
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)

    async def __call__(self, request: Request) -> None:
        """Check rate limit for the requesting client IP."""
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        window_start = now - self.window_seconds

        # Prune expired entries for this client
        self._requests[client_ip] = [
            t for t in self._requests[client_ip] if t > window_start
        ]

        if len(self._requests[client_ip]) >= self.requests_per_minute:
            raise HTTPException(
                status_code=429,
                detail={
                    "error_code": "RATE_LIMIT_EXCEEDED",
                    "message": "Too many requests. Please try again later.",
                    "details": {"retry_after_seconds": self.window_seconds},
                },
            )

        self._requests[client_ip].append(now)


# Module-level rate limiter instance applied to API v1 routes.
# Overridden in tests via dependency_overrides to avoid interference.
rate_limiter = RateLimiter(requests_per_minute=100)
