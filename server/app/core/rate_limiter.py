"""
Demonstration-Level In-Memory Rate Limiter
Note: This is a lightweight proof-of-concept guard designed for hackathon demonstration.
It is not intended as production-grade distributed DDoS mitigation.
"""

import time
from collections import defaultdict
from typing import Dict, List
from fastapi import HTTPException, Request, status

from app.config import settings


class InMemoryRateLimiter:
    """
    Sliding window in-memory rate limiter per client IP.
    """
    def __init__(self, requests_per_minute: int = 10):
        self.limit = requests_per_minute
        self.window_seconds = 60
        self.client_records: Dict[str, List[float]] = defaultdict(list)

    def is_rate_limited(self, client_ip: str) -> bool:
        now = time.time()
        window_start = now - self.window_seconds

        # Prune expired timestamps
        self.client_records[client_ip] = [
            t for t in self.client_records[client_ip] if t > window_start
        ]

        # Check limit
        if len(self.client_records[client_ip]) >= self.limit:
            return True

        # Append current request
        self.client_records[client_ip].append(now)
        return False


# Global instance configured from settings
sos_rate_limiter = InMemoryRateLimiter(
    requests_per_minute=settings.RATE_LIMIT_SOS_PER_MINUTE
)


def check_sos_rate_limit(request: Request):
    """
    FastAPI dependency to guard public SOS broadcast endpoints.
    """
    # Extract client IP (checking X-Forwarded-For if behind proxy)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        client_ip = forwarded.split(",")[0].strip()
    else:
        client_ip = request.client.host if request.client else "127.0.0.1"

    if sos_rate_limiter.is_rate_limited(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                "[RATE LIMIT DEMO GUARD] Too many SOS broadcasts received from this client. "
                f"Rate limited to {settings.RATE_LIMIT_SOS_PER_MINUTE} requests per minute to prevent flood abuse."
            ),
        )
