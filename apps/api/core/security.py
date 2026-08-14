from __future__ import annotations

import hashlib
import hmac
import time
from collections import defaultdict, deque
from threading import Lock

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from apps.api.core.config import Settings, get_settings

bearer = HTTPBearer(auto_error=False)


def require_admin(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    settings: Settings = Depends(get_settings),
) -> None:
    expected = settings.admin_api_key.get_secret_value()
    supplied = credentials.credentials if credentials else ""
    if not expected or not hmac.compare_digest(supplied, expected):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin token")


def anonymize_visitor(request: Request, salt: str) -> str:
    forwarded = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
    ip = forwarded or (request.client.host if request.client else "unknown")
    agent = request.headers.get("user-agent", "")[:200]
    daily = time.strftime("%Y-%m-%d", time.gmtime())
    return hashlib.sha256(f"{salt}|{daily}|{ip}|{agent}".encode()).hexdigest()[:32]


class InMemoryRateLimiter:
    """Small-process limiter; use gateway/Redis enforcement for horizontal scale."""

    def __init__(self, limit: int = 120, window_seconds: int = 60) -> None:
        self.limit = limit
        self.window = window_seconds
        self.entries: dict[str, deque[float]] = defaultdict(deque)
        self.lock = Lock()

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        with self.lock:
            events = self.entries[key]
            while events and events[0] < now - self.window:
                events.popleft()
            if len(events) >= self.limit:
                return False
            events.append(now)
            return True
