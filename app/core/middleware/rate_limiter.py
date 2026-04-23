import logging
import time
import uuid

from fastapi import Request
from redis.asyncio import Redis
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse, Response
from starlette.status import HTTP_429_TOO_MANY_REQUESTS
from starlette.types import ASGIApp

from app.core.config import settings


logger = logging.getLogger(__name__)

# Atomic Lua script — executed as a single Redis transaction.
# Eliminates the race condition
SLIDING_WINDOW_SCRIPT = """
local key    = KEYS[1]
local now    = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local limit  = tonumber(ARGV[3])
local member = ARGV[4]

redis.call('ZADD', key, now, member)
redis.call('ZREMRANGEBYSCORE', key, 0, now - window)
local count = redis.call('ZCARD', key)
redis.call('EXPIRE', key, window)
return count
"""

# Routes that bypass rate limiting entirely
EXCLUDED_PATHS = frozenset({"/health"})


class RedisRateLimiterMiddleware(BaseHTTPMiddleware):
    """
    Production-grade sliding-window rate limiter backed by Redis.

    """

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)
        self._script_sha: str | None = None

    def _get_client_key(self, request: Request) -> str:
        """
        Derive a rate-limit key from the request.
        """
        # Prefer authenticated user id — immune to IP sharing / spoofing
        user_id = getattr(getattr(request, "state", None), "user_id", None)
        if user_id:
            return f"rate:user:{user_id}"

        # Proxy-injected real IP
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return f"rate:ip:{real_ip.strip()}"

        # First entry in X-Forwarded-For (added by load balancer)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return f"rate:ip:{forwarded_for.split(',')[0].strip()}"

        # Direct peer — fallback for local / non-proxied deployments
        client_host = request.client.host if request.client else "unknown"
        return f"rate:ip:{client_host}"

    async def _load_script(self, redis: Redis) -> str:
        """
        SCRIPT LOAD the Lua script once and cache the SHA.
        Subsequent calls use EVALSHA — cheaper and faster than EVAL.
        """
        if self._script_sha is None:
            self._script_sha = await redis.script_load(SLIDING_WINDOW_SCRIPT)
        return self._script_sha

    # Core dispatch

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Skip rate limiting for excluded paths
        if request.url.path in EXCLUDED_PATHS:
            return await call_next(request)

        # Retrieve the shared Redis connection pool created during app lifespan.
        # See app/main.py for the recommended lifespan setup.
        redis = getattr(getattr(request, "app", None), "state", None)
        redis = getattr(redis, "redis", None) if redis else None

        if redis is None:
            # Redis not wired up — log loudly and fail open
            logger.error(
                "RedisRateLimiterMiddleware: app.state.redis is not set. "
                "Initialise the connection pool in your app lifespan and assign "
                "it to app.state.redis. Rate limiting is DISABLED for this request."
            )
            return await call_next(request)

        key = self._get_client_key(request)
        now_ms = int(time.time() * 1000)  # millisecond precision
        member = f"{now_ms}-{request.headers.get('X-Correlation-ID', uuid.uuid4().hex)}"

        try:
            sha = await self._load_script(redis)
            count = await redis.evalsha(
                sha,
                1,  # number of KEYS
                key,  # KEYS[1]
                now_ms,  # ARGV[1]  — current timestamp (ms)
                settings.RATE_WINDOW * 1000,  # ARGV[2]  — window size (ms)
                settings.RATE_LIMIT,  # ARGV[3]  — request limit
                member,  # ARGV[4]  — unique member
            )
        except Exception as exc:
            # Redis unavailable or script error — fail open to avoid a full outage.
            # Swap for `return JSONResponse(status_code=503, ...)` if you prefer
            # fail-closed behaviour (safer for sensitive APIs).
            logger.error("Rate limiter Redis error (failing open): %s", exc)
            return await call_next(request)

        if count > settings.RATE_LIMIT:
            return JSONResponse(
                status_code=HTTP_429_TOO_MANY_REQUESTS,
                headers={
                    "Retry-After": str(settings.RATE_WINDOW),
                    "X-RateLimit-Limit": str(settings.RATE_LIMIT),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time()) + settings.RATE_WINDOW),
                },
                content={
                    "error": "Too many requests",
                    "retry_after": settings.RATE_WINDOW,
                },
            )

        return await call_next(request)
