from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.core.utils import build_current_user, fetch_user_from_db
from app.models.enums import UserRole


def test_build_current_user_maps_fields():
    user = SimpleNamespace(
        id=1,
        full_name="Test User",
        role=UserRole.CONSUMER,
        is_active=True,
        is_banned=False,
        terms_accepted=True,
    )

    current = build_current_user(user)

    assert current.id == 1
    assert current.full_name == "Test User"
    assert current.role == UserRole.CONSUMER
    assert current.is_active is True
    assert current.is_banned is False
    assert current.terms_accepted is True


@pytest.mark.asyncio
async def test_fetch_user_from_db_found_and_missing():
    db = AsyncMock()
    scalar_result = SimpleNamespace()
    found_user = SimpleNamespace(id=10)

    scalar_result.first = lambda: found_user
    db.scalars = AsyncMock(return_value=scalar_result)

    result = await fetch_user_from_db(db, 10)
    assert result == found_user

    scalar_result.first = lambda: None
    missing = await fetch_user_from_db(db, 999)
    assert missing is None
