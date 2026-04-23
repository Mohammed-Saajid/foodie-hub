import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

# Middleware and dependencies
from fastapi.middleware.cors import CORSMiddleware

from app import models  # noqa: F401
from app.api.router import api_router
from app.core.config import settings

# Exception handlers
from app.core.exception_handlers import setup_exception_handlers
from app.core.logger import setup_logging
from app.core.middleware.logging_middleware import CorrelationIDMiddleware
from app.core.middleware.rate_limiter import RedisRateLimiterMiddleware
from app.core.session import check_db_connection, check_redis_connection, init_db, init_redis
from app.models.base import Base


# Setup Logging
setup_logging()

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info(f"Starting up {settings.PROJECT_NAME}..")
    if settings.AUTO_CREATE_TABLES:
        logger.warning("AUTO_CREATE_TABLES is enabled; creating tables from SQLAlchemy metadata")
        await init_db(Base.metadata)
    app.state.redis = await init_redis(settings.REDIS_URL)
    yield
    logger.info(f"Shutting down {settings.PROJECT_NAME}..")
    await app.state.redis.aclose()


app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)

app.add_middleware(CorrelationIDMiddleware)
app.add_middleware(RedisRateLimiterMiddleware)

setup_exception_handlers(app)

# Include API and WebSocket routes
app.include_router(api_router, prefix="/api/v1")


@app.get("/health", tags=["System"])
async def health_check() -> dict[str, str]:
    return {
        "status": "online",
        "project": settings.PROJECT_NAME,
        "version": settings.PROJECT_VERSION,
        "environment": settings.ENVIRONMENT,
        "db": "connected" if await check_db_connection() else "disconnected",
        "redis": "connected" if await check_redis_connection(app=app) else "disconnected",
    }
