from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import Response

from app.core.middleware.rate_limiter import RedisRateLimiterMiddleware


def _build_request(
    path: str = "/items", headers: list[tuple[bytes, bytes]] | None = None
) -> Request:
    app = FastAPI()
    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.3"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "headers": headers or [],
        "client": ("127.0.0.1", 50000),
        "server": ("testserver", 80),
        "app": app,
    }
    return Request(scope)


@pytest.mark.asyncio
async def test_get_client_key_user_id():
    middleware = RedisRateLimiterMiddleware(FastAPI())
    request = _build_request()
    request.state.user_id = 99

    assert middleware._get_client_key(request) == "rate:user:99"


@pytest.mark.asyncio
async def test_get_client_key_real_ip():
    middleware = RedisRateLimiterMiddleware(FastAPI())
    request = _build_request(headers=[(b"x-real-ip", b"10.0.0.5")])

    assert middleware._get_client_key(request) == "rate:ip:10.0.0.5"


@pytest.mark.asyncio
async def test_get_client_key_forwarded_for_and_fallback():
    middleware = RedisRateLimiterMiddleware(FastAPI())
    forwarded_request = _build_request(headers=[(b"x-forwarded-for", b"1.2.3.4, 5.6.7.8")])
    fallback_request = _build_request()

    assert middleware._get_client_key(forwarded_request) == "rate:ip:1.2.3.4"
    assert middleware._get_client_key(fallback_request) == "rate:ip:127.0.0.1"


@pytest.mark.asyncio
async def test_load_script_cached_once():
    middleware = RedisRateLimiterMiddleware(FastAPI())
    redis = AsyncMock()
    redis.script_load = AsyncMock(return_value="sha-1")

    first = await middleware._load_script(redis)
    second = await middleware._load_script(redis)

    assert first == "sha-1"
    assert second == "sha-1"
    redis.script_load.assert_awaited_once()


@pytest.mark.asyncio
async def test_dispatch_excluded_path_skips_rate_limit():
    middleware = RedisRateLimiterMiddleware(FastAPI())
    request = _build_request(path="/health")

    async def call_next(_: Request) -> Response:
        return Response(status_code=200)

    response = await middleware.dispatch(request, call_next)

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_dispatch_no_redis_fails_open():
    middleware = RedisRateLimiterMiddleware(FastAPI())
    request = _build_request(path="/orders")

    async def call_next(_: Request) -> Response:
        return Response(status_code=200)

    response = await middleware.dispatch(request, call_next)

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_dispatch_evalsha_error_fails_open():
    middleware = RedisRateLimiterMiddleware(FastAPI())
    request = _build_request(path="/orders")

    redis = AsyncMock()
    redis.script_load = AsyncMock(return_value="sha")
    redis.evalsha = AsyncMock(side_effect=RuntimeError("redis down"))
    request.app.state.redis = redis

    async def call_next(_: Request) -> Response:
        return Response(status_code=200)

    response = await middleware.dispatch(request, call_next)

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_dispatch_rate_limited_returns_429():
    middleware = RedisRateLimiterMiddleware(FastAPI())
    request = _build_request(path="/orders")

    redis = AsyncMock()
    redis.script_load = AsyncMock(return_value="sha")
    redis.evalsha = AsyncMock(return_value=10_000)
    request.app.state.redis = redis

    async def call_next(_: Request) -> Response:
        return Response(status_code=200)

    response = await middleware.dispatch(request, call_next)

    assert response.status_code == 429


@pytest.mark.asyncio
async def test_dispatch_under_limit_calls_next():
    middleware = RedisRateLimiterMiddleware(FastAPI())
    request = _build_request(path="/orders")

    redis = AsyncMock()
    redis.script_load = AsyncMock(return_value="sha")
    redis.evalsha = AsyncMock(return_value=1)
    request.app.state.redis = redis

    async def call_next(_: Request) -> Response:
        return Response(status_code=201)

    response = await middleware.dispatch(request, call_next)

    assert response.status_code == 201
