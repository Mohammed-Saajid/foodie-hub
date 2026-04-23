from collections.abc import AsyncGenerator
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

# Application imports
from app.api.dependencies import (
    get_current_user,
    get_feedback_service,
    get_hotel_repository,
    get_hotel_service,
    get_menu_item_repository,
    get_menu_service,
    get_order_bid_repository,
    get_order_bid_service,
    get_order_repository,
    get_order_service,
    get_report_service,
    get_terms_service,
    get_user_repository,
    get_user_service,
)
from app.core.config import settings
from app.core.session import get_cache, get_db
from app.main import app
from app.models.base import Base


# Cleanly register fixtures from other modules
pytest_plugins = ["tests.utils"]


@pytest_asyncio.fixture(scope="session")
async def engine():
    """
    Creates a session-scoped async engine connected to an in-memory SQLite database.
    StaticPool ensures connections are maintained across the test suite.
    """
    engine_instance = create_async_engine(
        settings.DATABASE_URL,
        poolclass=StaticPool,
    )

    async with engine_instance.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    try:
        yield engine_instance
    finally:
        await engine_instance.dispose()


@pytest_asyncio.fixture
async def db_session(engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """
    Function-scoped session fixture.
    Implements the "nested transaction" (SAVEPOINT) pattern to allow application
    code to call session.commit() without actually persisting data to the database,
    ensuring strict isolation between tests.
    """
    async with engine.connect() as conn:
        # Start the outer transaction
        transaction = await conn.begin()

        # Start a nested transaction (SAVEPOINT)
        await conn.begin_nested()

        session_factory = async_sessionmaker(
            bind=conn,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        async with session_factory() as session:
            # Ensure the nested transaction is restarted if the application calls commit()
            @event.listens_for(session.sync_session, "after_transaction_end")
            def restart_savepoint(session, transaction):
                if conn.closed:
                    return
                if not conn.in_nested_transaction():
                    conn.sync_connection.begin_nested()

            yield session

        # Rollback the outer transaction, wiping all changes made during the test
        await transaction.rollback()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Test client fixture that automatically injects the isolated db_session
    into FastAPI's dependency overrides.
    """
    app.dependency_overrides[get_db] = lambda: db_session
    transport = ASGITransport(app=app)

    try:
        async with AsyncClient(transport=transport, base_url="http://test/api/v1/") as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def passwd_context():
    """
    Fixture for password hashing context.
    Imported locally to avoid loading security modules before necessary.
    """
    from app.core.security import pwd_context

    return pwd_context


@pytest.fixture
def service_factory():
    def _create(**methods):
        cache = AsyncMock()

        for name, value in methods.items():
            setattr(cache, name, value)

        return cache

    return _create


@pytest.fixture
def repository_factory():
    def _create(**methods):
        repo = AsyncMock()

        for name, value in methods.items():
            setattr(repo, name, value)

        return repo

    return _create


@pytest.fixture
def user_factory():
    def _create(**kwargs):
        return SimpleNamespace(
            id=kwargs.get("id", 1),
            username=kwargs.get("username", "testuser"),
            full_name=kwargs.get("full_name", "Test User"),
            role=kwargs.get("role", "consumer"),
            terms_accepted=kwargs.get("terms_accepted", True),
            mobile_number=kwargs.get("mobile_number", "1234567890"),
            department=kwargs.get("department", "AIML"),
            register_number=kwargs.get("register_number", "212223240096"),
            email=kwargs.get("email", "example@example.com"),
            terms_accepted_at=kwargs.get("terms_accepted_at"),
            is_banned=kwargs.get("is_banned", False),
            is_active=kwargs.get("is_active", True),
            active_orders_count=kwargs.get("active_orders_count", 0),
            active_orders_for_delivery_count=kwargs.get("active_orders_for_delivery_count", 0),
            about_me=kwargs.get("about_me", ""),
            profile_picture_url=kwargs.get("profile_picture_url"),
            upi_screenshot_url=kwargs.get("upi_screenshot_url"),
        )

    return _create


@pytest.fixture
def override_dependencies():
    registered = {}

    def _apply(**deps):
        mapping = {
            "user": get_current_user,
            "user_service": get_user_service,
            "cache": get_cache,
            "terms_service": get_terms_service,
            "feedback_service": get_feedback_service,
            "order_service": get_order_service,
            "report_service": get_report_service,
            "hotel_service": get_hotel_service,
            "order_bid_service": get_order_bid_service,
            "menu_service": get_menu_service,
            "user_repository": get_user_repository,
            "hotel_repository": get_hotel_repository,
            "menu_item_repository": get_menu_item_repository,
            "order_repository": get_order_repository,
            "order_bid_repository": get_order_bid_repository,
        }

        for key, value in deps.items():
            if key not in mapping:
                raise ValueError(f"Unsupported dependency override: {key}")

            async def _override(v=value):
                return v

            registered[mapping[key]] = _override

        app.dependency_overrides.update(registered)

    yield _apply

    app.dependency_overrides.clear()
