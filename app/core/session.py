import logging
from collections.abc import AsyncGenerator, Awaitable
from typing import cast

from fastapi import Depends, FastAPI, Request
from redis.asyncio import Redis
from sqlalchemy import MetaData, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.services.cache import CacheService


engine = create_async_engine(settings.DATABASE_URL, future=True, echo=False)
AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
logger = logging.getLogger(__name__)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Error occurred while fetching database session: {e}")
            raise


async def init_db(base_metadata: MetaData) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(base_metadata.create_all)


async def init_redis(url: str) -> Redis:
    client = Redis.from_url(
        url,
        encoding="utf-8",
        decode_responses=True,
        max_connections=10,
        socket_connect_timeout=2,
        socket_timeout=1,
    )
    try:
        await cast(Awaitable[bool], client.ping())
        logger.info("Successfully connected to Redis")
        return client
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        raise RuntimeError("Could not connect to Redis") from e


def get_redis(request: Request) -> Redis:
    return cast(Redis, request.app.state.redis)


async def get_cache(redis: Redis = Depends(get_redis)) -> CacheService:
    return CacheService(redis)


async def check_db_connection() -> bool:
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return False


async def check_redis_connection(app: FastAPI) -> bool:
    try:
        await app.state.redis.ping()
        return True
    except Exception as e:
        logger.error(f"Redis connection check failed: {e}")
        return False
