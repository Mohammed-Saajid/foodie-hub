from unittest.mock import AsyncMock

import pytest
from pydantic import BaseModel

from app.services.cache import CacheService


class CachePayload(BaseModel):
    id: int
    name: str


class TestCacheService:
    @pytest.mark.asyncio
    async def test_get_model_cache_miss(self):
        redis = AsyncMock()
        redis.get = AsyncMock(return_value=None)
        service = CacheService(redis=redis)

        result = await service.get_model("auth:user:1", CachePayload)

        assert result is None
        redis.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_model_success(self):
        payload = CachePayload(id=1, name="Alice")
        redis = AsyncMock()
        redis.get = AsyncMock(return_value=payload.model_dump_json())
        service = CacheService(redis=redis)

        result = await service.get_model("auth:user:1", CachePayload)

        assert result == payload
        redis.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_model_corrupted_cache_deletes_key(self):
        redis = AsyncMock()
        redis.get = AsyncMock(return_value="{this-is-not-json")
        redis.delete = AsyncMock(return_value=1)
        service = CacheService(redis=redis)

        result = await service.get_model("auth:user:1", CachePayload)

        assert result is None
        redis.delete.assert_awaited_once_with("auth:user:1")

    @pytest.mark.asyncio
    async def test_set_model(self):
        redis = AsyncMock()
        redis.set = AsyncMock(return_value=True)
        service = CacheService(redis=redis)
        payload = CachePayload(id=2, name="Bob")

        await service.set_model("auth:user:2", payload, ttl=120)

        redis.set.assert_awaited_once_with("auth:user:2", payload.model_dump_json(), ex=120)

    @pytest.mark.asyncio
    async def test_delete(self):
        redis = AsyncMock()
        redis.delete = AsyncMock(return_value=1)
        service = CacheService(redis=redis)

        await service.delete("auth:user:2")

        redis.delete.assert_awaited_once_with("auth:user:2")
