import time
from collections import defaultdict
from threading import Lock

from fastapi import HTTPException, Request


class RateLimiter:
    """In-memory sliding window rate limiter."""

    def __init__(self, max_requests: int = 5, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)
        self._lock = Lock()

    def _get_client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _cleanup(self, key: str, now: float) -> None:
        cutoff = now - self.window_seconds
        self._requests[key] = [
            t for t in self._requests[key] if t > cutoff
        ]

    async def __call__(self, request: Request) -> None:
        client_ip = self._get_client_ip(request)
        now = time.time()

        with self._lock:
            self._cleanup(client_ip, now)

            if len(self._requests[client_ip]) >= self.max_requests:
                raise HTTPException(
                    status_code=429,
                    detail={
                        "error": "rate_limit_exceeded",
                        "message": f"Too many uploads. Limit: {self.max_requests} per {self.window_seconds}s",
                        "details": None,
                    },
                )

            self._requests[client_ip].append(now)


upload_rate_limiter = RateLimiter(max_requests=5, window_seconds=60)
