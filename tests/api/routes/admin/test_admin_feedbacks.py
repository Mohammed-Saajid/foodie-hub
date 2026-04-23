from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest


class TestAdminFeedbacks:
    @pytest.mark.asyncio
    async def test_get_feedbacks(
        self,
        client: AsyncMock,
        user_factory: callable,
        service_factory,
        override_dependencies,
    ):
        user = user_factory(id=1, role="admin")
        feedbacks = (
            [SimpleNamespace(id=1, feedback="Great app!", user_id=1, created_at=date(2023, 1, 1))],
            1,
        )

        feedback_service = service_factory(list_feedbacks=AsyncMock(return_value=feedbacks))

        override_dependencies(
            user=user,
            feedback_service=feedback_service,
        )

        response = await client.get(
            "/admin/feedbacks", params={"limit": 10, "offset": 0, "asc": True}
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_feedbacks_unauthorized(
        self,
        client: AsyncMock,
        user_factory: callable,
        override_dependencies,
    ):
        user = user_factory(id=2, role="consumer")

        override_dependencies(user=user)

        response = await client.get("/admin/feedbacks")

        assert response.status_code == 403
