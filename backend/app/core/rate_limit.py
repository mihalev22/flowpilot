import time
from collections import defaultdict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

RATE_LIMITED_PATHS = {"/api/auth/login", "/api/auth/register", "/api/webhooks/telegram"}
RATE_LIMIT = 20
WINDOW_SECONDS = 60

_hits: dict[tuple[str, str], list[float]] = defaultdict(list)


def reset_rate_limits() -> None:
    _hits.clear()


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method == "POST" and request.url.path in RATE_LIMITED_PATHS:
            key = (_client_ip(request), request.url.path)
            now = time.monotonic()
            window = [ts for ts in _hits[key] if now - ts < WINDOW_SECONDS]
            if len(window) >= RATE_LIMIT:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Слишком много запросов. Попробуйте позже."},
                    headers={"Retry-After": str(WINDOW_SECONDS)},
                )
            window.append(now)
            _hits[key] = window
            if len(_hits) > 10_000:
                _prune(now)
        return await call_next(request)


def _prune(now: float) -> None:
    for key in list(_hits):
        _hits[key] = [ts for ts in _hits[key] if now - ts < WINDOW_SECONDS]
        if not _hits[key]:
            del _hits[key]
