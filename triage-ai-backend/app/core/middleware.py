import hashlib
import time
import re
import logging
from collections import defaultdict, deque
from typing import Callable

from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings

logger = logging.getLogger(__name__)

# ── Secure response headers ───────────────────────────────────────────────────
SECURE_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(self), camera=(self), microphone=()",
    "Cache-Control": "no-store",
    "Strict-Transport-Security": "max-age=63072000; includeSubDomains",
}

# ── Abuse detection — in-memory sliding window per IP ─────────────────────────
_abuse_windows: dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
_blocked_ips: dict[str, float] = {}
ABUSE_THRESHOLD = 80       # requests in window
ABUSE_WINDOW_S  = 60       # seconds
BLOCK_DURATION_S = 300     # 5-minute block


def _is_blocked(ip: str) -> bool:
    if ip in _blocked_ips:
        if time.time() < _blocked_ips[ip]:
            return True
        del _blocked_ips[ip]
    return False


def _record_request(ip: str) -> bool:
    now = time.time()
    window = _abuse_windows[ip]
    window.append(now)
    cutoff = now - ABUSE_WINDOW_S
    recent = sum(1 for t in window if t >= cutoff)
    if recent >= ABUSE_THRESHOLD:
        _blocked_ips[ip] = now + BLOCK_DURATION_S
        logger.warning("Abuse detected — blocking IP %s for %ds", ip, BLOCK_DURATION_S)
        return False
    return True


# ── Input sanitisation ────────────────────────────────────────────────────────
_STRIP_TAGS   = re.compile(r"<[^>]+>")
_SCRIPT_BLOCK = re.compile(r"<script[\s\S]*?</script>", re.IGNORECASE)
_MAX_BODY     = 10 * 1024 * 1024     # 256 KB


def sanitise_string(value: str, max_len: int = 2000) -> str:
    v = _SCRIPT_BLOCK.sub("", value)
    v = _STRIP_TAGS.sub("", v)
    v = v.replace("\x00", "")
    return v[:max_len].strip()


# ── API key guard ─────────────────────────────────────────────────────────────
_ADMIN_PREFIX = "/admin"
_OPEN_PATHS   = {"/health", "/docs", "/redoc", "/openapi.json"}


def _check_api_key(request: Request) -> None:
    if not settings.API_KEY:
        return
    path = request.url.path
    if path in _OPEN_PATHS or not path.startswith(_ADMIN_PREFIX):
        return
    key = request.headers.get("X-API-Key", "")
    if not key or key != settings.API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key.")


# ── Middleware ────────────────────────────────────────────────────────────────
class SecurityMiddleware(BaseHTTPMiddleware):
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.method == "OPTIONS":
            return await call_next(request)
        
        ip = request.client.host if request.client else "unknown"

        # Blocked-IP gate
        if _is_blocked(ip):
            return Response(
                content='{"detail":"Too many requests. Try again later."}',
                status_code=429,
                media_type="application/json",
            )

        # Sliding-window abuse check
        if not _record_request(ip):
            return Response(
                content='{"detail":"Rate limit exceeded."}',
                status_code=429,
                media_type="application/json",
            )

        # Oversized body guard
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > _MAX_BODY:
            return Response(
                content='{"detail":"Request body too large."}',
                status_code=413,
                media_type="application/json",
            )

        # API key check for admin routes
        try:
            _check_api_key(request)
        except HTTPException as exc:
            return Response(
                content=f'{{"detail":"{exc.detail}"}}',
                status_code=exc.status_code,
                media_type="application/json",
            )

        response: Response = await call_next(request)

        # Attach secure headers
        for k, v in SECURE_HEADERS.items():
            response.headers[k] = v

        return response
