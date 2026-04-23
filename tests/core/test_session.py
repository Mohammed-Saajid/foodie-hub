from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from starlette.requests import Request

from app.core import session
from app.services.cache import CacheService


class _AsyncContextManager:
    def __init__(self, value):
        self._value = value

    async def __aenter__(self):
        return self._value

    async def __aexit__(self, exc_type, exc, tb):
        return False


@pytest.mark.asyncio
async def test_get_db_success_commit():
    db = AsyncMock()

    class SessionFactory:
        def __call__(self):
            return _AsyncContextManager(db)

    with patch.object(session, "AsyncSessionLocal", SessionFactory()):
        gen = session.get_db()
        yielded = await anext(gen)
        assert yielded is db
        with pytest.raises(StopAsyncIteration):
            await anext(gen)

    db.commit.assert_awaited_once()
    db.rollback.assert_not_called()


@pytest.mark.asyncio
async def test_get_db_exception_rolls_back():
    db = AsyncMock()

    class SessionFactory:
        def __call__(self):
            return _AsyncContextManager(db)

    with patch.object(session, "AsyncSessionLocal", SessionFactory()):
        gen = session.get_db()
        await anext(gen)
        with pytest.raises(RuntimeError):
            await gen.athrow(RuntimeError("boom"))

    db.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_init_db_runs_create_all():
    conn = AsyncMock()

    class FakeEngine:
        def begin(self):
            return _AsyncContextManager(conn)

    with patch.object(session, "engine", FakeEngine()):
        metadata = MagicMock()
        await session.init_db(metadata)

    conn.run_sync.assert_awaited_once_with(metadata.create_all)


@pytest.mark.asyncio
async def test_init_redis_success():
    client = AsyncMock()
    client.ping = AsyncMock(return_value=True)

    with patch.object(session.Redis, "from_url", return_value=client):
        result = await session.init_redis("redis://localhost:6379/0")

    assert result is client


@pytest.mark.asyncio
async def test_init_redis_failure_raises_runtime_error():
    client = AsyncMock()
    client.ping = AsyncMock(side_effect=RuntimeError("cannot ping"))

    with (
        patch.object(session.Redis, "from_url", return_value=client),
        pytest.raises(RuntimeError, match="Could not connect to Redis"),
    ):
        await session.init_redis("redis://localhost:6379/0")


@pytest.mark.asyncio
async def test_get_redis_and_get_cache():
    app = FastAPI()
    redis = AsyncMock()
    app.state.redis = redis

    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.3"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": "/",
        "raw_path": b"/",
        "query_string": b"",
        "headers": [],
        "client": ("127.0.0.1", 50000),
        "server": ("testserver", 80),
        "app": app,
    }
    request = Request(scope)

    returned_redis = session.get_redis(request)
    cache = await session.get_cache(redis)

    assert returned_redis is redis
    assert isinstance(cache, CacheService)


@pytest.mark.asyncio
async def test_check_db_connection_success_and_failure():
    conn = AsyncMock()

    class FakeEngineOk:
        def connect(self):
            return _AsyncContextManager(conn)

    with patch.object(session, "engine", FakeEngineOk()):
        ok = await session.check_db_connection()

    assert ok is True

    class FakeEngineFail:
        def connect(self):
            raise RuntimeError("db down")

    with patch.object(session, "engine", FakeEngineFail()):
        failed = await session.check_db_connection()

    assert failed is False


@pytest.mark.asyncio
async def test_check_redis_connection_success_and_failure():
    app = SimpleNamespace(state=SimpleNamespace(redis=AsyncMock()))
    app.state.redis.ping = AsyncMock(return_value=True)

    ok = await session.check_redis_connection(app)
    assert ok is True

    app.state.redis.ping = AsyncMock(side_effect=RuntimeError("redis down"))
    failed = await session.check_redis_connection(app)
    assert failed is False
