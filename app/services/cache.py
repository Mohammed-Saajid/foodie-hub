from typing import TypeVar

from pydantic import BaseModel
from redis.asyncio import Redis


T = TypeVar("T", bound=BaseModel)


class CacheService:
    def __init__(self, redis: Redis):
        self.redis: Redis = redis

    async def get_model(self, key: str, model: type[T]) -> T | None:
        raw = await self.redis.get(key)
        if not raw:
            return None

        try:
            return model.model_validate_json(raw)
        except Exception:
            # corrupted cache delete
            await self.redis.delete(key)
            return None

    async def set_model(self, key: str, value: BaseModel, ttl: int) -> None:
        await self.redis.set(key, value.model_dump_json(), ex=ttl)

    async def delete(self, key: str) -> None:
        await self.redis.delete(key)
